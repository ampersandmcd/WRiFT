#################################################
#################################################
#################################################
##### FARSITE BETA (04/04/22)
##### Rothermel Surface Spread
##### Canopy Spread

################################################
############ External Modules
################################################

# weather processing module (thank you nathan)
from app.modeling.weather import CurrentWeather
from app.modeling.rothermel import compute_surface_spread
from app.modeling.data_preparation import prepare_data, build_tanphi_arrays

# Data containers and pre-processing
import pickle
from dataclasses import dataclass
import os

# Computational Tools
import numpy as np
import pandas as pd
import xarray as xr
from numba import jit
from numba.experimental import jitclass
from numba import int32, float32, uint16

# quick check for burnable fuel types
NB = set([91., 92., 93., 98., 99., 0.])
burnable = lambda x : x not in NB

# some helper math functions that can be compiled
# The constants in these are just trial and error stuff I came up with
# feel free to change as necessary if you know what they do
@jit(nopython=True, fastmath=True)
def compute_OR(x):
    return x*(2**.5)/5

@jit(nopython=True, fastmath=True)
def compute_grid_dimension(x, m):
    return min(m, max(2, int(np.ceil(30/x))))

@jit(nopython=True, fastmath=True)
def compute_xinc(s, d):
    return int(np.rint(s * np.cos(d)))

@jit(nopython=True, fastmath=True)
def compute_yinc(s, d):
    return int(np.rint(s * np.sin(d)))

@jitclass([('Wx', int32), ('Wy', int32), ('OPx', int32), ('OPy', int32), ('OMx', int32),
           ('OMy', int32), ('WR', float32), ('OR', float32), ('dim', uint16), ('t', uint16)])
class FireCell:
    """
    This is a container for information we can cache about a cell with fires
    """

    def __init__(self, INPUT, i, j, wind_speed, wind_dir):

        WR = compute_surface_spread(INPUT[i,j,:], wind_speed) * .3048
        OR = compute_OR(WR)
        dim = compute_grid_dimension(OR, 8)
        t = int(np.ceil(compute_grid_dimension(OR, np.inf)/dim))
        WR, OR = WR*(dim/30)*t, OR*(dim/30)*t
        Wx, Wy = compute_xinc(WR, wind_dir), compute_yinc(WR, wind_dir)
        OPx, OPy = compute_xinc(OR, wind_dir + np.pi/2), compute_yinc(OR, wind_dir + np.pi/2)
        OMx, OMy = compute_xinc(OR, wind_dir - np.pi/2), compute_yinc(OR, wind_dir - np.pi/2)

        self.Wx = Wx   # x component of spread in direction of wind (grid units / min*t)
        self.Wy = Wy   # y component of spread in direction of wind (grid units / min*t)
        self.OPx = OPx # x component of spread in (pi/2) direction orthogonal to wind (grid units / min*t)
        self.OPy = OPy # y component of spread in (pi/2) direction orthogonal to wind (grid units / min*t)
        self.OMx = OMx # x component of spread in (-pi/2) direction orthogonal to wind (grid units / min*t)
        self.OMy = OMy # y component of spread in (-pi/2) direction orthogonal to wind (grid units / min*t)
        self.WR = WR   # spread rate in direction of wind (grid units / min*t)
        self.OR = OR   # spread rate in direction orthogonal to wind (grid units / min*t)
        self.dim = dim # grid resolution
        self.t = t     # number of time steps to skip between updates (min)

def pre_burn(lat, lon, path_pickle='app/data/farsite.pickle'):
    """
    Processes the FARSITE data pickle created by `app.modeling.data_preparation.prepare_data`
    and converts input lat/lon to farsite data array indices

    :param lat: latitudinal coordinate of ignition
    :param lon: longitudinal coordinate of ignition
    :param path_pickle: path to the preprocessed farsite pickle data
    :return: unpickled data, istart, jstart, wind_speed, wind_direction
    """

    # Load pickled data, otherwise generate pickle
    # data is INPUT (landfire stuff), FUEL (raw fuel types), X (longitudes), Y (latitudes)
    data = pickle.load(open(path_pickle, "rb")) if os.path.exists(path_pickle) else prepare_data()

    # get starting cell
    i_start, j_start = np.argmin(np.abs(data[2] - lon)), np.argmin(np.abs(data[3] - lat))


    # get weather information (converting wind speed in kt -> ft/min, degrees -> radians)
    weather = CurrentWeather(20, lat, lon)
    weather = weather.weather_by_station(weather.getNearestStation())
    wind_speed, wind_dir = weather.loc['wind_speed_kt']*101.269, weather.loc['wind_dir_degrees']*(np.pi/180)

    # determine slope information

    switch = [lambda x : x > 330 or x < 30, lambda x: 30 <= x < 60, lambda x: 60 <= x < 120, lambda x: 120 <= x < 150,
              lambda x: 150 <= x < 210, lambda x: 210 <= x < 240, lambda x: 240 <= x < 300, lambda x: x <= 300]

    case = [(0,1), (-1,1), (-1,0), (-1,-1), (0,-1), (1,-1), (1,0), (1,1)]
    ip, jp = case[0]
    for i,f in enumerate(switch):
        if f((wind_dir*(180/np.pi)) - 20):
            ip, jp = case[i]

    INPUT = data[0]

    if not os.path.exists("app/data/slope" + str(ip) + str(jp) + ".pickle"):
        build_tanphi_arrays()

    INPUT[:, :, 5] = pickle.load(open("app/data/slope" + str(ip) + str(jp) + ".pickle", "rb"))

    return INPUT, data[1], data[2], data[3], i_start, j_start, wind_speed, wind_dir


def handle_new_fire_point(new_frontier, FIRES, AFC, PIFC, INPUT, FUEL, wind_speed, wind_dir, cell, new_i, new_j, new_x, new_y):
    """
    Handles a new fire (updates frontier, both caches, regrids, ect)
    :param new_frontier: new frontier of fires this fire is pushed to
    :param INPUT: input array as described above
    :param FUEL: fuel array as described above
    :param wind_speed: wind speed (ft/min)
    :param wind_dir: wind direction (radians)
    :param AFC: A reference to the active fire cache
    :param FIRES: all fires
    :param PIFC: a reference to the past intracellular fire cache
    :param cell: the cell the fire originated from
    :param new_i: index of new row
    :param new_j: index of new column
    :param new_x: the (prior to regrid) new x
    :param new_y: the (prior to regrid) new y
    """

    if (0 <= new_i < (INPUT.shape[0])) and (0 <= new_j < (INPUT.shape[1])) and burnable(FUEL[new_i, new_j]):

        # we added a new fire, that means we need to know the dimension of the grid it is placed
        # if the dimension differs from that of our original cell, we need to reconcile
        if new_i != cell[0] or new_j != cell[1]:
            new_x, new_y = regrid(AFC, INPUT, wind_speed, wind_dir, new_i, new_j, new_x, new_y, cell)

        if (new_i, new_j) not in PIFC or (new_x, new_y) not in PIFC[(new_i, new_j)]:

            # Update PIFC as necessary
            if (new_i, new_j) not in PIFC:
                PIFC[(new_i, new_j)] = set([(new_x, new_y)])
            else:
                PIFC[(new_i, new_j)].add((new_x, new_y))

            # Update frontier as necessary
            if (new_i, new_j) not in new_frontier:
                new_frontier[(new_i, new_j)] = set([(new_x, new_y)])
            else:
                new_frontier[(new_i, new_j)].add((new_x, new_y))

            FIRES.add((new_i, new_j))


def regrid(AFC, INPUT, wind_speed, wind_dir, new_i, new_j, new_x, new_y, cell):
    """
    regrids fires when they switch cells, updates AFC for cell if necessary
    :param AFC: A reference to the active fire cache
    :param INPUT: the input array as described above
    :param wind_speed: wind speed (ft/min)
    :param wind_dir: wind direction (radians)
    :param new_i: index of new row
    :param new_j: index of new column
    :param new_x: the (prior to regrid) new x
    :param new_y: the (prior to regrid) new y
    :param cell: the cell where the fire spread from
    :return: new_x, new_y - these are the coordinates post regrid
    """

    if (new_i, new_j) not in AFC:

        wd_perturbation = np.random.rand()*.52 - .26
        ws_perturbation = np.random.rand()*.30 - .15
        AFC[(new_i, new_j)] = FireCell(INPUT, new_i, new_j, wind_speed*(1 + ws_perturbation), wind_dir + wd_perturbation)

    grid_dimension = AFC[cell].dim
    new_grid_dimension = AFC[(new_i, new_j)].dim
    new_x = int(np.floor((new_x / (grid_dimension - 1)) * new_grid_dimension))
    new_y = int(np.floor((new_y / (grid_dimension - 1)) * new_grid_dimension))

    return new_x, new_y

def build_result(FIRES, X, Y):
    """
    maps fire indices to lat/lon coordinates
    :param X: latitudes
    :param Y: longituds
    :param FIRES: fire cell coordinates
    :return: dataframe to pass forward
    """
    FIRES_LATLON = pd.DataFrame({(X[pair[0]], Y[pair[1]]) for pair in FIRES})
    FIRES_LATLON.columns = ["x", "y"]
    return FIRES_LATLON


def burn(lat, lon, path_pickle='app/data/farsite.pickle', mins=1000):
    """
    burning down the house

    :param lat: latitude of ignition
    :param lon: longitude of ignition
    :param pack_pickle: path to preprocessed data pickle
    :param mins: number of one minute iterations to burn for
    :return: a set of cells burned after all iterations are complete
    """

    # Load preprocessed data
    INPUT, FUEL, X, Y, i_start, j_start, wind_speed, wind_dir = pre_burn(lat, lon, path_pickle)
    FIRES = set([(i_start, j_start)])

    if not burnable(FUEL[i_start, j_start]):
        return build_result(FIRES, X, Y)

    # # #
    # Fires are 1x2 arrays of integers, where:
    # fire[0] and fire[1] are row and column intracellular coordinates
    #
    # We re-grid each cell on the fly to match the resolution required by R and our time step
    #

    # (A.F.C. - Active Fire Cache) Cache information for cells which are actively burning
    # Cells without active fires are regularly purged
    AFC = dict()

    # (P.I.F.C. - Past Intracellular Fire Cache)
    # Refreshed after TBD iterations, stores intracellular points which have had fire
    # two dimensional map: cell -> set of points which have had fire
    PIFC = dict()

    # Compute info for initial fire
    AFC[(i_start, j_start)] = FireCell(INPUT, i_start, j_start, wind_speed, wind_dir)

    initial_fire = (int(np.floor(AFC[(i_start, j_start)].dim / 2)), int(np.floor(AFC[(i_start, j_start)].dim / 2)))

    PIFC[(i_start, j_start)] = set([initial_fire])
    frontier = dict([((i_start, j_start), set([initial_fire]))])  # Fires which will be iterated on this iteration

    for t in range(mins):

        if not frontier:
            break

        new_frontier = {}

        for cell in frontier:

            if not t%AFC[cell].t:

                inputs = INPUT[cell[0], cell[1]]
                cell_info = AFC[cell]

                for fire in frontier[cell]:

                    wd = cell_info.dim - 1
                    curx, cury = fire

                    # Spread in direction of wind
                    new_x = curx + cell_info.Wx
                    new_y = cury + cell_info.Wy
                    new_i = int(cell[0] + new_y // (wd))
                    new_j = int(cell[1] + new_x // (wd))
                    new_x %= wd
                    new_y %= wd

                    # Spread in direction wind + pi/2
                    new_OPx = curx + cell_info.OPx
                    new_OPy = cury + cell_info.OPy
                    new_OPi = int(cell[0] + new_OPy // (wd))
                    new_OPj = int(cell[1] + new_OPx // (wd))
                    new_OPx %= wd
                    new_OPy %= wd

                    # Spread in direction wind - pi/2
                    new_OMx = curx + cell_info.OMx
                    new_OMy = cury + cell_info.OMy
                    new_OMi = int(cell[0] + new_OMy // (wd))
                    new_OMj = int(cell[1] + new_OMx // (wd))
                    new_OMx %= wd
                    new_OMy %= wd

                    handle_new_fire_point(new_frontier, FIRES, AFC, PIFC, INPUT, FUEL, wind_speed, wind_dir, cell, new_i, new_j, new_x, new_y)
                    handle_new_fire_point(new_frontier, FIRES, AFC, PIFC, INPUT, FUEL, wind_speed, wind_dir, cell, new_OPi, new_OPj, new_OPx, new_OPy)
                    handle_new_fire_point(new_frontier, FIRES, AFC, PIFC, INPUT, FUEL, wind_speed, wind_dir, cell, new_OMi, new_OMj, new_OMx, new_OMy)

            else:
                new_frontier[cell] = frontier[cell]

        if not t % 200: PIFC = {cell: PIFC[cell] for cell in PIFC if cell in new_frontier}

        frontier = new_frontier

    return build_result(FIRES, X, Y)
