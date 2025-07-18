# 🌧️ Real-Time Precipitation Interpolation and Mapping Platform

This repository hosts a **real-time open-source geospatial framework** for acquiring and interpolating precipitation data from meteorological stations and visualizing it dynamically in a WebGIS environment. The system is designed as a scientific and operational tool to support hydrogeological risk monitoring using Python, PostgreSQL/PostGIS, and open geospatial APIs.

🔬 **Developed for**: *A framework for dynamic mapping of precipitations using open-source 3D-WebGIS technology*

## 📌 Overview

This platform performs:
1. **Real-time acquisition** of pluviometric data from ItaliaMeteo stations (via [Meteohub API](https://meteohub.mistralportal.it/)).
2. **Storage** of point data in a PostGIS-enabled PostgreSQL database.
3. **Dynamic raster interpolation** using Inverse Distance Weighting (IDW) via Python and SciPy.
4. **Raster output generation** for use in GIS or publishing via WMS (e.g., MapServer, GeoServer).
5. **Optional real-time 3D WebGIS visualization** using CesiumJS and WMS layers.

## 🗂 Repository Structure

```
├── dynamic_precipitation_data_acquisition.py     # Script for real-time acquisition and DB insertion
├── dynamic_interpolation_raster_generation.py    # Script for raster interpolation and DB insertion
├── reference_4326.tif                             # (User-provided) reference raster used as interpolation grid
├── README.md                                      # Project documentation
```

## ⚙️ Requirements

### 🐍 Python Libraries

Install with:
```bash
pip install pandas numpy scipy psycopg2-binary requests rasterio matplotlib scikit-learn
```

### 🐘 PostgreSQL/PostGIS
- PostgreSQL 14+ with PostGIS enabled
- Table: `weather_observations` (see below for schema)

### 🗺️ Raster tools
- `raster2pgsql` and `psql` (included in PostGIS bundle) for raster import

## 🛠️ Setup

### 1. Database Setup

Create the required table in PostGIS:
```sql
CREATE TABLE weather_observations (
    station_id TEXT,
    value DOUBLE PRECISION,
    observed_at TIMESTAMP,
    geom GEOMETRY(Point, 4326),
    PRIMARY KEY (station_id, observed_at)
);
```

You may also need to run:
```sql
CREATE INDEX weather_geom_idx ON weather_observations USING GIST (geom);
```

### 2. Reference Raster

Place a reference GeoTIFF named `reference_4326.tif` in the project root, using EPSG:4326. This raster defines the spatial resolution and extent of the interpolation grid.

## 🚀 How to Run

### Step 1: Real-Time Data Acquisition

Run the script to fetch the latest hour of rainfall data and insert valid stations into the database:
```bash
python dynamic_precipitation_data_acquisition.py
```

> ✅ Ensures completeness: only runs DB insert if all critical stations are present.

### Step 2: Interpolation and Raster Generation

Run the interpolation script to:
- Fetch latest simultaneous timestamp with ≥7 stations
- Perform IDW interpolation
- Normalize and smooth raster
- Store final output as `interpolated.tif`
- Insert the raster into PostGIS via `raster2pgsql`

```bash
python dynamic_interpolation_raster_generation.py
```

## 📊 Interpolation Details

- **Method**: Inverse Distance Weighting (IDW)
- **Parameters**:
  - `power=2`: Exponent controlling spatial decay
  - `k=4`: Number of nearest neighbors
- **Post-Processing**: Gaussian smoothing and min-max normalization

## 🌍 Integration in WebGIS

For 3D visualization, the raster can be served via:

- **GeoServer** for static rasters
- **MapServer** for real-time PostGIS raster layers

And visualized in **CesiumJS** through WMS links.

## 🛰️ Data Source

- **Weather API**: [MeteoHub](https://meteohub.mistralportal.it/api/observations)
- **Monitored Stations**: 
  - `'scl016'`, `'Palermo SIAS'`, `'scl069'`, `'scl088'`, `'scl148'`, `'scl421'`, `'scl040'`, `'scl396'`



## 📝 License

This project is licensed under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license.
