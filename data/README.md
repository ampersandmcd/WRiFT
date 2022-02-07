# CapstoneExploration/data

A subdirectory to explore data acquisition for our modeling.
## NetCDF Files
- Check out the documentation for [netCDF4](https://unidata.github.io/netcdf4-python/) or [xarray](https://xarray.pydata.org/en/stable/) to learn about interfacing with netCDF files in python. 
- The [farsite.nc](https://storage.googleapis.com/modeling_data_farsite/farsite.nc) file should contain all static modeling data needed for FARSITE in Santa Clara County.
  - Data is all mapped to the same geospatial grid, with 30x30 m pixels. 
  - Data is organized in 14 bands within the NetCDF, each representing a different variable. Click the links to access a .csv legend for each variable.
    1. US_210CBD: Canopy Bulk Density [(kg/m^3*100)](https://www.landfire.gov/CSV/LF_Limited/LF19_CBD_210.csv)
    2. US_210CBH: Canopy Base Height [(m*10)](https://www.landfire.gov/CSV/LF_Limited/LF19_CBH_210.csv)
    3. US_210CC: Canopy Cover [(tree cover %)](https://www.landfire.gov/CSV/LF_Limited/LF19_CC_210.csv)
    4. US_210CH: Canopy Height [(m*10)](https://www.landfire.gov/CSV/LF_Limited/LF19_CH_210.csv)
    5. US_210EVC: Existing Vegetation Cover [(Qualitative, see legend)](https://www.landfire.gov/CSV/LF_Limited/LF19_EVC_210.csv)
    6. US_210EVH: Existing Vegetation Height [(Qualitative, see legend)](https://www.landfire.gov/CSV/LF_Limited/LF19_EVH_210.csv)
    7. US_210F40: Fuel Type [Qualitative, see legend](https://www.landfire.gov/CSV/LF_Limited/LF19_F40_210.csv)
    8. US_210FVC: Fuel Vegetation Cover [(Qualitative, see legend)](https://www.landfire.gov/CSV/LF_Limited/LF19_FVC_210.csv)
    9. US_210FVH: Fuel Vegetation Height [(Qualitative, see legend)](https://www.landfire.gov/CSV/LF_Limited/LF19_FVH_210.csv)
    10. US_210FVT: Fuel Vegetation Type [(Qualitative, see legend)](https://www.landfire.gov/CSV/LF_Limited/LF19_FVT_210.csv)
    11. US_ASP: Aspect (direction of slope face, in degrees from North)
    12. US_DEM: Elevation (m)
    13. US_FDIST: Fuel Disturbance [(Qualitative, see legend)](https://www.landfire.gov/CSV/LF_Limited/LF19_FDst_210.csv)
    14. US_SLP: Slope (% change in elevation)

## To Do List


## Activity Log

#### 19 January 2022
- Acquired NCDC API key for team use.
- Added simple query to NCDC web API.
