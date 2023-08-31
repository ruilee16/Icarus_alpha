from rasterio.mask import mask
import numpy as np
from rtree.index import Index
from netCDF4 import Dataset


from Icarus_main.Classes.temperature_class import Point
from Icarus_main.utils.utilities import update_dataclass


def parse_raster_temperature(shapefile, raster_dataset, geometry_name='geometry'):
    """

    :param shapefile:
    :param raster_dataset:
    :param geometry_name:
    :return:
    """
    _result = []
    for index, row in shapefile.iterrows():
        geometry = row[geometry_name]
        # Extract raster values within the geometry using rasterio.mask
        masked_data, masked_transform = mask(raster_dataset, [geometry], crop=True)
        # Calculate statistics (e.g., mean, median, etc.) from the masked data
        _temp_value = masked_data[(masked_data > 0) & (masked_data < 255)]
        if len(_temp_value) > 0:
            _result.append(int(np.mean(_temp_value)*10))
        else:
            _result.append(-999)
        # Print or store the calculated statistics
    return _result


def _load_pt_property(points):
    for point in points:
        yield point.uuid, (point.x, point.y, point.x, point.y), point.uuid


def _get_nc_loc_rt(lons, lats, shape):
    pts = [Point(x=lons[_i][_j], y=lats[_i][_j], x_id=_i, y_id=_j) for _i in range(shape[-2]) for _j in
           range(shape[-1])]
    [update_dataclass(item, uuid=index) for index, item in enumerate(pts)]
    return Index(_load_pt_property(pts)), pts


def parse_air_temp(shapefile, tmax_url, tmin_url, day):
    if shapefile.crs != 4326:
        centroid = shapefile.to_crs(4326).centroid.to_list()
    else:
        centroid = shapefile.centroid.to_list()
    # get daymet data
    tmaxnc = Dataset(tmax_url, 'r')
    tminnc = Dataset(tmin_url, 'r')
    # get nc loc rtree
    _nc_indexes, loc_pts = _get_nc_loc_rt(tmaxnc.variables['lon'], tmaxnc.variables['lat'], tmaxnc.variables['tmax'].shape)
    _shp_nc_ind = [next(_nc_indexes.nearest((_.x, _.y, _.x, _.y), objects=True)).object for _ in centroid]
    _airTemp_max = [int(tmaxnc.variables['tmax'][day][loc_pts[_].x_id][loc_pts[_].y_id]*10) for _ in _shp_nc_ind]
    _airTemp_min = [int(tminnc.variables['tmin'][day][loc_pts[_].x_id][loc_pts[_].y_id]*10) for _ in _shp_nc_ind]
    return {'t_max': _airTemp_max, 't_min': _airTemp_min}

