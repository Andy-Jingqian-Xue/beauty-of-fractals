import warnings
from shapely.geometry import LineString, Point
import geopandas as gpd
warnings.filterwarnings("ignore", category=RuntimeWarning, module='shapely')

input_path = "sample_data/contour04.shp"
output_path = "bends04.shp"
tolerance = 5


def find_farthest_point(line, points):
    # Find the farthest point from the line
    max_distance = -1
    index_of_max = None
    for i, (x, y) in enumerate(points):
        point = Point(x, y)
        distance = line.distance(point)
        if distance > max_distance:
            max_distance = distance
            index_of_max = i
    return index_of_max, max_distance


def recursive_bend_identification(points, start, end, tolerance, bends_pair, ds, lengths):
    # Douglas-Peucker algorithm
    if end <= start + 1:
        return

    line = LineString([points[start], points[end]])
    mid_index, distance = find_farthest_point(line, points[start:end+1])
    mid_index += start

    if distance > tolerance:
        if points[start] != points[end]:
            line_pair = LineString(
                [points[start], points[mid_index], points[end]])
            bends_pair.append(line_pair)
            ds.append(distance)
            lengths.append(line_pair.length)

        # Divide into two parts: start to mid_index, and mid_index to end
        recursive_bend_identification(
            points, start, mid_index, tolerance, bends_pair, ds, lengths)
        recursive_bend_identification(
            points, mid_index, end, tolerance, bends_pair, ds, lengths)


def identify_bends_from_polyline(line, tolerance=1.0):
    # Input feature form polygons
    bends_pair, ds, lengths = [], [], []
    points = list(line.coords)
    recursive_bend_identification(points, 0, len(
        points) - 1, tolerance, bends_pair, ds, lengths)
    return bends_pair, ds, lengths


# Read input file
gdf = gpd.read_file(input_path)
bs, dcs, lengths = [], [], []

# Identify bends
for line in gdf.geometry:
    if line.is_valid and line.geom_type == 'LineString':
        bends, ds, ls = identify_bends_from_polyline(line, tolerance)
        bs.extend(bends)
        dcs.extend(ds)
        lengths.extend(ls)

# Create output file
gdf_new = gpd.GeoDataFrame(geometry=bs)
gdf_new['distance'] = dcs
gdf_new['length'] = lengths
gdf_new = gdf_new[gdf_new['length'] > 0]
gdf_new.to_file(output_path)
