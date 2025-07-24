# 🌧️ Real-Time Precipitation Interpolation and Mapping Platform

This repository hosts a **real-time open-source geospatial framework** for acquiring and interpolating precipitation data from meteorological stations and visualizing it dynamically in a 3D WebGIS environment. The system supports hydrogeological risk monitoring using Python, PostgreSQL/PostGIS, CesiumJS, and open geospatial services.

🔬 **Developed for**: *A framework for dynamic mapping of precipitations using open-source 3D-WebGIS technology*

---

## 📌 Overview

This platform performs:
1. **Real-time acquisition** of rainfall data from ItaliaMeteo stations.
2. **Storage** in a PostGIS-enabled PostgreSQL database.
3. **Raster interpolation** using Inverse Distance Weighting (IDW).
4. **Raster output generation** and database import.
5. **WebGIS visualization** of interpolated layers using CesiumJS + MapServer WMS.

---

## 🗂 Repository Contents

```
├── dynamic_precipitation_data_acquisition.py     # Real-time acquisition and DB insertion
├── dynamic_interpolation_raster_generation.py    # IDW interpolation, smoothing, raster generation
├── interpolation.map                             # MapServer config file for WMS exposure
├── index.html                                     # WebGIS viewer with CesiumJS
├── reference_4326.tif                             # Grid template raster (user-provided)
├── README_precipitation_platform.txt              # This documentation
```

---

## ⚙️ Requirements

### 🐍 Python
Install libraries:
```bash
pip install pandas numpy scipy psycopg2-binary requests rasterio matplotlib scikit-learn
```

### 🐘 PostgreSQL/PostGIS
- PostgreSQL 14+ with PostGIS extension
- Table schema:
```sql
CREATE TABLE weather_observations (
    station_id TEXT,
    value DOUBLE PRECISION,
    observed_at TIMESTAMP,
    geom GEOMETRY(Point, 4326),
    PRIMARY KEY (station_id, observed_at)
);
```

### 🗺️ Raster Tools
- `raster2pgsql` and `psql` (PostGIS bundle)
- MapServer (e.g., MS4W)
- CesiumJS (v1.89 or later)

---

## 🚀 Workflow

### 1. Acquire Precipitation Data

```bash
python dynamic_precipitation_data_acquisition.py
```

> ✅ Only inserts if all required stations are found.

### 2. Interpolate and Generate Raster

```bash
python dynamic_interpolation_raster_generation.py
```

- Fetches most recent `observed_at` timestamp with ≥7 stations.
- Interpolates via IDW (`power=2`, `k=4`)
- Normalizes and smooths with Gaussian filter
- Saves and imports raster into PostGIS (`interpolated` table)

---

## 🌍 WebGIS Visualization

### A. MapServer Setup

`interpolation.map` configures WMS exposure of the `interpolated` raster:
- Reads from PostGIS using:
  ```plaintext
  CONNECTIONTYPE POSTGIS
  DATA "PG:host=localhost port=5432 ... table=interpolated column=rast mode=2"
  ```
- Colorized with a defined `COLORMAP`
- Accessible at:
  ```
  http://localhost:8083/cgi-bin/mapserv.exe?map=/ms4w/apps/susceptibility/interpolation.map&service=WMS&version=1.1.1&request=GetCapabilities
  ```

### B. CesiumJS WebGIS

Open `index.html` to launch the 3D viewer (host via Apache or localhost):

- Loads WMS via `Cesium.WebMapServiceImageryProvider`
- Zooms to Palermo (Italy)
- Selects `interpolated` raster layer from MapServer

```html
layers: 'interpolated',
url: 'http://localhost:8083/cgi-bin/mapserv.exe?...'
```

---

## 🛰️ Data Source

- **API**: [MeteoHub](https://meteohub.mistralportal.it/)
- **Stations**: `'scl016'`, `'Palermo SIAS'`, `'scl069'`, `'scl088'`, `'scl148'`, `'scl421'`, `'scl040'`, `'scl396'`



---

## 📝 License

Licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)

