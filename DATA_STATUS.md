# Data & Runnability Status

Living checklist of what is wired, what data is still missing, and which notebook sections can
run. Update the checkboxes as data arrives. Last checked: 2026-07-28.

Legend: ✅ ready · ⛔ blocked (data or code) · ⚠️ runs, but verify something on first run.

---

## 1. Section runnability

| Section | State | Blocked by |
|---|---|---|
| 1.1 Ecosystem Type | ✅ | — (derived from pathway band 2) |
| 1.2 Administrative Boundaries | ⛔ | GADM data (`GADM_L0/L1/L2`) |
| 1.3 Protected Areas (WDPA) | ✅ | — (fields verified, uses `REALM`) |
| 1.4 Terrain | ✅ | — (slope derived from elevation DEM) |
| 1.5 Historical Deforestation | ✅ | — |
| 1.6 Deforestation Risk | ⛔ | national risk CSV + stub `load_national_forest_risk_percentiles` + country from 1.2 |
| 1.7 Natural Disaster Hazard | ⛔ | 5 hazard rasters |
| 2.1 Forest Landscape Integrity | ⚠️ | verify class raster carries 1/2/3 |
| 2.2 Key Biodiversity Areas | ⛔ | KBA data (`KBA_POLYGON`) |
| 3.1 Current Carbon Storage | ✅ | — (AGB wired, BGB derived) |
| 3.2 Soil Organic Carbon | ⛔ | SOC raster (`SOIL_CARBON_RASTER`) |
| 3.3 Annual Temperature | ⛔ | 12 WorldClim tavg rasters |
| 3.4 Annual Precipitation | ⛔ | 12 WorldClim prec rasters |
| 3.5 Fire Susceptibility | ⛔ | fire hazard raster (same file as 1.7 fire) |
| 3.6 Soil Classification | ⛔ | soil raster + lookup table + stub `load_soil_class_table` |
| 4.1 Pathway Distribution | ⚠️ | verify `prob.tif`/pathway values; runs |
| 4.2 Activity List | ✅ | — |
| 5.x Benefit | — | built in another session, not audited here |

Runnable now: **1.1, 1.3, 1.4, 1.5, 2.1, 3.1, 4.1, 4.2**.

---

## 2. Data still missing (config `<SET>`)

- [ ] **GADM boundaries** — `GADM_L0`, `GADM_L1`, `GADM_L2` (1.2). Verify field names
      `GADM_COUNTRY_FIELD` / `NAME_1` / `NAME_2` against the file.
- [ ] **National forest risk reference** — `NATIONAL_FOREST_RISK_CSV` (1.6). Per-country
      percentile breakpoints of `prob.tif`.
- [ ] **Hazard rasters ×5** — `HAZARD_RASTERS`: landslide, flood, flashflood, fire, drought
      (1.7). The `fire` file is also reused by 3.5.
- [ ] **Key Biodiversity Areas** — `KBA_POLYGON` (2.2).
- [ ] **Soil organic carbon** — `SOIL_CARBON_RASTER`, tC/ha (3.2).
- [ ] **Soil classification** — `SOIL_CLASS_RASTER` + `SOIL_CLASS_TABLE` (3.6).
- [ ] **WorldClim ×24** — `WORLDCLIM_TAVG_RASTERS` (12) + `WORLDCLIM_PREC_RASTERS` (12),
      v2.1 30s (3.3, 3.4).

---

## 3. Code stubs (`common.py`)

- [x] `load_raster_clipped` — implemented (rasterio)
- [x] `load_vector_intersecting` — implemented (geopandas)
- [x] `load_activity_table` — implemented (pandas)
- [ ] `load_soil_class_table` — needed for 3.6
- [ ] `load_national_forest_risk_percentiles` — needed for 1.6

---

## 4. Wired data (ready)

| Config | File | Used by |
|---|---|---|
| `PATHWAY_RASTER` | `E:\NBSTOOLV3\SEA_NBS_PATHWAY.tif` | 4.1, 4.2, 1.1 (band 2) |
| `ACTIVITY_TABLE` | repo `canonical_v3_activities.csv` | 4.2 |
| `AGB_RASTER` (+ derived BGB) | `E:\NBSTOOLV3\AGBD_GEDI_AEF_pred_SEA_2024.tif` | 3.1, 5.x |
| `WDPA_POLYGON` | `E:\NBSTOOLV3\WDPA_SEA.shp` | 1.3 |
| `FC2014_RASTER`, `FC2024_RASTER`, `LC2024_RASTER` | `E:\NBSTOOLV3\SEA_FC2014/FC2024/LC2024.tif` | 1.5 |
| `PROB_RASTER` | `E:\NBSTOOLV3\SEA_DEFRISKS_PROB.tif` | 1.6 |
| `ELEVATION_RASTER` | `E:\NBSTOOLV3\SEA_ELEVATION_54034.tif` | 1.4 (slope derived) |
| `FLII_FOREST_RASTER`, `FLII_CLASS_RASTER` | `D:\NBSTOOLV3\flii_mosaic / flii_class_mosaic_SEA_300m.tif` | 2.1 |

---

## 5. Verify on first run

- [ ] `PROB_RASTER` is UInt16 with 0–65535 encoding 0–100 (1.6 rescale).
- [ ] FLII class raster carries codes 1/2/3 = Low/Medium/High (2.1).
- [ ] `GADM_*` field names match config once GADM is added (1.2).
- [ ] Slope unit: n/a — slope is derived from the elevation DEM, not a raster.

---

## 6. Highest-impact next steps

1. **GADM** → unblocks 1.2, and 1.6 (which needs the dominant country from 1.2).
2. **Hazard rasters** → one set unblocks both 1.7 and 3.5.
3. **National risk CSV** + implement `load_national_forest_risk_percentiles` → unblocks 1.6.
4. **KBA** → unblocks 2.2 (vector loader already done).
