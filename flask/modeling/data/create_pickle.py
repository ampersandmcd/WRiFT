import pickle
import numpy as np
import pandas as pd
import xarray as xr
import rioxarray

from modeling.data.current_weather import CurrentWeather


def create_pickle():
    data = prepare_data("landfire_data/farsite.nc", "csv/FUEL_DIC.csv")

    with open("pickled_data/farsite.pickle", "wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

def prepare_data(path_landfire, path_fueldict):
    """
    Prepares the data required for fire modeling
    :param lat: latitude coordinate of ignition point
    :param lon: longitude coordinate of ignition point
    :param path_landfire: path to the file farsite.nc, containing LANDFIRE data
    :param path_fueldict: path to the file FUEL_DIC.csv, containing translation info for fuel types
    :return: INPUT and FUEL, arrays described below, X and Y arrays of lat/lon coordinates
    """
    # we also need grid coordinates for the lat/lon, so lets perform that conversion

    LATLON = xr.open_dataset(path_landfire, decode_coords="all")
    LATLON = LATLON.rio.reproject("EPSG:4326")
    X = LATLON["x"].data
    Y = LATLON["y"].data

    # # #
    # Fuel data processing
    # # #

    LANDFIRE = xr.open_dataset(path_landfire, decode_coords="all")
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

    return INPUT, FUEL, X, Y


if __name__ == "__main__":
    create_pickle()
