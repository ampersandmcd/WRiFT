import pickle
import numpy as np
import xarray as xr
import pandas as pd
import os

def prepare_data(path_farsite="data/farsite.nc", path_fueldict="data/FUEL_DIC.csv"):
    """
    Prepares the data required for fire modeling - THIS DATA CAN (AND WILL) BE CACHED
    :param lat: latitude coordinate of ignition point
    :param lon: longitude coordinate of ignition point
    :param path_farsite: path to the file farsite.nc, containing LANDFIRE data
    :param path_fueldict: path to the file FUEL_DIC.csv, containing translation info for fuel types
    :return: INPUT and FUEL, arrays described below, X and Y arrays of lat/lon coordinates
    """
    # we also need grid coordinates for the lat/lon, so lets perform that conversion

    LATLON = xr.open_dataset(path_farsite, decode_coords="all")
    LATLON = LATLON.rio.reproject("EPSG:4326")
    X = LATLON["x"].data
    Y = LATLON["y"].data

    # # #
    # Fuel data processing
    # # #

    LANDFIRE = xr.open_dataset(path_farsite, decode_coords="all")
    FUEL = LANDFIRE['US_210F40'][:].data
    ELEV = LANDFIRE['US_DEM'][:].data

    INPUT = np.zeros((FUEL.shape[0], FUEL.shape[1], 6), dtype=np.float32)  # 32 bit float for efficiency

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
    # (dim 5) Elevation in meters

    FUEL_TYPE_MAP = pd.read_csv(path_fueldict, header='infer').set_index('VALUE')
    FUEL_TYPE_MAP = {float(ind): np.array([FUEL_TYPE_MAP['FuelBedDepth'][ind],
                                           FUEL_TYPE_MAP['SAV'][ind],
                                           FUEL_TYPE_MAP['OvenDryLoad'][ind],
                                           FUEL_TYPE_MAP['Mx'][ind] / 100,
                                           (FUEL_TYPE_MAP['Mx'][ind] * .95) / 100, 0])
                     for ind in FUEL_TYPE_MAP.index}

    for i in range(INPUT.shape[0]):
        for j in range(INPUT.shape[1]):
            # pull essential data
            INPUT[i, j, :] = FUEL_TYPE_MAP[FUEL[i, j] if FUEL[i, j] else -9999.]

            # (dim 2): ton/acre -> lb/ft^2
            INPUT[i, j, 2] *= .0459137

            # get elevation for final dimension
            INPUT[i, j, 5] = ELEV[i,j]

    data = INPUT, FUEL, X, Y
    with open("data/farsite.pickle", "wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
    return data

def build_tanphi_arrays(path_farsite_pickle="data/farsite.pickle"):
    """
    This divides the 360 degree arc into 8 slices, and creates a pickle for each
    Say wind points into slice A, then when burning we will load the slice A pickle
    :param path_farsite: path to the farsite pickle
    :return: None
    """
    coordinate_translation = [(0,1),   # wind east (remember column index is second)
                              (-1,1),  # north-east
                              (-1,0),  # north
                              (-1,-1), # north-west
                              (0,-1),  # west
                              (1,-1),  # south-west
                              (1,0),   # south
                              (1,1)]   # south-east

    with open(path_farsite_pickle, "rb") as f:
        INPUT = pickle.load(f)[0]

    for i_offset, j_offset in coordinate_translation:
        slope = np.zeros((INPUT.shape[0], INPUT.shape[1]))

        for i in range(1, INPUT.shape[0] - 1):
            for j in range(1, INPUT.shape[1] - 1):
                slope[i,j] = (INPUT[i + i_offset, j + j_offset, 5] - INPUT[i, j, 5]) / 30

        for i in range(INPUT.shape[0]):
            slope[i,0] = slope[i,1]
            slope[0,1] = slope[1,i]
            slope[i, slope.shape[1] - 1] = slope[i, slope.shape[1] - 2]
            slope[slope.shape[0] - 1, i] = slope[slope.shape[0] - 2, i]

        with open("data/slope" + str(i_offset) + str(j_offset), "wb") as f:
            pickle.dump(slope, f, protocol=pickle.HIGHEST_PROTOCOL)
