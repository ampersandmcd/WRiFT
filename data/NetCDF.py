from netCDF4 import Dataset

def netcdf():
    url = ('https://storage.googleapis.com/modeling_data_farsite/Aspect_SC.nc#mode=bytes')
    link=Dataset(url)
    print(link)

if __name__=='__main__':
    netcdf()