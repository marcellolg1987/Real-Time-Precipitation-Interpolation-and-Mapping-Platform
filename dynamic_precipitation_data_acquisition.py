import requests
import psycopg2
from datetime import datetime, timedelta

# --- Calculate Current UTC Hourly Time Window ---
now_utc = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
start_time = now_utc.strftime('%Y-%m-%d %H:00')
end_time = (now_utc + timedelta(hours=1)).strftime('%Y-%m-%d %H:00')

print(f"Fetching data from: {start_time} to {end_time}")

# --- API Request ---
url = "https://meteohub.mistralportal.it/api/observations"
params = {
    "q": f"reftime: >={start_time},<{end_time};product:B12101;license:CCBY_COMPLIANT;timerange:254,0,0;level:103,2000,0,0",
    "reliabilityCheck": "true",
    "last": "true"
}
response = requests.get(url, params=params)
response.raise_for_status()
data = response.json()

STATIONS_TO_KEEP = ['scl016', 'Palermo SIAS', 'scl069', 'scl088', 'scl148', 'scl421', 'scl040', 'scl396']
station_data = {}

# Extract station data and group by ID
for item in data.get('data', []):
    try:
        station_id = item['stat']['details'][0]['val']
        if station_id in STATIONS_TO_KEEP:
            lat = item['stat']['lat']
            lon = item['stat']['lon']
            value = float(item['prod'][0]['val'][0]['val'])
            observed_at = item['prod'][0]['val'][0]['ref']
            station_data[station_id] = (value, lat, lon, observed_at)
    except Exception as e:
        print(f"Skipping record due to error: {e}")

# Check completeness
missing = set(STATIONS_TO_KEEP) - set(station_data.keys())
if missing:
    print(f"?? Incomplete acquisition. Missing stations: {missing}")
    print("?? Skipping database insertion.")
else:
    print("? All required stations present. Writing to database...")

    conn = psycopg2.connect("dbname=postgis_35_sample user=postgres password=password host=localhost")
    cur = conn.cursor()

    # Enforce column type (only once)
    cur.execute("""
        ALTER TABLE weather_observations 
        ALTER COLUMN value TYPE DOUBLE PRECISION 
        USING value::DOUBLE PRECISION;
    """)

    inserted = 0
    for station_id, (value, lat, lon, observed_at) in station_data.items():
        cur.execute("""
            INSERT INTO weather_observations (station_id, value, observed_at, geom)
            VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            ON CONFLICT DO NOTHING
        """, (station_id, value, observed_at, lon, lat))
        inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"? {inserted} records inserted.")

