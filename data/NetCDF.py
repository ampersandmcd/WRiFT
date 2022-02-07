from netCDF4 import Dataset

def stream():
    url = ('https://storage.googleapis.com/modeling_data_farsite/Aspect_SC.nc#mode=bytes')
    link=Dataset(url)
    print(link)


def read():
    nc = Dataset("farsite.nc")
    print(nc)


if __name__=='__main__':
    read()