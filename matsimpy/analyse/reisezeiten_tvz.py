import pandas as pd
import geopandas as gpd
from shapely.geometry import Point



sc_path = r"C:\Users\til43\IdeaProjects\matsim-berlin\output\200\scenario-berlin-v6.4-3pct-200\berlin-v6.4.output_trips.csv.gz"
df_sc = pd.read_csv(sc_path, sep=";")

sq_path = r"C:\Users\til43\IdeaProjects\matsim-berlin\output\200\status-quo_berlin-v6.4-3pct-200\berlin-v6.4.output_trips.csv.gz"
df_sq = pd.read_csv(sq_path, sep=";")

# start_x;start_y

shp_file_path = "../tvz/Verkehrszellen_Berlin2023.SHP"
shp_file = gpd.read_file(shp_file_path)
print(shp_file.head())


def get_vz_nr_start_end(df_i, shp_file):
    # Convert start points to GeoDataFrame
    gdf_start = gpd.GeoDataFrame(
        df_i,
        geometry=gpd.points_from_xy(df_i.start_x, df_i.start_y),
        crs="EPSG:25832"  # ETRS89 / UTM zone 32N
    )
    gdf_start = gdf_start.to_crs(shp_file.crs)

    # Spatial join for start points
    joined_start = gpd.sjoin(gdf_start, shp_file[["VZ_NR", "geometry"]], how="left", predicate="within")
    df_i["VZ_NR_start"] = joined_start["VZ_NR"]

    # Convert end points to GeoDataFrame
    gdf_end = gpd.GeoDataFrame(
        df_i,
        geometry=gpd.points_from_xy(df_i.end_x, df_i.end_y),
        crs="EPSG:25832"
    )
    gdf_end = gdf_end.to_crs(shp_file.crs)

    # Spatial join for end points
    joined_end = gpd.sjoin(gdf_end, shp_file[["VZ_NR", "geometry"]], how="left", predicate="within")
    df_i["VZ_NR_end"] = joined_end["VZ_NR"]

    return df_i[(pd.notna(df_i["VZ_NR_end"])) & (pd.notna(df_i["VZ_NR_start"]))]


df_sc = get_vz_nr_start_end(df_sc, shp_file)
df_sq = get_vz_nr_start_end(df_sq, shp_file)

print(df_sc.head())
print(df_sc.head())

# 1. Filter by main_mode
df_filtered = df_sc[df_sc['main_mode'] == 'pt'].copy()

# 2. Convert trav_time (hh:mm:ss) to minutes
df_filtered['trav_time_minutes'] = pd.to_timedelta(df_filtered['trav_time']).dt.total_seconds() / 60

# 3. Group by VZ_NR_start and VZ_NR_end and calculate the average trav_time
df_grouped = (
    df_filtered
    .groupby(['VZ_NR_start', 'VZ_NR_end'], as_index=False)
    .agg({'trav_time_minutes': 'mean'})
)

# Optional: round minutes to 2 decimals
df_grouped['trav_time_minutes'] = df_grouped['trav_time_minutes'].round(2)
sc_trav_time = df_grouped.copy()

print(sc_trav_time.to_csv("travel_time_taz_sc.csv"))

# status quo
# 1. Filter by main_mode
df_filtered = df_sq[df_sq['main_mode'] == 'pt'].copy()

# 2. Convert trav_time (hh:mm:ss) to minutes
df_filtered['trav_time_minutes'] = pd.to_timedelta(df_filtered['trav_time']).dt.total_seconds() / 60

# 3. Group by VZ_NR_start and VZ_NR_end and calculate the average trav_time
df_grouped = (
    df_filtered
    .groupby(['VZ_NR_start', 'VZ_NR_end'], as_index=False)
    .agg({'trav_time_minutes': 'mean'})
)

# Optional: round minutes to 2 decimals
df_grouped['trav_time_minutes'] = df_grouped['trav_time_minutes'].round(2)
sq_trav_time = df_grouped.copy()

print(sq_trav_time.to_csv("travel_time_taz_sq.csv"))


df_merged = sc_trav_time.merge(sq_trav_time, on=['VZ_NR_start', 'VZ_NR_end'], suffixes=('_df1', '_df2'))

# Subtract trav_time_minutes
df_merged['trav_time_diff'] = df_merged['trav_time_minutes_df1'] - df_merged['trav_time_minutes_df2']

print(df_merged[['VZ_NR_start', 'VZ_NR_end', 'trav_time_diff']])

df_merged.to_csv("merged_trav_time_taz.csv")



