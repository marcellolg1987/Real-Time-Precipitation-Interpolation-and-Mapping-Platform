
import requests
import psycopg2
from datetime import datetime, timedelta
import pytz
import pandas as pd
import numpy as np
import rasterio
from rasterio.transform import xy
from scipy.spatial import cKDTree
from sklearn.preprocessing import MinMaxScaler
from scipy.ndimage import gaussian_filter
from pyproj import Transformer
import matplotlib.pyplot as plt
import subprocess
import os

# === CONFIGURATION ===
DB_NAME = "postgis_35_sample"
DB_USER = "postgres"
DB_PASSWORD = "password"
DB_HOST = "localhost"
DB_PORT = "5432"
TABLE_NAME = "weather_observations"
RASTER_REF = "reference_4326.tif"
RASTER_OUT = "interpolated.tif"
RASTER2PGSQL_PATH = r"C:\Program Files\PostgreSQL\17\bin\raster2pgsql.exe"
PSQL_PATH = r"C:\Program Files\PostgreSQL\17\bin\psql.exe"
STATIONS_TO_KEEP = ['scl016', 'Palermo SIAS', 'scl069', 'scl088', 'scl148', 'scl421', 'scl040', 'scl396']

# === STEP 1: Fetch Latest Meteo Data from API ===
now_utc = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
start_time = now_utc.strftime('%Y-%m-%d %H:00')
end_time = (now_utc + timedelta(hours=1)).strftime('%Y-%m-%d %H:00')

url = "https://meteohub.mistralportal.it/api/observations"
params = {
    "q": f"reftime: >={start_time},<{end_time};product:B12101;license:CCBY_COMPLIANT;timerange:254,0,0;level:103,2000,0,0",
    "reliabilityCheck": "true",
    "last": "true"
}
response = requests.get(url, params=params)
response.raise_for_status()
data = response.json()

print("Station IDs available in this request:")
for item in data.get('data', []):
    try:
        station_id = item['stat']['details'][0]['val']
        print(station_id)
    except:
        continue


conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
cur = conn.cursor()

station_list = tuple(STATIONS_TO_KEEP)
cur.execute(f"""
    SELECT observed_at
    FROM weather_observations
    WHERE station_id IN %s
    GROUP BY observed_at
    HAVING COUNT(DISTINCT station_id) >= 7
    ORDER BY observed_at DESC
    LIMIT 1;
""", (station_list,))
result = cur.fetchone()
if result is None:
    raise ValueError("No timestamp found with at least 7 required stations.")
latest_timestamp = result[0]
print(f"Using data from: {latest_timestamp}")

query = "SELECT ST_X(geom) AS x, ST_Y(geom) AS y, value FROM weather_observations WHERE observed_at = %s;"
points_df = pd.read_sql(query, conn, params=(latest_timestamp,))
conn.close()

# === Load reference raster ===
with rasterio.open(RASTER_REF) as src:
    transform = src.transform
    width, height = src.width, src.height
    profile = src.profile
    bounds = src.bounds

    rows, cols = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')
    xs, ys = rasterio.transform.xy(transform, rows, cols)
    pixel_coords = np.column_stack((np.array(xs).flatten(), np.array(ys).flatten()))



# === Interpolation ===
def inverse_distance_weighting(coords, values, query_coords, power=2, k=4):
    k = min(k, len(coords))
    tree = cKDTree(coords)
    dists, idxs = tree.query(query_coords, k=k)
    if k == 1:
        dists = dists[:, np.newaxis]
        idxs = idxs[:, np.newaxis]
    weights = 1 / (dists ** power + 1e-12)
    weights /= weights.sum(axis=1, keepdims=True)
    return np.sum(values[idxs] * weights, axis=1)

known_coords = points_df[['x', 'y']].values
known_values = points_df['value'].values
interp_values = inverse_distance_weighting(known_coords, known_values, pixel_coords)
scaler = MinMaxScaler()
normalized = scaler.fit_transform(interp_values.reshape(-1, 1)).flatten()
final_image = normalized.reshape((height, width))
smoothed = gaussian_filter(final_image, sigma=3)

# === Save interpolated raster ===
profile.update(dtype='float32', count=1)
with rasterio.open(RASTER_OUT, "w", **profile) as dst:
    dst.write(smoothed.reshape((1, height, width)).astype('float32'))

# === Optional: Visualize ===
plt.figure(figsize=(8, 6))
plt.imshow(smoothed, cmap='viridis', extent=(bounds.left, bounds.right, bounds.bottom, bounds.top))
plt.scatter(known_coords[:,0], known_coords[:,1], c='red', label='Stations')
plt.title("IDW + Smoothed Precipitation Map")
plt.colorbar(label="Normalized Precipitation")
plt.legend()
plt.show()

# === STEP 3: Load Raster into PostGIS ===
if "PROJ_LIB" in os.environ:
    del os.environ["PROJ_LIB"]
os.environ["PGPASSWORD"] = DB_PASSWORD

raster2pgsql_cmd = [
    RASTER2PGSQL_PATH,
    "-s", "32633", "-I", "-C", "-M",
    RASTER_OUT,
    "interpolated"
]
psql_cmd = [
    PSQL_PATH,
    "-d", DB_NAME,
    "-U", DB_USER,
    "-h", DB_HOST,
    "-p", DB_PORT
]

print(f"Inserting raster '{RASTER_OUT}' into PostGIS table 'interpolated'...")
raster2pgsql_proc = subprocess.Popen(raster2pgsql_cmd, stdout=subprocess.PIPE)
psql_proc = subprocess.Popen(psql_cmd, stdin=raster2pgsql_proc.stdout)
raster2pgsql_proc.stdout.close()
psql_proc.communicate()
print("✅ Raster imported into PostGIS.")
print(f"Total stations used: {len(points_df)}")
print(points_df)