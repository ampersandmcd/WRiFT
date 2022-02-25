import requests
import urllib
import json
import pandas as pd

from weather import Weather


class HistoricWeather(Weather):
    """
    A class for historic weather data queries
    """
    BASE_URL = "https://www.ncdc.noaa.gov/cdo-web/api/v2/"
    DATA_ID = ""
    DATA_TYPES = ""

    def __init__(self, start_date, end_date, lat, long):
        """
        Initialize a HistoricWeather object
        @param start_date: The start date for weather queries
        @param end_date: The end date for weather queries
        """
        token = open(".ncdc_token").read()
        self.headers = {"token": token}
        self.start_date = start_date
        self.end_date = end_date
        super().__init__(lat, long)

    def refresh_data(self):
        pass

    def query(self, resource, params):
        """
        Query the NCDC web API
        @param resource: The resource to query
        @param params: The parameters to use
        @return:
        """
        endpoint = self.BASE_URL + resource
        response = requests.get(endpoint, headers=self.headers, params=params)
        return response

    def get_stations(self, width):
        """
        Return the available weather stations in an approximately Square search area. This method will perform
        very poorly for areas near Earth's geographic poles, where the search area will become a tall thin rectangle.
        @param width: The width of the search area [degrees]. Note that at the equator, 1 degree ~ 70 mi
        @return: A list of available stations
        """
        extent = f"{self.lat - width/2},{self.long-width/2},{self.lat+width/2},{self.long+width/2}"
        params = {"datasetid": self.DATA_ID, "startdate": self.start_date, "enddate": self.end_date,
                  "extent": extent, "sortfield": "maxdate", "sortorder": "desc", "datatypeid": self.DATA_TYPES}
        response = self.query("stations", params)
        data = json.loads(response.text)
        stations = pd.DataFrame(data["results"])
        stations.set_index("id", inplace=True)
        return stations

    def weather_by_station(self, station):
        """
        Return temperature and wind information from a single station
        @param station: The station to query
        @return: A dataframe containing a row for each variable
        """
        params = {"datasetid": self.DATA_ID, "startdate": self.start_date, "enddate": self.end_date, "limit": 3,
                  "sortfield": "date", "sortorder": "desc", "stationid":station, "datatypeid": self.DATA_TYPES}
        response = self.query("data", params)
        data = json.loads(response.text)
        reports = pd.DataFrame(data["results"])
        reports.drop(["station", "attributes", "date"], axis=1, inplace=True)
        reports.set_index("datatype", inplace=True)
        return reports


class DailyWeather(HistoricWeather):
    DATA_ID = "GHCND"
    DATA_TYPES = "TMAX,WDF2,WSF2"


def example():
    """
    Example usage of the DailyWeather class
    """
    w = DailyWeather("2020-01-01", "2020-01-02", 42.73131121772554, -84.4827754135353)
    stations = w.get_stations(1)
    closest = w.getNearestStation(stations)
    weather = w.weather_by_station(closest)
    print(F"max temperature: {weather['value']['TMAX']/10} C")
    print(F"max windspeed: {weather['value']['WSF2']/10} m/s")
    print(F"wind direction: {weather['value']['WDF2']} degrees CW from N")


if __name__ == '__main__':
    example()
