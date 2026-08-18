# Data & Runnability Status

Living checklist of what is wired, what data is still missing, and which notebook sections can
run. Update the checkboxes as data arrives. Last checked: 2026-07-29 (after 5.3 ARR carbon).

Legend: ✅ ready · ⛔ blocked (data or code) · ⚠️ runs, but verify something on first run.

AOI + outputs (one place): set `AOI_PATH` and `AOI_ID` in `config.py`, then RESTART every
notebook kernel. Outputs go to `D:\NBSTOOLV3\OUTPUTS\<AOI_ID>\`: JSON stage handoff in the
folder, saved GeoTIFFs under `rasters\`, and every output table as CSV under `tables\`.
Each section writes its raster and its table CSVs automatically when its cell runs (via
`save_raster` and `save_table_csv` in `show_result`). Sections that save a
raster: 1.1, 1.4, 1.5, 1.7, 1.8, 2.1, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1 (vector sections 1.2/1.3/2.2/4.2
and the numeric 5.x produce none).


---

## 1. Section runnability

| Section | State | Note / blocked by |
|---|---|---|
| 1.1 Ecosystem Type | ✅ | derived from pathway band 2 |
| 1.2 Administrative Boundaries | ⚠️ | wired (one combined shapefile, dissolved by GID); verify GID/NAME fields on first run |
| 1.3 Protected Areas (WDPA) | ✅ | fields verified, uses `REALM` |
| 1.4 Terrain | ✅ | slope derived from elevation DEM |
| 1.5 Historical Deforestation | ✅ | — |
| 1.6 Deforestation Risk | ⚠️ | loader done; run `build_national_risk_reference.py` once to make the CSV; graceful (no verdict) without it |
| 1.7 Natural Disaster Risks | ⚠️ | 5 risk rasters wired (`RISK_RASTERS`, risk_*.tif, 4-class 1-4, 0=nodata); cyclone/drought are coarse (~11 km, ~28 km) so a small AOI may be one class |
| 1.8 Land Cover | ✅ | LC2024 20-class map; full + top-6 tables |
| 2.1 Forest Landscape Integrity | ⚠️ | verify class raster carries 1/2/3 |
| 2.2 Key Biodiversity Areas | ✅ | KBA wired (`IntName`) |
| 3.1 Current Carbon Storage | ✅ | AGB wired, BGB derived |
| 3.2 Soil Organic Carbon | ✅ | 0–30 cm = sum of stock1+2+3 (SoilGrids depths) |
| 3.3 Annual Temperature | ⚠️ | 12-band raster wired; verify unit + source/period label |
| 3.4 Annual Precipitation | ⚠️ | 12-band raster wired; verify unit + source/period label |
| 3.5 Fire Susceptibility | ⚠️ | fire wired (hazard_fire.tif); verify 1–5 encoding |
| 3.6 Soil Classification | ⛔ | **parked** — awaiting team confirm of code→name lookup; + stub |
| 3.7 Historical Burned Area | ⚠️ | GABAM 2014-2024 wired (`GABAM_RASTER_TEMPLATE`, MOSAIC_2); union headline + per-year bar chart; 11 clips per run |
| 4.1 Pathway Distribution | ⚠️ | verify prob/pathway values; runs |
| 4.2 Activity List | ✅ | — |
| 5.1 General Benefit | ✅* | needs the F02-P4 stage JSON first |
| 5.2 Avoided Unplanned Deforestation | ✅* | needs F02-P4 + F02-P2 General (1.5) stage JSON + `PROJECT_DURATION_YEARS` |
| 5.3 ARR Carbon Removal (ex-ante) | ⚠️ | runs directly from rasters (pathway + AGB + elevation + precip), no stage file; baseline uses PLACEHOLDER class values (C4/C5/C6), and precip/elev units to verify |

Runnable now: **1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 2.1, 2.2, 3.1, 3.2, 3.3, 3.4, 3.5, 3.7, 4.1, 4.2, 5.3**, plus
**5.1, 5.2** after their upstream stages are run (see F02-P5 run order below). ⚠️ rows run but
need a one-time check.

### F02-P5 run order (cross-stage, not missing data)

- **5.1** reads the **F02-P4** stage. Run and save `F02-P4 Pathway` first.
- **5.2** reads **F02-P4** (QB gate) + **F02-P2 General** (1.5 rate). Set `PROJECT_DURATION_YEARS`.
  Run only General's working cells then Save, so the General JSON carries the rate.
- **5.3** reads the pathway, AGB, elevation and precip rasters **directly**, no stage file. Set
  `PROJECT_DURATION_YEARS`. Independent of 5.1 and 5.2.

---

## 2. Data still missing / pending

- [ ] **National forest risk reference CSV** (1.6) — run `build_national_risk_reference.py`
      once (nbs-screening env) to compute p10..p90 of prob.tif per country and write
      `NATIONAL_FOREST_RISK_CSV`. Until then 1.6 runs but reports "no national reference".
- [x] **Hazard rasters ×5** — wired from `D:\NBSTOOLV3\disaster_risks` (landslide, flood,
      flashflood, fire, drought). Folder also has cyclone + storm, deliberately left out (team keeps 1.7 to five hazards).
- [x] **Soil organic carbon depths** — resolved: SoilGrids 0-5/5-15/15-30/30-60/60-100 cm; 3.2 sums the top three for 0–30 cm.
- [ ] **Soil class code→name lookup** (3.6) — PARKED, team to confirm the legend for `soil_groups.tif` (0–29). Not assumed alphabetical.

---

## 3. Code stubs (`common.py`)

- [x] `load_raster_clipped` · [x] `load_vector_intersecting` · [x] `load_activity_table`
- [ ] `load_soil_class_table` — needed for 3.6
- [x] `load_national_forest_risk_percentiles` — implemented (reads NATIONAL_FOREST_RISK_CSV)

---

## 4. Wired data (ready)

| Config | File | Used by |
|---|---|---|
| `PATHWAY_RASTER` | `D:\NBSTOOLV3\SEA_NBS_PATHWAY.tif` | 4.1, 4.2, 1.1, 5.2 |
| `ACTIVITY_TABLE` | repo `canonical_v3_activities.csv` | 4.2 |
| `AGB_RASTER` (+ derived BGB) | `D:\NBSTOOLV3\AGBD_GEDI_AEF_pred_SEA_2024.tif` | 3.1, 5.2, 5.3 |
| `ADMIN_BOUNDARIES` | `D:\NBSTOOLV3\SEA_Administrative_Boundaries_4326_(revised).shp` | 1.2 |
| `WDPA_POLYGON` | `D:\NBSTOOLV3\WDPA_SEA.shp` | 1.3 |
| `KBA_POLYGON` | `D:\NBSTOOLV3\SouthEast_Asia_KBA.shp` | 2.2 |
| `FC2014/FC2024/LC2024_RASTER` | `D:\NBSTOOLV3\SEA_FC2014/FC2024/LC2024.tif` | 1.5; LC2024 also 1.8 |
| `PROB_RASTER` | `D:\NBSTOOLV3\SEA_DEFRISKS_PROB.tif` | 1.6, 5.2 |
| `ELEVATION_RASTER` | `D:\NBSTOOLV3\SEA_ELEVATION_54034.tif` | 1.4 (slope derived), 5.3 (dryland zone) |
| `FLII_FOREST/CLASS_RASTER` | `D:\NBSTOOLV3\flii_mosaic / flii_class_mosaic_SEA_300m.tif` | 2.1 |
| `WORLDCLIM_TAVG/PREC_RASTER` | `D:\NBSTOOLV3\temperature_v3 / precipitation_v3.tif` (12-band) | 3.3, 3.4; PREC also 5.3 (dryland zone) |
| `RISK_RASTERS` (5) | `D:\NBSTOOLV3\risk_*.tif` (cyclone, drought, fire, flood, landslide) | 1.7 |
| `HAZARD_RASTERS` (5) | `D:\NBSTOOLV3\disaster_risks\hazard_*.tif` | 3.5 (fire); ex-1.7, kept until 3.5 rebuild |
| `SOIL_CLASS_RASTER` | `D:\NBSTOOLV3\soil_groups.tif` | 3.6 (needs lookup) |
| `GABAM_RASTER_TEMPLATE` | `D:\NBSTOOLV3\MOSAIC_2\GABAM_<year>.tif` (2014-2024) | 3.7 |

---

## 5. Verify on first run

- [ ] `PROB_RASTER` is UInt16, 0–65535 = 0–100 (1.6).
- [ ] FLII class raster codes are 1/2/3 = Low/Medium/High (2.1).
- [ ] 1.2 admin field names `GID_0/1/2`, `NAME_1/2`, `COUNTRY` match (they do in this file).
- [x] 1.7 risk rasters (`risk_*.tif`) confirmed uint8, 4-class 1-4 (Very Low..High), 0=nodata.
- [ ] 3.5 still reads the old `hazard_fire.tif` (1–5 encoding); reconcile when 3.5 is rebuilt.
- [ ] `temperature_v3` unit is °C and `precipitation_v3` is mm; confirm the source/period so the
      `WORLDCLIM_*` labels are right (3.3, 3.4). **5.3 also depends on the precip unit being mm**:
      the dryland zone thresholds (annual > 2000 mm, dry month < 100 mm) assume mm/month.
- [ ] **5.3 baseline class values** (`ARR_BASELINE_CLASS_MGHA` C4 25, C5 5, C6 0 Mg/ha) are
      placeholders; the ARR removal total scales with them. Replace with sourced values.

---

## 6. Highest-impact next steps

1. **Run `build_national_risk_reference.py`** to produce the 1.6 national CSV.
2. **Soil class lookup** (parked) + implement `load_soil_class_table` → unblocks 3.6.
