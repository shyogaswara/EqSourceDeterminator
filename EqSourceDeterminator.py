#!/usr/bin/env python

'''The code will be used to determine the source of the earthquake by using
Geopandas library. This code is meant to be used with GetParam.py as Module
to create simple report about earthquake event. 

The code written by shyogaswara, for further information please mail me 
at sh.yogaswara@gmail.com

[PYTHON VERSION]
3.10

[LIBRARIES]
geopandas
numpy
shapely

[CHANGELOG 1/2024]
- New Release
'''
import geopandas as gpd
import numpy as np

from shapely.geometry import Point

__author__ = 'Shandy Yogaswara'
__version_info__ = (2024, 1, 'aN (Alpha Release)')
__version__ = ".".join(map(str, __version_info__))

class EqSourceDeterminator:
    '''
    Class used to determine the source of earthquake. the fault based on
    Pusgen and Sieh and Natawidjaja (2006) in form of shp or geoJSON, 
    while also determine if the earthquake is inland or sea.

    [Attributes]
    latitude : float
        latitude of earthquake epicenter
    longitude : float
        longitude of earthquake epicenter
    url_geometry : str, list
        list of shapefile path that contain land geometry and fault
        geometry

    [Methods]
    is_inland
        determine if coordinate point is inside land geometry or not
    distance_to_fault
        determine nearest distance from coordinate point to fault
        geometry
    determine_eq_source
        conclude the earthquake source based on is_inland, 
        distance_to_fault, and earthquake parameters
    
    '''
    def __init__(self,latitude,longitude,depth,*url_geometry):
        '''
        [Arguments]
        latitude : float
            latitude of earthquake epicenter
        longitude : float
            longitude of earthquake epicenter
        depth : float
            earthquake depth in Km
        url_geometry : str, list
            list of shapefile path that contain land geometry and fault
            geometry as arguments sequentially
        '''
        self.latitude, self.longitude, self.depth = latitude, longitude, depth
        self.url_geometry = url_geometry

    def is_inland(self,latitude=None,longitude=None,url_geometry=None):
        '''
        determine if coordinate point is inside land geometry or not.

        [Arguments]
        latitude : float
            latitude of earthquake epicenter, default use initial
            arguments
        longitude : float
            longitude of earthquake epicenter default use initial
            arguments
        url_geometry : str
            land geometry shapefile path, default use the 1st initial
            arguments

        [Variables]
        latitude : float
            latitude of earthquake epicenter, default use initial
            arguments
        longitude : float
            longitude of earthquake epicenter default use initial
            arguments
        url_geometry : str
            land geometry shapefile path, default use the 1st initial
            arguments
        land_geometry : object
            shapefile from url_geometry object that geopandas read
        eq_point : object
            earthquake coordinate as point geometry
        is_inland : bool
            boolean value corresponding to earthquake location in land
            or not

        [Raises]
        ValueError
            if either latitude or longitude value is not float
        FileNotFoundError
            if land geometry shapefile is not found
        '''
        if url_geometry is None and self.url_geometry[0] is None:
            raise FileNotFoundError('shapefile is not found')

        if latitude is None and self.latitude is None:
            raise ValueError('latitude value is not found, please input value from -90 to 90')

        if longitude is None and self.longitude is None:
            raise ValueError('longitude value is not found, please input value from -180 to 180')

        url_geometry = self.url_geometry[0] if url_geometry is None else url_geometry
        latitude = self.latitude if latitude is None else latitude
        longitude = self.longitude if longitude is None else longitude
        
        land_geometry = gpd.read_file(url_geometry)

        eq_point = Point(longitude, latitude)

        self.is_inland = land_geometry.contains(eq_point).any()

    def distance_to_fault(self,latitude=None,longitude=None,url_geometry=None):
        '''
        determine the nearest segment point from shp to a point.

        [Arguments]
        latitude : float
            latitude of earthquake epicenter, default use initial
            arguments
        longitude : float
            longitude of earthquake epicenter default use initial
            arguments
        url_geometry : str
            fault geometry shapefile path, default use the 2nd initial
            arguments

        [Variables]
        latitude : float
            latitude of earthquake epicenter, default use initial
            arguments
        longitude : float
            longitude of earthquake epicenter default use initial
            arguments
        url_geometry : str
            fault geometry shapefile path, default use the 2nd initial
            arguments
        fault_geometry : object
            shapefile from url_geometry object that geopandas read
        eq_point : object
            earthquake coordinate as point geometry
        distance_to_fault : dataframe
            altered fault_geometry dataframe by adding distance between
            eq_point and each elements of fault_geometry in Km.
        nearest_to_fault : dataframe
            distance_to_fault row where the Distance have the minimum
            value, consist of Id, Segment,type, maximum magnitude, slip 
            rate, and distance to epicenter in Km

        [Raises]
        ValueError
            if either latitude or longitude value is not found
        FileNotFoundError
            if fault geometry shapefile is not found
        TypeError
            if latitude or longitude value is not float
        '''
        if url_geometry is None and self.url_geometry[1] is None:
            raise FileNotFoundError('shapefile is not found')

        if latitude is None and self.latitude is None:
            raise ValueError('latitude value is not found, please input value from -90 to 90')

        if longitude is None and self.longitude is None:
            raise ValueError('longitude value is not found, please input value from -180 to 180')

        url_geometry = self.url_geometry[1] if url_geometry is None else url_geometry

        latitude = self.latitude if latitude is None else latitude
        if not isinstance(latitude, float):
            raise TypeError(f'{latitude} type is not float, but {type(latitude)} instead')

        longitude = self.longitude if longitude is None else longitude
        if not isinstance(longitude, float):
            raise TypeError(f'{longitude} type is not float, but {type(longitude)} instead')
        
        fault_geometry = gpd.read_file(url_geometry).to_crs('EPSG:4326')

        eq_point = Point(longitude, latitude)

        fault_geometry['Distance']  = [111.18 * eq_point.distance(line) for line in fault_geometry.geometry]
        self.distance_to_fault = fault_geometry.drop(['Id','Name','LCLASSSTR','geometry'],axis=1)
        self.nearest_segment = self.distance_to_fault.loc[self.distance_to_fault['Distance'] == self.distance_to_fault['Distance'].min()]

    def determine_eq_source(self,is_inland=None,nearest_segment=None,depth=None):
        '''
        determine earthquake source based on the location of epicenter.
        the conditions are :
        1. if is_inland = True and depth < 50, it's considered as 
        fault activity, where the name came from nearest_segment or
        if the distance from nearest_segment is > 15, it will be 
        called 'Sesar Lokal' or 'Local Fault'
        2. if is_inland = False and depth < 50, it is considered as 
        fault activity just like the 1st condition, but it wont account
        for the distance value, as long as the is_inland = 'laut'
        3. if the depth > 50, it will be regarded as Subduction activity

        [Arguments]
        is_inland : bool
            epicenter position, where True = epicenter is in land
        nearest_segment : dataframe object
            nearest segment based on distance_to_fault method, consisted
            of segment name, type, maximum magnitude, slip rate, and
            distance to epicenter in Km
        depth : float
            earthquake depth

        [Raises]
        ValueError
            if no segment data or depth is found
        TypeError
            if the type of data doesnt match with requirements
        '''
        
        if is_inland is None and self.is_inland is None:
            raise ValueError('Cant determine if earthquake is in land or not')
        if nearest_segment is None and self.nearest_segment is None:
            raise ValueError('No segment found, please check the fault shapefile and re run from beginning')
        if depth is None and self.depth is None:
            raise ValueError('Missing earthquake parameter : Depth')

        nearest_segment = self.nearest_segment if nearest_segment is None else nearest_segment

        depth = self.depth if depth is None else depth
        if isinstance(depth,int) or isinstance(depth,float):
            '''if depth variable type is int or float, check depth value. if its
            more than 50, set segment_name as subduction zone, else set as None
            '''
            if depth > 50:
                self.segment_name = 'zona subduksi'
            else:
                self.segment_name = None
        else:
            raise TypeError(f'depth type error, should be int, but instead {type(depth)}')

        is_inland = self.is_inland if is_inland is None else is_inland
        if isinstance(is_inland, bool) or isinstance(is_inland, np.bool_):
            '''if is_inland is boolean or numpy boolean, check is_inland value.
            if True, set is_inland as land and check segment_name. if None,
            check nearest_segment.Distance value. if its less than 16, set
            nearest_segment.Segment values as segment_name, if not, set as Local
            Fault instead. if is_inland is false, set is_inland as sea and
            check segment_name. if None, set nearest_segment.Segment values as
            segment_name. take caution if segment_name somehow is a fault segment
            at land, user comprehensive understanding about geology settings
            is needed.
            '''
            if is_inland:
                self.is_inland = 'darat'
                if self.segment_name is None:
                    if nearest_segment.Distance.values < 16:
                        self.segment_name = nearest_segment.Segment.values[0]
                    else:
                        self.segment_name = 'Sesar Lokal'
            elif not is_inland:
                self.is_inland = 'laut'
                if self.segment_name is None:
                    self.segment_name = nearest_segment.Segment.values[0]
        else:
            raise TypeError(f'is_inland type error, should be boolean, but instead {type(is_inland)}')


if __name__ == '__main__':
    land_geometry = r"D:\ProjectPy\AutoNarasi\flaskr_\static\shapefile\land_geometry\indo_provinces.shp"
    land_geometry2 = r"D:\ProjectPy\AutoNarasi\flaskr_\static\shapefile\land_geometry\Indo_provgeojson"
    fault_geometry = r"D:\ProjectPy\AutoNarasi\flaskr_\static\shapefile\fault_geometry\IndonesiaFaults_PuSGeN2017\2016_SUM_FaultModel_v1_2.shp"
    fault_geometry2 = r"D:\ProjectPy\AutoNarasi\flaskr_\static\shapefile\fault_geometry\IndonesiaFaultModels_Pusgen2016.geojson"
    
    latitude = -3.57
    longitude = 100.56
    depth = 30
    mag = 2.9

    EqSource = EqSourceDeterminator(latitude, longitude, depth, land_geometry, fault_geometry2)
    EqSource.is_inland()
    EqSource.distance_to_fault()
    EqSource.determine_eq_source()
    print(f'gempa terletak di {EqSource.is_inland} dengan segmen patahan di {EqSource.segment_name}')
    
