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
