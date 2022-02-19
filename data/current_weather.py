import requests
import pandas as pd
from io import StringIO
import geopy.distance


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
        return self.data.loc[station]


def example():
    f"""
    Example usage of the @Link{CurrentWeather} class.
    """
    lat, long = 37.280346, -121.692092
    distance = 20

    weather = CurrentWeather(distance, lat, long)
    nearest = weather.getNearestStation()
    data = weather.dataByStation(nearest)
    wind_speed, wind_dir = data['wind_speed_kt'], data['wind_dir_degrees']
    print(F"wind speed: {wind_speed}, wind direction: {wind_dir}")


if __name__ == '__main__':
    example()
