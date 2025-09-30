import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import os

input_folder = r"G:\matsim-output\400-10pct"

sc_path = r"\scenario-berlin-v6.4-10pct-400\berlin-v6.4.output_trips.csv.gz"
df_sc = pd.read_csv(input_folder+sc_path, sep=";")

sq_path = r"\status-quo_berlin-v6.4-10pct-400\berlin-v6.4.output_trips.csv.gz"
df_sq = pd.read_csv(input_folder+sq_path, sep=";")

# start_x;start_y
shp_file_path = "../tvz/raster_1.5.SHP"

# shp_file_path = "../tvz/Verkehrszellen_Berlin2023.SHP"

shp_file = gpd.read_file(shp_file_path)
shp_file = shp_file.rename(columns={"id": "VZ_NR"})
print(shp_file.head())

def get_vz_nr(df_i, shp_file):
    # convert df to GeoDataFrame
    gdf_points = gpd.GeoDataFrame(
        df_i,
        geometry=gpd.points_from_xy(df_i.start_x, df_i.start_y),
        crs="EPSG:25832"   # ETRS89 / UTM zone 32N
    )

    # Reproject POINTS to match shapefile (EPSG:25833)
    gdf_points = gdf_points.to_crs(shp_file.crs)

    print(gdf_points.crs)
    print(shp_file.crs)

    # --- 3. Ensure both layers are in the same CRS ---
    if shp_file.crs != gdf_points.crs:
        shp_file = shp_file.to_crs(gdf_points.crs)

    # --- 4. Spatial join (assign vz_nr to each point) ---
    joined = gpd.sjoin(gdf_points, shp_file[["VZ_NR", "geometry"]], how="left", predicate="within")

    # --- 5. Result ---
    df_with_vz = pd.DataFrame(joined.drop(columns="geometry"))

    return df_with_vz[pd.notna(df_with_vz["VZ_NR"])]


df_sc = get_vz_nr(df_sc, shp_file)
df_sq = get_vz_nr(df_sq, shp_file)

modes = ["bike", "car", "freight", "pt", "ride", "truck", "walk"]


def modal_split(df):
    # group by VZ_NR + mode
    grouped = df.groupby(["VZ_NR", "main_mode"]).size().reset_index(name="count")

    # pivot to wide format
    pivoted = grouped.pivot(index="VZ_NR", columns="main_mode", values="count").fillna(0)

    # make sure all modes exist as columns
    for m in modes:
        if m not in pivoted.columns:
            pivoted[m] = 0

    # compute row sums
    row_sum = pivoted.sum(axis=1)

    # divide each column by row sum -> percentage
    pivoted = pivoted.div(row_sum, axis=0) * 100

    # keep VZ_NR as column instead of index
    pivoted = pivoted.reset_index()

    return pivoted[modes + ["VZ_NR"]]  # reorder cols: all modes + VZ_NR


# Apply to both datasets
sc_split = modal_split(df_sc)
sq_split = modal_split(df_sq)

print(sc_split.to_csv("../tvz/sc_tvz.csv"))
print(sq_split.to_csv("../tvz/sq_tvz.csv"))

# Merge shp_file with sc_split
output_shp = pd.merge(shp_file, sc_split, on="VZ_NR", how="left")
output_shp = output_shp.rename(columns={"pt": "pt_sc"})

# Merge again with sq_split (keeping the previous merge)
output_shp = pd.merge(output_shp, sq_split, on="VZ_NR", how="left")
output_shp = output_shp.rename(columns={"pt": "pt_sq"})

# Compute difference
output_shp["pt_diff"] = output_shp["pt_sc"] - output_shp["pt_sq"]

# Convert to GeoDataFrame
gdf = gpd.GeoDataFrame(output_shp, geometry='geometry', crs="EPSG:25833")

# Save to shapefile
gdf.to_file("../tvz/output_raster_15.shp", driver="ESRI Shapefile")



