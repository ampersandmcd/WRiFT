from abc import abstractmethod
import pandas as pd

import geopy.distance


def _coordDistance(row, lat, long):
    f"""
    Given an associative array containing 'latitude' and 'longitude'
    columns, calculate the distance from the lat and long passed in.
    @param row: the associative array containing 'latitude' and 'longitude' keys
    @param lat: the latitude of the point to calculate distance from
    @param long: the longitude of the point to calculate distance from
    """
    return geopy.distance.distance((lat, long), (row['latitude'], row['longitude'])).mi


class Weather:
    """
    Abstract class for weather queries
    """

    def __init__(self, lat, long):
        self.lat = lat
        self.long = long
        self.data = self.refresh_data()

    @abstractmethod
    def refresh_data(self):
        pass

    @abstractmethod
    def weather_by_station(self, station):
        pass

    def getNearestStation(self):
        f"""
        Find the nearest weather station in this @Link{Weather} to the
        latitude and longitude provided.
        """
        distances = self.data.apply(_coordDistance, axis=1, lat=self.lat, long=self.long)
        return distances.idxmin()


import requests
import pandas as pd
from io import StringIO

from exploration.data.weather import Weather


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


class CurrentWeather(Weather):
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
        super().__init__(lat, long)

    def refresh_data(self):
        f"""
        Pull the most recent data from the ADDS server.
        """
        data_text = self.query()
        return _weatherDataToDF(data_text)

    def query(self) -> str:
        f"""
        Collect current weather data from all stations available within this @Link{CurrentWeather} 
        object's radius.
        """
        distance_string = F"{self.radius};{self.long},{self.lat}"

        query = {"dataSource": "metars", "requestType": "retrieve", "format": "csv",
                 "radialDistance": distance_string, "hoursBeforeNow": "1"}

        data = requests.get(self.BASE_URL, params=query)

        if data.status_code != 200:
            raise ValueError(f"ADDS Server returned status code {data}; check arguments and retry query")

        return data.text

    def most_recent(self):
        f"""
        Get the most recent data available.
        Only returns data for a single station.
        """
        return self.data.iloc[0]

    def weather_by_station(self, station):
        f"""
        Get the most recent data corresponding to the given station.
        @param station: The station to search for
        """
        data = self.data.loc[station]
        if data.size > self.SINGLE_METAR_SIZE:
            return data.iloc[0]
        return data


def example():
    f"""
    Example usage of the @Link{CurrentWeather} class.
    """
    lat, long = 37.3923, -121.5
    distance = 20

    weather = CurrentWeather(20, lat, long)
    weather = weather.weather_by_station(weather.getNearestStation())
    wind_speed, wind_dir = weather['wind_speed_kt'], weather['wind_dir_degrees']
    print(F"wind speed: {wind_speed}, wind direction: {wind_dir}")


if __name__ == '__main__':
    example()
