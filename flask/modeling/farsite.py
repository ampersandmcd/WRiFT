#################################################
#################################################
#################################################
##### FARSITE ALPHA (02/20/22)
##### Rothermel Surface Spread Only

################################################
############ External Modules
################################################

# weather processing module (thank you nathan)
from modeling.data.current_weather import CurrentWeather

from modeling.models.rothermel import compute_surface_spread

# Data containers and pre-processing
import pandas as pd
import pickle

# Computational Tools
import numpy as np
import pandas as pd


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
    if (new_i, new_j) in AFC:

        new_grid_dimension = AFC[(new_i, new_j)][3]

    else:

        # if the cell isn't in the AFC, reconcile then place it
        new_cell_inputs = INPUT[new_i, new_j]
        new_R = compute_surface_spread(new_cell_inputs, wind_speed) * .3048

        new_orthogonal_spread = ((2 ** .5) / 5) * new_R
        new_grid_dimension = int(np.ceil(30 / new_orthogonal_spread))

        # convert m/min -> grid steps per min
        new_R *= (new_grid_dimension / 30)
        new_orthogonal_spread *= (new_grid_dimension / 30)

        new_x_inc = int(np.rint(new_R * np.cos(wind_dir)))
        new_y_inc = int(np.rint(new_R * np.sin(wind_dir)))

        AFC[(new_i, new_j)] = np.array([new_x_inc, new_y_inc, new_orthogonal_spread,
                                        new_grid_dimension, new_R])

    grid_dimension = AFC[cell][3]
    new_x = int(np.floor((new_x / (grid_dimension - 1)) * new_grid_dimension))
    new_y = int(np.floor((new_y / (grid_dimension - 1)) * new_grid_dimension))

    return new_x, new_y

def handle_new_fire_point(new_frontier, FIRES, NB, AFC, PIFC, INPUT, FUEL, wind_speed, wind_dir, cell, new_i, new_j,
                          new_x, new_y):
    """
    Handles a new fire (updates frontier, both caches, regrids, ect)
    :param new_frontier: new frontier of fires this fire is pushed to
    :param INPUT: input array as described above
    :param FUEL: fuel array as described above
    :param wind_speed: wind speed (ft/min)
    :param wind_dir: wind direction (radians)
    :param AFC: A reference to the active fire cache
    :param FIRES: all fires
    :param NB: set of non burnable terrains
    :param PIFC: a reference to the past intracellular fire cache
    :param cell: the cell the fire originated from
    :param new_i: index of new row
    :param new_j: index of new column
    :param new_x: the (prior to regrid) new x
    :param new_y: the (prior to regrid) new y
    """

    if (0 <= new_i < INPUT.shape[0]) and (0 <= new_j < INPUT.shape[1]) and FUEL[new_i, new_j] not in NB:

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

def pre_burn(lat, lon, path_pickle):
    """
    Processes a provided data pickle, as well as lat/lon to get info for burn
    :param lat: latitudinal coordinate of ignition
    :param lon: longitudinal coordiante of ignition
    :param path_pickle: path to the preprocessed pickle data
    :return: unpickled data, istart, jstart, wind speed, wind direction
    """
    # INPUT (landfire stuff), FUEL (raw fuel type), X (longitudes), Y (latitudes)
    # INPUT must be expanded to account for slope in direction of wind
    with open(path_pickle, "rb") as f:
        data = pickle.load(f)

    # get starting cell
    i_start, j_start = np.argmin(np.abs(data[2] - lon)), np.argmin(np.abs(data[3] - lat))

    ######
    ## get weather info

    weather = CurrentWeather(20, lat, lon)
    weather = weather.weather_by_station(weather.getNearestStation())

    wind_speed, wind_dir = weather.loc['wind_speed_kt'], weather.loc['wind_dir_degrees']

    # convert kt -> ft/min
    wind_speed *= 101.269

    ######
    ## Get slope in direction of wind

    if wind_dir > 330 or wind_dir < 30:
        ip, jp = 0, 1
    elif 30 <= wind_dir < 60:
        ip, jp = -1, 1
    elif 60 <= wind_dir < 120:
        ip, jp = -1, 0
    elif 120 <= wind_dir < 150:
        ip, jp = -1, -1
    elif 150 <= wind_dir < 210:
        ip, jp = 0, -1
    elif 210 <= wind_dir < 240:
        ip, jp = 1, -1
    elif 240 <= wind_dir < 300:
        ip, jp = 1, 0
    else:
        ip, jp = 1, 1

    # wind_dir degrees -> radians
    wind_dir *= np.pi / 180

    INPUT = data[0]

    #
    # Loops below compute (or estimate) tan_phi for each cell

    for i in range(1, INPUT.shape[0] - 1):
        for j in range(1, INPUT.shape[1] - 1):
            INPUT[i, j, 5] = (INPUT[i + ip, j + jp, 5] - INPUT[i, j, 5]) / 30

    # edges don't have adjacent cells yet, so lets just guess
    for i in range(INPUT.shape[0]):
        INPUT[i, 0, 5] = INPUT[i, 1, 5]  # left col
        INPUT[0, i, 5] = INPUT[1, i, 5]  # top row

        # right col
        INPUT[i, INPUT.shape[1] - 1, 5] = INPUT[i, INPUT.shape[1] - 2, 5]

        # bottom row
        INPUT[INPUT.shape[0] - 1, i, 5] = INPUT[INPUT.shape[0] - 2, i, 5]


    return INPUT, data[1], data[2], data[3], i_start, j_start, wind_speed, wind_dir


def burn(lat, lon, path_landfire=None, path_fueldict=None, path_pickle=None, mins=500):
    """
    Burning down the house
    :param lat: latitude of ignition
    :param lon: longitude of ignition
    :param path_landfire: path to `landfire.nc`
    :param path_fueldict: path to `FUEL_DIC.csv`
    :param path_pickle: path to preprocessed pickle data
    :param mins: number of one minute iterations to burn for
    :return: A set of cells burned after all iterations
    """

    # load preprocessed data
    INPUT, FUEL, X, Y, i_start, j_start, wind_speed, wind_dir = pre_burn(lat, lon, path_pickle)

    # Quick check for which fuel types will not burn, we have to be careful to skip these
    NB = set([91., 92., 93., 98., 99., 0.])

    if FUEL[i_start, j_start] in NB:
        result = pd.DataFrame({(X[i_start], Y[j_start])})
        result.columns = ["x", "y"]
        return result

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
    inputs = INPUT[i_start, j_start, :]
    R = compute_surface_spread(inputs, wind_speed) * .3048
    wind_orthogonal_spread = ((2 ** .5) / 5) * R
    grid_dimension = int(np.ceil(30 / wind_orthogonal_spread))
    R *= (grid_dimension / 30)
    wind_orthogonal_spread *= (grid_dimension / 30)
    x_inc = int(np.rint(R * np.cos(wind_dir)))
    y_inc = int(np.rint(R * np.sin(wind_dir)))
    initial_fire = (int(np.floor(grid_dimension / 2)), int(np.floor(grid_dimension / 2)))

    # place initial fire in AFC and PIFC
    AFC[(i_start, j_start)] = np.array([x_inc, y_inc, wind_orthogonal_spread, grid_dimension, R])
    PIFC[(i_start, j_start)] = set([initial_fire])

    frontier = dict([((i_start, j_start), set([initial_fire]))])  # Fires which will be iterated on this iteration
    FIRES = set([(i_start, j_start)])  # Final output: cells which have had fire at any point

    for t in range(mins):

        # quit if there are no fires to update
        if not frontier:
            break

        new_frontier = {}

        for cell in frontier:

            inputs = INPUT[cell[0], cell[1]]

            for fire in frontier[cell]:
                #####
                # Triangular Geometry
                #####

                info = AFC[cell]
                x_inc, y_inc, wind_orthogonal_spread, grid_dimension, R = info[0], info[1], info[2], info[3], info[4]

                new_x = fire[0] + x_inc
                new_y = fire[1] + y_inc
                new_i = int(cell[0] + new_y // (grid_dimension - 1))
                new_j = int(cell[1] + new_x // (grid_dimension - 1))
                new_x %= (grid_dimension - 1)
                new_y %= (grid_dimension - 1)

                x1_orth_inc = int(np.rint(wind_orthogonal_spread * np.cos(wind_dir + np.pi / 2)))
                y1_orth_inc = int(np.rint(wind_orthogonal_spread * np.sin(wind_dir + np.pi / 2)))
                new_x_orth1 = fire[0] + x1_orth_inc
                new_y_orth1 = fire[1] + y1_orth_inc
                new_i_orth1 = int(cell[0] + new_y_orth1 // (grid_dimension - 1))
                new_j_orth1 = int(cell[1] + new_x_orth1 // (grid_dimension - 1))
                new_x_orth1 %= (grid_dimension - 1)
                new_y_orth1 %= (grid_dimension - 1)

                x2_orth_inc = int(np.rint(wind_orthogonal_spread * np.cos(wind_dir - np.pi / 2)))
                y2_orth_inc = int(np.rint(wind_orthogonal_spread * np.sin(wind_dir - np.pi / 2)))
                new_x_orth2 = fire[0] + x2_orth_inc
                new_y_orth2 = fire[1] + y2_orth_inc
                new_i_orth2 = int(cell[0] + new_y_orth2 // (grid_dimension - 1))
                new_j_orth2 = int(cell[1] + new_x_orth2 // (grid_dimension - 1))
                new_x_orth2 %= (grid_dimension - 1)
                new_y_orth2 %= (grid_dimension - 1)

                handle_new_fire_point(new_frontier, FIRES, NB, AFC, PIFC, INPUT, FUEL, wind_speed,
                                      wind_dir, cell, new_i, new_j, new_x, new_y)
                handle_new_fire_point(new_frontier, FIRES, NB, AFC, PIFC, INPUT, FUEL, wind_speed,
                                      wind_dir, cell, new_i_orth1, new_j_orth1, new_x_orth1, new_y_orth1)
                handle_new_fire_point(new_frontier, FIRES, NB, AFC, PIFC, INPUT, FUEL, wind_speed,
                                      wind_dir, cell, new_i_orth2, new_j_orth2, new_x_orth2, new_y_orth2)

        if not t % 50: PIFC = {cell: PIFC[cell] for cell in PIFC if cell in new_frontier}

        frontier = new_frontier

    # map fire indices to lat/lon coords
    FIRES_LATLON = pd.DataFrame({(X[pair[0]], Y[pair[1]]) for pair in FIRES})
    FIRES_LATLON.columns = ["x", "y"]
    return FIRES_LATLON

# fires = burn(37.2, -121.592092, 'capstone/CapstoneExploration/data/farsite.nc', 'capstone/CapstoneExploration/FUEL_DIC.csv', 500)
# plt.scatter([item[1] for item in fires], [item[0] for item in fires])
# plt.show()
