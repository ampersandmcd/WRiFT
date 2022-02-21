#################################################
#################################################
#################################################
##### FARSITE ALPHA (02/20/22)
##### Rothermel Surface Spread Only

################################################
############ External Modules
################################################

# Data containers and pre-processing
import xarray as xr
import rioxarray
import pandas as pd

# Computationl Tools
import numpy as np

# Display/Output Tools
import matplotlib.pyplot as plt
import plotly.express as px

# Weather query tools
import requests
from io import StringIO
import geopy.distance


################################################
############ Weather Querying (Thank you Nathan)
################################################

def _weatherDataToDF(text: str):
    f"""
    Convert an ADDS server response to a DataFrame indexed by station.
    @param text: The string of weather data to be converted.
    """
    buffer = StringIO(text)
    df = pd.read_csv(buffer, skiprows=5, parse_dates=['observation_time'])
    df = df.drop(["raw_text"], axis=1)
    df.set_index("station_id", inplace=True)
    return df


def _coordDistance(row, lat, long):
    f"""
    Given an associative array containing 'latitude' and 'longitude'
    columns, calculate the distance from the lat and long passed in.
    @param row: the associative array containing 'latitude' and 'longitude' keys
    @param lat: the latitude of the point to calculate distance from
    @param long: the longitude of the point to calculate distance from
    """
    return geopy.distance.distance((lat, long), (row['latitude'], row['longitude'])).mi


class CurrentWeather:
    f"""
    Use the NOAA Aviation Weather Center to retrieve current weather information
    from all stations near a specified point.
    """
    BASE_URL = "https://aviationweather.gov/adds/dataserver_current/httpparam"
    SINGLE_METAR_SIZE = 42

    def __init__(self, radius, lat, long):
        f"""
        Initialize a @Link{CurrentWeather} object.
        :param radius: The radius to collect weather data within. [Statute Miles]
        :param lat: The latitude to center data collection on.
        :param long: The longitude to center data collection on.
        """
        self.radius = radius  # Statute miles
        self.lat = lat  # Center of radius
        self.long = long  # Center of radius
        self.data = pd.DataFrame()
        self.refreshData()

    def refreshData(self):
        f"""
        Pull the most recent data from the ADDS server.
        """
        data_text = self._collectWeatherData()
        self.data = _weatherDataToDF(data_text)

    def _collectWeatherData(self) -> str:
        f"""
        Collect current weather data from all stations available within this @Link{CurrentWeather}
        object's radius.
        """
        distance_string = F"{self.radius};{self.long},{self.lat}"

        query = {"dataSource": "metars", "requestType": "retrieve", "format": "csv",
                 "radialDistance": distance_string, "hoursBeforeNow": "1"}

        return requests.get(self.BASE_URL, params=query).text

    def getNearestStation(self):
        f"""
        Find the nearest weather station in this @Link{CurrentWeather} to the
        latitude and longitude provided.
        """
        distances = self.data.apply(_coordDistance, axis=1, lat=self.lat, long=self.long)
        return distances.idxmin()

    def mostRecentData(self):
        f"""
        Get the most recent data available.
        Only returns data for a single station.
        """
        return self.data.iloc[0]

    def dataByStation(self, station):
        f"""
        Get the most recent data corresponding to the given station.
        @param station: The station to search for
        """
        data = self.data.loc[station]
        if data.size > self.SINGLE_METAR_SIZE:
            return data.iloc[0]


################################################
############ Data Processing
################################################

def prepare_data(lat, lon, path_landfire, path_fueldict):
    """
    Prepares the data required for fire modeling
    :param lat: latitude coordinate of ignition point
    :param lon: longitude coordinate of ignition point
    :param path_landfire: path to the file farsite.nc, containing LANDFIRE data
    :param path_fueldict: path to the file FUEL_DIC.csv, containing translation info for fuel types
    :return: INPUT and FUEL, arrays described below, wind speed (ft/min), and wind direction (radians),
             start_i and start_j starting indices of fire
    """
    # we also need grid coordinates for the lat/lon, so lets perform that conversion

    LATLON = xr.open_dataset(path_landfire, decode_coords="all")
    LATLON = LATLON.rio.reproject("EPSG:4326")
    i_start = np.argmin(np.abs(LATLON['x'].data-lon))
    j_start = np.argmin(np.abs(LATLON['y'].data-lat))

    del LATLON

    # # #
    # Query Wind Speed and Direction
    # # #

    wtr = CurrentWeather(20, lat, lon)
    wtr = wtr.dataByStation(wtr.getNearestStation())

    wind_speed, wind_dir = wtr.loc['wind_speed_kt'], wtr.loc['wind_dir_degrees']

    # convert kt -> ft/min
    wind_speed *= 101.269

    # TO DO fix weird wind direction issue


    # # #
    # Fuel data processing
    # # #

    LANDFIRE = xr.open_dataset(path_landfire, decode_coords="all")
    FUEL = LANDFIRE['US_210F40'][:].data
    ELEV = LANDFIRE['US_DEM'][:].data


    INPUT = np.zeros((FUEL.shape[0], FUEL.shape[1], 6), dtype=np.float32) # 32 bit float for efficiency

    # from fuel types we need:
    #
    # (dim 0) Fuel Bed Depth (delta)  - Mean fuel array value in ft
    # (dim 1) SA to Vol Ratio (sigma) - (ft^-1)
    # (dim 2) Oven-dry fuel load (w_0)- (lb/ft^2) must convert from tons/acre
    # (dim 3) Extinction Moisture (Mx)- Should be very close to fuel moisture
    # (dim 4) Fuel Moisture (Mf)      - Approximated as proportion of extinction moisture
    #
    #
    # from elevation we need:
    #
    # (dim 5) tan_phi - Vertical rise / horizontal distance (((IN DIRECTION OF WIND))), unitless


    FUEL_TYPE_MAP = pd.read_csv(path_fueldict, header='infer').set_index('VALUE')
    FUEL_TYPE_MAP = {float(ind):np.array([FUEL_TYPE_MAP['FuelBedDepth'][ind],
                                          FUEL_TYPE_MAP['SAV'][ind],
                                          FUEL_TYPE_MAP['OvenDryLoad'][ind],
                                          FUEL_TYPE_MAP['Mx'][ind]/100,
                                          (FUEL_TYPE_MAP['Mx'][ind]*.95)/100, 0])
                     for ind in FUEL_TYPE_MAP.index}

    for i in range(INPUT.shape[0]):
        for j in range(INPUT.shape[1]):

            # pull essential data
            INPUT[i,j,:] = FUEL_TYPE_MAP[FUEL[i,j] if FUEL[i,j] else -9999.]

            # (dim 2): ton/acre -> lb/ft^2
            INPUT[i,j,2] *= .0459137

    # second pass for elevation (tan_phi)

    if wind_dir > 330 or wind_dir < 30:
        ip, jp = 0,1
    elif 30 <= wind_dir < 60:
        ip, jp = -1,1
    elif 60 <= wind_dir < 120:
        ip, jp = -1,0
    elif 120 <= wind_dir < 150:
        ip, jp = -1, -1
    elif 150 <= wind_dir < 210:
        ip, jp = 0,-1
    elif 210 <= wind_dir < 240:
        ip, jp = 1,-1
    elif 240 <= wind_dir < 300:
        ip, jp = 1,0
    else:
        ip, jp = 1,1

    # wind_dir degrees -> radians
    wind_dir *= np.pi/180

    #
    # Loops below compute (or estimate) tan_phi for each cell

    for i in range(1, INPUT.shape[0] - 1):
        for j in range(1, INPUT.shape[1] - 1):
            INPUT[i,j,5] = (ELEV[i+ip,j+jp]-ELEV[i,j])/30

    # edges don't have adjacent cells yet, so lets just guess
    for i in range(INPUT.shape[0]):
        INPUT[i,0,5] = INPUT[i,1,5] # left col
        INPUT[0,i,5] = INPUT[1,i,5] # top row

        # right col
        INPUT[i,INPUT.shape[1] - 1, 5] = INPUT[i,INPUT.shape[1] - 2, 5]

        # bottom row
        INPUT[INPUT.shape[0] - 1, i, 5] = INPUT[INPUT.shape[0] - 2, i, 5]

    return INPUT, FUEL, wind_speed, wind_dir, i_start, j_start


################################################
############ Rothermel Surface Spread EQs
################################################

def eq_A(sigma):
    """
    :param sigma: Surface-area-to-volume ratio (ft2/ft3)
    :return: A: A
    """
    return 113 * (sigma ** -0.7913)

def eq_r_M(M_f, M_x):
    """
    :param M_f: Moisture content (fraction)
    :param M_x: Dead fuel moisture of extinction (fraction)
    :return: r_M: r_M
    """
    return min(M_f / M_x, 1)

def eq_12(M_f):
    """
    :param M_f: Moisture content (fraction)
    :return: Q_ig: heat of pre-ignition (Kj/Kg)
    """
    return 250 + 1116*M_f

def eq_14(sigma):
    """
    :param sigma: Surface-area-to-volume ratio (ft2/ft3)
    :return: epsilon: effective heating number, dimensionless
    """
    return np.exp(-138 / sigma)

def eq_24(w_0, S_T = 0.0555):
    """
    :param w_0: Oven-dry fuel load (lb/ft2)
    :param S_T: Total mineral content, equal to 0.0555
    :return: w_n: Net fuel load (lb/ft^2)
    """
    return w_0 * (1 - S_T)

def eq_27(Gamma_prime, w_n, eta_M, eta_s, h = 8000):
    """
    :param Gamma_prime: Optimum reaction velocity (min^-1)
    :param w_n: Net fuel load (lb/ft^2)
    :param h: Low heat content (Btu/lb) Often 8,000 Btu/lb
    :param eta_M: Moisture damping coefficient
    :param eta_s: Mineral damping coefficient
    :return: IR, Reacton Intensity (Kj/min/m^2)
    """
    return Gamma_prime * w_n * h * eta_M * eta_s

def eq_29(r_M):
    """
    :param r_M: r_M
    :return: eta_M: Moisture damping coefficient
    """
    return 1 - 2.59 * (r_M) + 5.11 * (r_M ** 2) - 3.52 * (r_M ** 3)

def eq_30(S_e = 0.010):
    """
    :param S_e: Effective mineral content (fraction) Generally 0.010
    :return: eta_s: Mineral damping coefficient
    """
    return min(0.174 * (S_e ** -0.19), 1)


def eq_31(rho_b, rho_p = 32):
    """
    :param rho_b: Oven-dry bulk density (lb/ft3)
    :param rho_p: Oven-dry particle density (lb/ft3), which is equal to 32
    :return: beta: Packing ratio
    """
    return rho_b / rho_p

def eq_36(sigma):
    """
    :param sigma: Surface-area-to-volume ratio (ft2/ft3)
    :return: Gamma_prime_max: Maximum reaction velocity (min^-1)
    """
    return (sigma ** 1.5) / (495 + 0.0594 * (sigma ** 1.5))

def eq_37(sigma):
    """
    :param sigma: Surface-area-to-volume ratio (ft2/ft3)
    :return: beta_op: Packing ratio optimum
    """
    return 3.348 * (sigma ** -0.8189)

def eq_38(Gamma_prime_max, beta, beta_op, A):
    """
    :param Gamma_prime_max: Maximum reaction velocity (min^-1)
    :param beta: Packing ratio
    :param beta_op: Packing ratio optimum
    :param A: A
    :return: Gamma_prime: Optimum reaction velocity (min^-1)
    """
    return Gamma_prime_max * (beta / beta_op) ** A * np.exp(A * (1 - beta/beta_op))

def eq_40(w_0, delta):
    """
    :param w_0: Oven-dry fuel load (lb/ft2)
    :param delta: Fuel bed depth (ft)
    :return: rho_b: Oven-dry bulk density (lb/ft3)
    """
    return w_0 / delta

def eq_42(sigma, beta):
    """
    :param sigma: Surface-area-to-volume ratio (ft2/ft3)
    :param beta: Packing ratio
    :return: xi: propogating flux ratio, unitless
    """
    return  np.exp((0.792 + 0.681 * np.sqrt(sigma)) *(beta + 0.1)) / (192 + 0.2595 * sigma)

def eq_47(C, U, B, beta, beta_op, E): # eq_12
    """
    :param C: Function of fuel partical size in fuel bed
    :param U: Wind velocity at midflame height (ft/min)
    :param B: Function of fuel partical size in fuel bed
    :param beta: packing ratio of fuel bed (from fuel type data)
    :param beta_op: optimum packing ratio
    :param E: Function of fuel partical size in fuel bed
    :return: Phi_w, dimensionless coefficient for midflame wind speed
    """
    CUB = C*(U**B)
    return CUB*(beta/beta_op)**(-E)

def eq_48(sigma):
    """
    :param sigma: Surface-area-to-volume ratio (ft2/ft3)
    :return: C: Function of fuel partical size in fuel bed
    """
    return 7.47 * np.exp(-.133 * (sigma ** 0.55))

def eq_49(sigma):
    """
    :param sigma: Surface-area-to-volume ratio (ft2/ft3)
    :return: B: Function of fuel partical size in fuel bed
    """
    return 0.02526 * (sigma ** 0.54)

def eq_50(sigma):
    """
    :param sigma: Surface-area-to-volume ratio (ft2/ft3)
    :return: E: Function of fuel partical size in fuel bed
    """
    return 0.715  * np.exp(-3.59 * (10 ** -4) * sigma)

def eq_51(beta, tan_phi):
    """
    :param beta: Packing ratio
    :param tan_phi: Slope steepness, maximum (fraction) Vertical rise / horizontal distance
    """
    return 5.275 * (beta ** -0.3) * (tan_phi **2)

def eq_52(IR, xi, rho_b, epsilon, Q_ig, Phi_w, Phi_s): # eq_18
    """
    :param IR: Reacton Intensity (Kj/min/m^2)
    :param xi: propogating flux ratio, unitless
    :param rho_b: ovendry bulk density (kg/m^3)
    :param epsilon: effective heating number, dimensionless
    :param Q_ig: heat of pre-ignition (Kj/Kg)
    :param Phi_w: dimensionless coefficient for midflame wind speed, from eq_11
    :param Phi_s: dimensionless coefficient of slope, from eq_12
    :return: R, fire spread rate (m/min)
    """
    num = IR*xi*(1 + Phi_w + Phi_s)
    den = rho_b*epsilon*Q_ig
    return num/den


################################################
############ Computation Tools
################################################

def compute_surface_spread(inputs, wind_speed):
    """
    Wraps all the above functions into one function, computing surface spread rate
    :param inputs: input array, explained below
    :param wind_speed: wind speed (ft/min)
    :return: R, fire spreadrate (m/min)
    """

    delta   = inputs[0] # Fuel bed depth (ft)
    sigma   = inputs[1] # Surface-area-to-volume ratio (ft2/ft3)
    w_0     = inputs[2] # Oven-dry fuel load (lb/ft2)
    Mx      = inputs[3] # Extinction Moisture (portion of 1)
    Mf      = inputs[4] # Fuel Moisture (portion of 1)
    tan_phi = inputs[5] # Slope steepness, maximum (fraction) Vertical rise / horizontal distance

    U = wind_speed


    C, B, E = eq_48(sigma), eq_49(sigma), eq_50(sigma)     # Fuel Partical Size Constants
    Q_ig = eq_12(Mf)                                       # Heat of pre-ignition (Kj/Kg)
    epsilon = eq_14(sigma)                                 # Effective heating number, dimensionless
    eta_s = eq_30()                                        # Mineral Damping Coefficient
    r_M = eq_r_M(Mf, Mx)                                   # Ratio Mf/Mx
    eta_M = eq_29(r_M)                                     # Moisture Damping Constant
    w_n = eq_24(w_0)                                       # Net Fuel Load lb/ft^2 (CACHE THIS?)
    A = eq_A(sigma)                                        # Some Constant
    beta_op = eq_37(sigma)                                 # Optimum Packing Ratio
    rho_b = eq_40(w_0, delta)                              # Oven-dry bulk fuel density (lb/ft^3)
    beta = eq_31(rho_b)                                    # Packing Ratio
    Phi_s = eq_51(beta, tan_phi)                           # Slope Steepness
    Phi_w = eq_47(C, U, B, beta, beta_op, E)               # coefficient for midflame wind speed
    xi = eq_42(sigma, beta)                                # propogating flux ratio, unitless
    Gamma_prime_max = eq_36(sigma)                         # Maximum reaction velocity (min^-1)
    Gamma_prime = eq_38(Gamma_prime_max, beta, beta_op, A) # Optimum reaction velocity (min^-1)
    IR = eq_27(Gamma_prime, w_n, eta_M, eta_s)             # Reacton Intensity (Kj/min/m^2)
    R = eq_52(IR, xi, rho_b, epsilon, Q_ig, Phi_w, Phi_s)  # Rate of Fire Spread in Wind Dir (ft/min)

    return R

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
        new_R = compute_surface_spread(new_cell_inputs, wind_speed)*.3048

        new_orthogonal_spread = ((2**.5)/5)*new_R
        new_grid_dimension = int(np.ceil(30/new_orthogonal_spread))

        # convert m/min -> grid steps per min
        new_R *= (new_grid_dimension/30)
        new_orthogonal_spread *= (new_grid_dimension/30)

        new_x_inc = int(np.rint(new_R*np.cos(wind_dir)))
        new_y_inc = int(np.rint(new_R*np.sin(wind_dir)))

        AFC[(new_i, new_j)] = np.array([new_x_inc, new_y_inc, new_orthogonal_spread,
                                        new_grid_dimension, new_R])

    grid_dimension = AFC[cell][3]
    new_x = int(np.floor((new_x/(grid_dimension - 1))*new_grid_dimension))
    new_y = int(np.floor((new_y/(grid_dimension - 1))*new_grid_dimension))

    return new_x, new_y

def handle_new_fire_point(new_frontier, FIRES, NB, AFC, PIFC, INPUT, FUEL, wind_speed, wind_dir, cell, new_i, new_j, new_x, new_y):
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


def burn(lat, lon, path_landfire, path_fueldict, mins):
    """
    Burning down the house
    :param lat: latitude of ignition
    :param lon: longitude of ignition
    :param path_landfire: path to `landfire.nc`
    :param path_fueldict: path to `FUEL_DIC.csv`
    :param mins: number of one minute iterations to burn for
    :return: A set of cells burned after all iterations
    """
    data = prepare_data(lat, lon, path_landfire, path_fueldict)
    INPUT, FUEL, wind_speed, wind_dir, i_start, j_start = data[0], data[1], data[2], data[3], data[4], data[5]

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
    R = compute_surface_spread(inputs, wind_speed)*.3048
    wind_orthogonal_spread = ((2**.5)/5)*R
    grid_dimension = int(np.ceil(30/wind_orthogonal_spread))
    R *= (grid_dimension/30)
    wind_orthogonal_spread *= (grid_dimension/30)
    x_inc = int(np.rint(R*np.cos(wind_dir)))
    y_inc = int(np.rint(R*np.sin(wind_dir)))
    initial_fire = (int(np.floor(grid_dimension/2)), int(np.floor(grid_dimension/2)))

    # place initial fire in AFC and PIFC
    AFC[(i_start, j_start)]  = np.array([x_inc, y_inc, wind_orthogonal_spread, grid_dimension, R])
    PIFC[(i_start, j_start)] = set([initial_fire])

    frontier = dict([((i_start, j_start),set([initial_fire]))]) # Fires which will be iterated on this iteration
    FIRES    = set([(i_start, j_start)])                        # Final output: cells which have had fire at any point

    # Quick check for which fuel types will not burn, we have to be careful to skip these
    NB = set([91., 92., 93., 98., 99., 0.])

    if FUEL[i_start, j_start] in NB:
        raise Exception("Non-Burnable Starting Location")

    for t in range(500):

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
                new_i = int(cell[0] + new_y//(grid_dimension-1))
                new_j = int(cell[1] + new_x//(grid_dimension-1))
                new_x %= (grid_dimension-1)
                new_y %= (grid_dimension-1)

                x1_orth_inc = int(np.rint(wind_orthogonal_spread*np.cos(wind_dir + np.pi/2)))
                y1_orth_inc = int(np.rint(wind_orthogonal_spread*np.sin(wind_dir + np.pi/2)))
                new_x_orth1 = fire[0] + x1_orth_inc
                new_y_orth1 = fire[1] + y1_orth_inc
                new_i_orth1 = int(cell[0] + new_y_orth1//(grid_dimension-1))
                new_j_orth1 = int(cell[1] + new_x_orth1//(grid_dimension-1))
                new_x_orth1 %= (grid_dimension-1)
                new_y_orth1 %= (grid_dimension-1)

                x2_orth_inc = int(np.rint(wind_orthogonal_spread*np.cos(wind_dir - np.pi/2)))
                y2_orth_inc = int(np.rint(wind_orthogonal_spread*np.sin(wind_dir - np.pi/2)))
                new_x_orth2 = fire[0] + x2_orth_inc
                new_y_orth2 = fire[1] + y2_orth_inc
                new_i_orth2 = int(cell[0] + new_y_orth2//(grid_dimension-1))
                new_j_orth2 = int(cell[1] + new_x_orth2//(grid_dimension-1))
                new_x_orth2 %= (grid_dimension-1)
                new_y_orth2 %= (grid_dimension-1)

                handle_new_fire_point(new_frontier, FIRES, NB, AFC, PIFC, INPUT, FUEL, wind_speed,
                                      wind_dir, cell, new_i, new_j, new_x, new_y)
                handle_new_fire_point(new_frontier, FIRES, NB, AFC, PIFC, INPUT, FUEL, wind_speed,
                                      wind_dir, cell, new_i_orth1, new_j_orth1, new_x_orth1, new_y_orth1)
                handle_new_fire_point(new_frontier, FIRES, NB, AFC, PIFC, INPUT, FUEL, wind_speed,
                                      wind_dir, cell, new_i_orth2, new_j_orth2, new_x_orth2, new_y_orth2)


        if not t % 50: PIFC = {cell:PIFC[cell] for cell in PIFC if cell in new_frontier}

        frontier = new_frontier

    return FIRES


fires = burn(37.2, -121.592092, 'capstone/CapstoneExploration/data/farsite.nc', 'capstone/CapstoneExploration/FUEL_DIC.csv', 500)
plt.scatter([item[1] for item in fires], [item[0] for item in fires])
plt.show()
