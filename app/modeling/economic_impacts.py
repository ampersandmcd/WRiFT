import geopandas as gpd
import pickle
import pandas as pd
from app.modeling.cloud_storage import safe_open


class EconomicImpactCalculator:
    def __init__(self, footprint_file="app/data/footprints.pickle"):
        """
        Create an object to calculate economic impacts
        :param footprint_file: The file (.geojson) containing building footprints for the area of interest
        """
        self.footprint_file = footprint_file
        self.buildings = self._read_buildings()
        self.fire_hull = None
        self.damaged = None
        self.destroyed = None

    def _read_buildings(self):
        """
        Collect the geometry from the footprint file
        :return: GeoDataFrame of the building footprint polygons
        """
        buildings = gpd.GeoDataFrame(pickle.loads(safe_open(self.footprint_file)))
        return buildings

    def process_fire(self, fire: pd.DataFrame):
        """
        Take a dataframe of the burned cells (with columns labeled 'x' and 'y'), and determine
        damaged buildings. This is the main input function once the simulation has run.
        :param fire: The dataframe of burned cells. Columns labeled ['x', 'y'] for locations of burned cells
        :return: None
        """
        fire_gdf = gpd.GeoDataFrame(fire, geometry=gpd.points_from_xy(fire.x, fire.y))
        fire_u = fire_gdf.unary_union
        self.fire_hull = fire_u.buffer(0.00015, cap_style=3)
        self.buildings['damaged'] = self.buildings.intersects(self.fire_hull)
        self.buildings['destroyed'] = self.buildings.within(self.fire_hull)
        self.buildings['damaged'] = self.buildings['damaged'] & ~self.buildings['destroyed']
        self._extract_damaged()
        self._extract_destroyed()

    def num_damaged(self):
        """
        Get the number of damaged structures in this simulation
        :return: The number of damaged structures
        """
        return self.damaged.shape[0]

    def _extract_damaged(self):
        """
        Return a subset of the building footprints containing only those damaged
        :return:
        """
        self.damaged = self.buildings.loc[self.buildings['damaged'] == True]

    def num_destroyed(self):
        """
        Get the number of damaged structures in this simulation
        :return: The number of damaged structures
        """
        return self.destroyed.shape[0]

    def _extract_destroyed(self):
        """
        Return a subset of the building footprints containing only those damaged
        :return:
        """
        self.destroyed = self.buildings.loc[self.buildings['destroyed'] == True]

    def get_fire_shape(self):
        """
        Get the shape of the fire after simulation has run
        :return: A shapely geometry representing the boundaries of the fire
        """
        if self.fire_hull.geom_type == 'MultiPolygon':
            return [list(structure.exterior.coords) for structure in self.fire_hull.geoms]
        elif self.fire_hull.geom_type == 'Polygon':
            return [list(self.fire_hull.exterior.coords)]
        else:
            return []


    def get_damaged_structure_shape(self):
        """
        Get the shape of the buildings damaged by the fire
        :return: A single shapely geometry representing a multipolygon including each damaged building
        """
        u = self.damaged.unary_union
        if self.num_damaged() > 1:
            return [list(structure.exterior.coords) for structure in u.geoms]
        if self.num_damaged() == 1:
            return [list(u.exterior.coords)]
        return []

    def get_destroyed_structure_shape(self):
        """
        Get the shape of the buildings damaged by the fire
        :return: A single shapely geometry representing a multipolygon including each damaged building
        """
        u = self.destroyed.unary_union
        if self.num_destroyed() > 1:
            return [list(structure.exterior.coords) for structure in u.geoms]
        if self.num_destroyed() == 1:
            return [list(u.exterior.coords)]
        return []


def eic_example():
    """
    Demonstrate the Economic Impact calculator with dummy fire data.
    """
    dummy_fire = pd.DataFrame([[-122.0054482, 37.22892986], [-122.0054482, 37.22805234], [-122.00457067, 37.22951488],
                               [-122.00515569, 37.22834484], [-122.00574071, 37.22980739], [-122.0054482, 37.22922237],
                               [-122.00515569, 37.22863735], [-122.0054482, 37.22951488], [-122.00515569, 37.22892986],
                               [-122.00515569, 37.22805234], [-122.0054482, 37.22980739], [-122.00486318, 37.22834484],
                               [-122.00515569, 37.22922237], [-122.00457067, 37.22922237], [-122.00486318, 37.22863735],
                               [-122.00515569, 37.22951488], [-122.00486318, 37.22805234], [-122.00574071, 37.22834484],
                               [-122.00486318, 37.22892986], [-122.00515569, 37.22980739], [-122.00603321, 37.22951488],
                               [-122.00457067, 37.22834484], [-122.00574071, 37.22863735], [-122.00603321, 37.22980739],
                               [-122.00486318, 37.22922237], [-122.00457067, 37.22863735], [-122.00486318, 37.22951488],
                               [-122.00574071, 37.22892986], [-122.00457067, 37.22892986], [-122.0054482, 37.22834484],
                               [-122.00574071, 37.22922237], [-122.0054482, 37.22863735]])
    dummy_fire.columns = ['x', 'y']
    footprints = 'SC_buildings.geojson'

    print("Creating EIC object (reading in geojson for SC county structures)...")
    eic = EconomicImpactCalculator(footprints)
    print("... completed. Processing fire ...")
    eic.process_fire(dummy_fire)
    print("... completed. Buildings damaged: ")
    print(eic.num_damaged())


if __name__ == '__main__':
    eic_example()
