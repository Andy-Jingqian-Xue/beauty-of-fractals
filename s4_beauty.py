import warnings
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import LineString, Point

warnings.filterwarnings("ignore", category=RuntimeWarning, module='shapely')

input_path = "figures/contour04.shp"
output_path = "figures/bends16.shp"
tolerance = 100


def head_tail_breaks(array, break_per=0.4, version=2):
    ratio_list, cuts = [], [0]
    array_positive = array[array > 0]  # Consider only positive values
    classifications = np.zeros(array.shape)  # Initialize classifications array
    ht_index = 1

    while array_positive.size > 1 and np.mean(array_positive) > 0:
        mean_val = np.mean(array_positive)
        cuts.append(mean_val)
        ht_index += 1
        head = array_positive[array_positive > mean_val]
        ratio = len(head) / len(array_positive)
        ratio_list.append(ratio)
        if version == 1:
            if mean_val > break_per:
                break
        if version == 2:
            if np.mean(ratio_list) > break_per:
                break
        array_positive = head

    # Assign classes based on the cuts
    for i in range(1, len(cuts)):
        indices = np.where((array > cuts[i-1]) & (array <= cuts[i]))
        classifications[indices] = i

    # Handling elements greater than the last cut
    indices = np.where(array > cuts[-1])
    classifications[indices] = len(cuts)

    return ht_index, classifications


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

# Read input file and initialize lists for storing bend information
gdf = gpd.read_file(input_path)
bs, dcs, lengths = [], [], []

# Process each line in the GeoDataFrame to identify bends
for line in gdf.geometry:
    if line.is_valid and line.geom_type == 'LineString':
        bends, ds, ls = identify_bends_from_polyline(line, tolerance)
        bs.extend(bends)
        dcs.extend(ds)
        lengths.extend(ls)

# Create a new GeoDataFrame from the bends
gdf_new = gpd.GeoDataFrame(geometry=bs)
gdf_new['distance'] = dcs
gdf_new['length'] = lengths
gdf_new = gdf_new[gdf_new['length'] > 0]

# Apply the head/tail breaks method to classify bends
ht, classifications = head_tail_breaks(gdf_new['distance'])
gdf_new['class'] = classifications
# gdf_new.to_file(output_path)

# Output basic statistics
print('Number of substructures or bends (S):', len(gdf_new))
print('Degree of hierarchy (H):', ht)
print('Degree of structural beauty (L = S * H):', len(gdf_new) * ht)

# Calculate and display the number of bends in each classification
class_counts = gdf_new['class'].value_counts().sort_index()
for class_num in range(1, ht + 1):
    if class_num not in class_counts:
        class_counts.loc[class_num] = 0
class_counts.sort_index(inplace=True)

# Prepare data for the table
columns = ['S' + str(i) for i in range(1, ht + 1)]
data = class_counts.reindex(range(1, ht + 1), fill_value=0).tolist()
total_s = sum(data)
l_value = total_s * ht

# Create and format the output DataFrame for readability
output_df = pd.DataFrame([data], columns=columns)
output_df['S'] = total_s
output_df['H'] = ht
output_df['L'] = l_value

# Print the formatted table
print("\nStatistics at each level of hierarchy:")
print(output_df.to_string(index=False, formatters={
    'S': '{:d}'.format,
    'H': '{:d}'.format,
    'L': '{:d}'.format
}.update({col: '{:d}'.format for col in columns})))
