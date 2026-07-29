# Data & Runnability Status

Living checklist of what is wired, what data is still missing, and which notebook sections can
run. Update the checkboxes as data arrives. Last checked: 2026-07-28 (after the second upload).

Legend: ✅ ready · ⛔ blocked (data or code) · ⚠️ runs, but verify something on first run.

---

## 1. Section runnability

| Section | State | Note / blocked by |
|---|---|---|
| 1.1 Ecosystem Type | ✅ | derived from pathway band 2 |
| 1.2 Administrative Boundaries | ⚠️ | wired (one combined shapefile, dissolved by GID); verify GID/NAME fields on first run |
| 1.3 Protected Areas (WDPA) | ✅ | fields verified, uses `REALM` |
| 1.4 Terrain | ✅ | slope derived from elevation DEM |
| 1.5 Historical Deforestation | ✅ | — |
| 1.6 Deforestation Risk | ⛔ | national risk CSV + stub `load_national_forest_risk_percentiles` |
| 1.7 Natural Disaster Hazard | ⛔ | 5 hazard rasters |
| 2.1 Forest Landscape Integrity | ⚠️ | verify class raster carries 1/2/3 |
| 2.2 Key Biodiversity Areas | ✅ | KBA wired (`IntName`) |
| 3.1 Current Carbon Storage | ✅ | AGB wired, BGB derived |
| 3.2 Soil Organic Carbon | ✅ | 0–30 cm = sum of stock1+2+3 (SoilGrids depths) |
| 3.3 Annual Temperature | ⚠️ | 12-band raster wired; verify unit + source/period label |
| 3.4 Annual Precipitation | ⚠️ | 12-band raster wired; verify unit + source/period label |
| 3.5 Fire Susceptibility | ⛔ | fire hazard raster (same file as 1.7 fire) |
| 3.6 Soil Classification | ⛔ | **parked** — awaiting team confirm of code→name lookup; + stub |
| 4.1 Pathway Distribution | ⚠️ | verify prob/pathway values; runs |
| 4.2 Activity List | ✅ | — |
| 5.1 General Benefit | ✅* | needs the F02-P4 stage JSON first |
| 5.2 Avoided Unplanned Deforestation | ✅* | needs F02-P4 + F02-P2 General (1.5) stage JSON + `PROJECT_DURATION_YEARS` |

Runnable now: **1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2**, plus **5.1, 5.2**
after their upstream stages are run (see F02-P5 run order below). ⚠️ rows run but need a
one-time check.

### F02-P5 run order (cross-stage, not missing data)

- **5.1** reads the **F02-P4** stage. Run and save `F02-P4 Pathway` first.
- **5.2** reads **F02-P4** (QB gate) + **F02-P2 General** (1.5 rate). Set `PROJECT_DURATION_YEARS`.
  Run only General's working cells then Save, so the General JSON carries the rate.

---

## 2. Data still missing / pending

- [ ] **National forest risk reference** — `NATIONAL_FOREST_RISK_CSV` (1.6). Per-country
      percentile breakpoints of `prob.tif`.
- [ ] **Hazard rasters ×5** — `HAZARD_RASTERS`: landslide, flood, flashflood, fire, drought
      (1.7). The `fire` file is also reused by 3.5.
- [x] **Soil organic carbon depths** — resolved: SoilGrids 0-5/5-15/15-30/30-60/60-100 cm; 3.2 sums the top three for 0–30 cm.
- [ ] **Soil class code→name lookup** (3.6) — PARKED, team to confirm the legend for `soil_groups.tif` (0–29). Not assumed alphabetical.

---

## 3. Code stubs (`common.py`)

- [x] `load_raster_clipped` · [x] `load_vector_intersecting` · [x] `load_activity_table`
- [ ] `load_soil_class_table` — needed for 3.6
- [ ] `load_national_forest_risk_percentiles` — needed for 1.6

---

## 4. Wired data (ready)

| Config | File | Used by |
|---|---|---|
| `PATHWAY_RASTER` | `E:\NBSTOOLV3\SEA_NBS_PATHWAY.tif` | 4.1, 4.2, 1.1, 5.2 |
| `ACTIVITY_TABLE` | repo `canonical_v3_activities.csv` | 4.2 |
| `AGB_RASTER` (+ derived BGB) | `E:\NBSTOOLV3\AGBD_GEDI_AEF_pred_SEA_2024.tif` | 3.1, 5.2 |
| `ADMIN_BOUNDARIES` | `E:\NBSTOOLV3\SEA_Administrative_Boundaries_4326_(revised).shp` | 1.2 |
| `WDPA_POLYGON` | `E:\NBSTOOLV3\WDPA_SEA.shp` | 1.3 |
| `KBA_POLYGON` | `E:\NBSTOOLV3\SouthEast_Asia_KBA.shp` | 2.2 |
| `FC2014/FC2024/LC2024_RASTER` | `E:\NBSTOOLV3\SEA_FC2014/FC2024/LC2024.tif` | 1.5 |
| `PROB_RASTER` | `E:\NBSTOOLV3\SEA_DEFRISKS_PROB.tif` | 1.6, 5.2 |
| `ELEVATION_RASTER` | `E:\NBSTOOLV3\SEA_ELEVATION_54034.tif` | 1.4 (slope derived) |
| `FLII_FOREST/CLASS_RASTER` | `D:\NBSTOOLV3\flii_mosaic / flii_class_mosaic_SEA_300m.tif` | 2.1 |
| `WORLDCLIM_TAVG/PREC_RASTER` | `E:\NBSTOOLV3\temperature_v3 / precipitation_v3.tif` (12-band) | 3.3, 3.4 |
| `SOIL_CLASS_RASTER` | `E:\NBSTOOLV3\soil_groups.tif` | 3.6 (needs lookup) |

---

## 5. Verify on first run

- [ ] `PROB_RASTER` is UInt16, 0–65535 = 0–100 (1.6).
- [ ] FLII class raster codes are 1/2/3 = Low/Medium/High (2.1).
- [ ] 1.2 admin field names `GID_0/1/2`, `NAME_1/2`, `COUNTRY` match (they do in this file).
- [ ] `temperature_v3` unit is °C and `precipitation_v3` is mm; confirm the source/period so the
      `WORLDCLIM_*` labels are right (3.3, 3.4).

---

## 6. Highest-impact next steps

1. **Hazard rasters** → one set unblocks 1.7 and 3.5.
2. **National risk CSV** + implement `load_national_forest_risk_percentiles` → unblocks 1.6.
3. **Soil class lookup** (parked) + implement `load_soil_class_table` → unblocks 3.6.
