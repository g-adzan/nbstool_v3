# NBS Screening Tool (Backend Analysis)

Pre-feasibility screening backend for Nature-Based Solutions (NBS) carbon projects, developed
for NBS Tool v3 under the SCeNe Coalition. Given a project Area of Interest (AOI) polygon, the
tool overlays it with pre-defined geospatial layers and returns site characterization, threat
profiles, a pathway recommendation, and a benefit estimate.

This repository is the runtime screening layer. It consumes pre-defined layers produced upstream
by other methods.

## Status

All analysis logic is real Python: masking, tabulation, thresholds, narrative construction. File
access sits in a few stubs in `common.py`. `load_raster_clipped` is implemented (rasterio warp,
clip and polygon mask to the reference CRS), so the raster-only notebooks, including
`F02-P4 Pathway`, run once their paths are set in `config.py`. `load_activity_table` is also implemented and `ACTIVITY_TABLE` points to the bundled
`canonical_v3_activities.csv`, so 4.2 runs as well. Three stubs remain and raise `NotImplementedError` until the notebooks that need them are run: `load_vector_intersecting`,
`load_soil_class_table`, `load_national_forest_risk_percentiles`.

Design rationale lives in the markdown cells next to each component, not in a separate document.

## Notebooks (F02 phased structure)

| Notebook               | Phase  | Status                              |
| ---------------------- | ------ | ----------------------------------- |
| `F02-P2 General.ipynb` | F02-P2 | done (1.1 to 1.7)                   |
| `F02-P2 Nature.ipynb`  | F02-P2 | done (2.1 FLII, 2.2 KBA)            |
| `F02-P2 Climate.ipynb` | F02-P2 | 3.1 to 3.6 done                      |
| `F02-P3 Threats.ipynb` | F02-P3 | upcoming                            |
| `F02-P4 Pathway.ipynb` | F02-P4 | 4.1, 4.2 done (canonical_v3)         |
| `F02-P5 Benefit.ipynb` | F02-P5 | 5.1 general benefit, 5.2 avoided unplanned deforestation done |

Each component follows the same shape: a markdown cell with data, locked decisions, example
render and downstream use, then a code cell with one `analyze_*` function returning a
`ComponentResult`.

## How notebooks talk to each other

Notebook filenames contain spaces and hyphens, so they are not importable Python module names.
Nothing imports a notebook. Instead:

- **Shared code** lives in `common.py` and `config.py`, star imported at the top of every
  notebook (`from config import *`, `from common import *`), mirroring the
  `sea_deforestation_risk` house style.
- **Results** are passed as JSON on disk. Each notebook ends with
  `save_results(results, aoi, aoi_id, STAGE_*)`, which writes
  `outputs/<aoi_id>__<stage>.json`. A notebook that needs an earlier stage starts with
  `load_results(aoi_id, STAGE_*)`. Every stage file repeats the AOI block, so a stale file from
  a different AOI is caught rather than silently mixed in.

Set the same `aoi_id` in every notebook for one project area.

## User inputs

Beyond the AOI polygon, the tool takes one user input so far: `PROJECT_DURATION_YEARS`, set in
the Setup cell of `F02-P5 Benefit.ipynb` next to `AOI_PATH`. It is passed to the component as an
argument and written into the saved result, so a stage file records the duration it was produced
with.

## Reference CRS

The AOI is accepted in any CRS and reprojected once to ESRI:54034 (World Cylindrical Equal Area)
for all area work, by `common.prepare_aoi`. No component reprojects the AOI again. **Locked by
the team.** It differs from the per-region conformal CRS in the backend on purpose: the tool
needs area, not distance or shape.

Consequence to keep in mind: an equal-area projection preserves area but distorts distance and
shape, increasingly so away from the equator. Every hectare figure in the tool is sound. Any
future component that measures a distance, a perimeter, or a shape index must not use this CRS.

## Dependencies

`environment.yml` builds the `nbs-screening` conda environment. Every package it lists is there
for a reason, and the list is already complete for the finished tool, not only for what runs
today:

| Package | Used by |
|---|---|
| `numpy` | all array work: masks, tabulation, stacking, medians |
| `geopandas`, `shapely` | AOI handling, `prepare_aoi`, all vector overlay (1.2, 1.3, 2.2) |
| `rasterio`, `gdal` | `load_raster_clipped`, once the stub is implemented |
| `pandas` | `load_soil_class_table` and `load_national_forest_risk_percentiles` |
| `jupyterlab`, `ipykernel` | running the notebooks |

`rasterio` and `pandas` are imported in `common.py` for the implemented loaders
(`load_raster_clipped`, `load_activity_table`). The remaining stubs need no new packages.

Not included, and a decision to make: **`matplotlib` is absent**, because the notebooks build no
plots. Every chart is emitted as data in `tables` and drawn by the frontend. If you want to
preview the bar charts inside the notebooks while developing, add `matplotlib` to
`environment.yml` and a plotting cell per component.

## Data inputs

All pre-defined layer paths and locked constants live in `config.py`. Set every path marked
`<SET ...>` before running. That file is the full input checklist.

## Layout

- `config.py` - layer registry, reference CRS, class codes, thresholds, stage keys
- `common.py` - AOI contract, data access stubs, zonal tabulation, shared forest masks,
  narrative helpers, `ComponentResult`, result handoff (`save_results` / `load_results`)
- `F02-P2 General.ipynb` - components 1.1 to 1.7
- `F02-P2 Nature.ipynb` - components 2.1 and 2.2
- `F02-P2 Climate.ipynb` - components 3.1 to 3.6
- `F02-P4 Pathway.ipynb` - components 4.1 and 4.2
- `F02-P5 Benefit.ipynb` - component 5.1
- `wrb_descriptions.py` - WRB 2006 soil group glosses, soil properties only
- `DATA_STATUS.md` - living checklist: which data is wired, which is missing, which sections run
- `canonical_v3_activities.csv` - activity + Triple Win benefit + QB catalog, exported from the Sheet, joined on (cat_code, ecosystem)
- `outputs/` - per stage result JSON, written at run time
- `docs/backend_analysis_pseudocode.md` - superseded by the notebooks, kept only until the
  conversion is reviewed, then to be deleted
- `environment.yml` - conda environment
