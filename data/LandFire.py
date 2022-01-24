import pandas as pd
from osgeo import gdal, gdalconst, _gdal


def GetBlockSize(band) -> (int, int):
    """
    How many entries per block? Used to traverse the
    raster in a memory-friendly way by retreiving one
    block at a time.
    :param band: The data band to find size of
    :return: A tuple of the form (x_block_size, y_block_size)
    """
    x = _gdal.ptrcreate('int', 0, 2)
    _gdal.GDALGetBlockSize(band._o, x, _gdal.ptradd(x, 1))
    result = (_gdal.ptrvalue(x, 0), _gdal.ptrvalue(x, 1))
    _gdal.ptrfree(x)
    return result


def computeOffset(dataset, x, y) -> (int, int):
    """
    Translates coordinates in units of meters
    to their corresponding position in the dataset
    :param dataset: The raster we're looking in
    :param x: x position in meters
    :param y: y position in meters
    :return: A tuple of the form (x_offset, y_offset)
    """
    geo_transform = dataset.GetGeoTransform()
    origin_x = geo_transform[0]
    origin_y = geo_transform[3]
    pixel_width = geo_transform[1]
    pixel_height = geo_transform[5]

    x_offset = int((x - origin_x) / pixel_width)
    y_offset = int((y - origin_y) / pixel_height)
    return x_offset, y_offset


def openRaster():
    """
    Open a raster, and return the dataset
    :return: The dataset of the raster specified
    """
    raster_file = r"LF2020_FBFM40_200_CONUS/Tif/LC20_F40_200.tif"

    gdal.AllRegister()
    dataset = gdal.Open(raster_file, gdalconst.GA_ReadOnly)

    if dataset is None:
        print('Could not open ' + raster_file)

    return dataset


def openLegend():
    """
    Open the legend specified
    :return: A dataframe containing the legend
    """
    legend_file = r"LF2020_FBFM40_200_CONUS/CSV_Data/LF16_F40_200.csv"

    legend = pd.read_csv(legend_file)

    return legend


def printInfo(dataset):
    """
    Print this dataset's metadata
    :param dataset: The dataset of interest
    :return: None
    """
    cols = dataset.RasterXSize
    rows = dataset.RasterYSize
    bands = dataset.RasterCount

    print(F"cols: {cols} rows: {rows} bands: {bands}")

    info = gdal.Info(dataset)
    print(info)

if __name__ == '__main__':

    dataset = openRaster()
    legend = openLegend()

    printInfo(dataset)

    band = dataset.GetRasterBand(1)

    x_offset, y_offset = computeOffset(dataset, 5000, 5000)

    data = band.ReadAsArray(75000, 75000, 1, 1)

    print(f"Fuel type at (75000, 75000) = {data[0, 0]}")
