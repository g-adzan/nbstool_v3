# NBS Screening Tool (Backend Analysis)

Pre-feasibility screening backend for Nature-Based Solutions (NBS) carbon projects, developed
for NBS Tool v3 under the SCeNe Coalition. Given a project Area of Interest (AOI) polygon, the
tool overlays it with pre-defined geospatial layers and returns site characterization, threat
profiles, a pathway recommendation, and a benefit estimate.

This repository is the runtime screening layer. It consumes pre-defined layers produced upstream
by other methods.

## Status

Runnable. All analysis logic is real Python (masking, tabulation, thresholds, narrative
construction), and the data-access layer in `common.py` is implemented: `load_raster_clipped`
(rasterio), `load_vector_intersecting` (geopandas) and `load_activity_table` (pandas). Most
sections run today against the datasets wired in `config.py`.

One data-access stub still raises `NotImplementedError` until its section is used:
`load_soil_class_table` (3.6, parked pending the soil legend). 1.6's loader is implemented but
needs its CSV built once with `build_national_risk_reference.py`.

**`DATA_STATUS.md` is the source of truth for what is wired, what data is still missing, and
which sections run.** Read it first.

## Quickstart

1. Build the environment: `conda env create -f environment.yml` then
   `conda activate nbs-screening` (see the header of `environment.yml` for the resilient
   conda settings and the Jupyter kernel registration).
2. Set the AOI in `config.py`: `AOI_PATH` and `AOI_ID` (one place, see below).
3. Point any unset layer paths in `config.py` (marked `<SET ...>`) at your files. Everything
   already wired points at `D:\NBSTOOLV3`.
4. Open a notebook and Run All. For sections that read an earlier stage (Climate 3.2, all of
   Benefit), run and save `F02-P2 General` and `F02-P4 Pathway` first.

**Whenever you edit `config.py`, restart the notebook kernel** — `from config import *` caches
the module, so a running kernel keeps the old values.

## Notebooks (F02 phased structure)

| Notebook               | Phase  | Components |
| ---------------------- | ------ | ---------- |
| `F02-P2 General.ipynb` | F02-P2 | 1.1 Ecosystem, 1.2 Admin, 1.3 WDPA, 1.4 Terrain, 1.5 Deforestation, 1.6 Risk, 1.7 Hazard, 1.8 Land Cover |
| `F02-P2 Nature.ipynb`  | F02-P2 | 2.1 FLII, 2.2 KBA |
| `F02-P2 Climate.ipynb` | F02-P2 | 3.1 Carbon, 3.2 Soil carbon, 3.3 Temperature, 3.4 Precipitation, 3.5 Fire, 3.6 Soil class, 3.7 Historical burned area |
| `F02-P3 Threats.ipynb` | F02-P3 | upcoming |
| `F02-P4 Pathway.ipynb` | F02-P4 | 4.1 Pathway distribution, 4.2 Activity list |
| `F02-P5 Benefit.ipynb` | F02-P5 | 5.1 General benefit, 5.2 Avoided unplanned deforestation, 5.3 ARR carbon removal |

Each component is a markdown cell (data, decisions, downstream use) then a code cell with one
`analyze_*` function returning a `ComponentResult`. Each section runs and displays itself when
its cell runs, via `show_result`; the final cell writes the combined JSON. The computed-table
sections (4.1, 4.2) show a table and a `values` dict instead of a narrative sentence.

## AOI and outputs (one place)

The AOI is set once in `config.py`:

```python
AOI_PATH = r"D:\NBSTOOLV3\AOI1.shp"
AOI_ID   = "aoi1"
```

Every notebook reads these, so switching AOI is a single edit plus a kernel restart. `AOI_ID`
names the per-AOI output folder, so runs never mix. Everything a run writes goes under
`D:\NBSTOOLV3\OUTPUTS\<AOI_ID>\`:

- the JSON stage handoff, `<AOI_ID>__<stage>.json`, in the folder itself;
- saved output GeoTIFFs under `rasters\` (one per raster-producing section, in the reference
  CRS, masked cells as nodata);
- every output table as CSV under `tables\`.

The raster and CSV saves happen automatically when a section's cell runs (via `save_raster` and
`save_table_csv` inside `show_result`).

## How notebooks talk to each other

Notebook filenames contain spaces and hyphens, so they are not importable Python module names.
Nothing imports a notebook. Instead:

- **Shared code** lives in `common.py` and `config.py`, star imported at the top of every
  notebook (`from config import *`, `from common import *`).
- **Results** pass as JSON on disk. Each notebook ends with
  `save_results(results, aoi, aoi_id, STAGE_*)`; a notebook that needs an earlier stage starts
  with `load_results(aoi_id, STAGE_*)`. Every stage file repeats the AOI block, so a stale file
  from a different AOI is caught rather than silently mixed in.

Run order for cross-stage sections: Climate 3.2 reads General; Benefit 5.1/5.2 read Pathway
(and 5.2 also reads General 1.5). Run and save those upstream notebooks first. `DATA_STATUS.md`
has the details.

## User inputs

Beyond the AOI, `F02-P5 Benefit` takes `PROJECT_DURATION_YEARS`, set in its Setup cell. It is
passed to the components and written into the saved result, so a stage file records the duration
it was produced with.

## Reference CRS

The AOI is accepted in any CRS and reprojected once to ESRI:54034 (World Cylindrical Equal Area)
for all area work, by `common.prepare_aoi`. No component reprojects the AOI again. **Locked by
the team.** It differs from the per-region conformal CRS in the backend on purpose: the tool
needs area, not distance or shape.

Consequence to keep in mind: an equal-area projection preserves area but distorts distance and
shape, increasingly so away from the equator. Every hectare figure in the tool is sound. Slope
in 1.4 is derived from the elevation DEM with a latitude correction for exactly this reason; any
other component measuring distance, perimeter or a shape index must not use this CRS.

## Dependencies

`environment.yml` builds the `nbs-screening` conda environment (conda-forge, strict priority).

| Package | Used by |
|---|---|
| `numpy` | all array work |
| `geopandas`, `shapely` | AOI handling, `prepare_aoi`, vector overlay (1.2, 1.3, 2.2) |
| `rasterio`, `gdal` | `load_raster_clipped`, `save_raster` |
| `pandas` | `load_activity_table`, `save_table_csv`, CSV lookups |
| `jupyterlab`, `ipykernel` | running the notebooks |

`matplotlib` is deliberately absent: the notebooks build no plots, every chart is emitted as
data in `tables` and drawn by the frontend. Add it only if you want in-notebook chart previews.

## Data inputs

All layer paths and locked constants live in `config.py`; it is the full input checklist.
Datasets are under `D:\NBSTOOLV3` (rasters, vectors) and `D:\NBSTOOLV3\disaster_risks` (hazards).
Paths still marked `<SET ...>` are not available yet; see `DATA_STATUS.md`.

## Layout

- `config.py` - AOI, output folders, layer registry, reference CRS, class codes, thresholds,
  stage keys
- `common.py` - AOI contract, `load_*` data access, zonal tabulation, forest masks, terrain and
  climate helpers, `ComponentResult`, `show_result`, `save_raster` / `save_table_csv`, result
  handoff (`save_results` / `load_results`)
- `F02-P2 General.ipynb` - components 1.1 to 1.8
- `F02-P2 Nature.ipynb` - components 2.1 and 2.2
- `F02-P2 Climate.ipynb` - components 3.1 to 3.7
- `F02-P4 Pathway.ipynb` - components 4.1 and 4.2
- `F02-P5 Benefit.ipynb` - components 5.1, 5.2, 5.3
- `wrb_descriptions.py` - WRB 2006 soil group glosses, soil properties only
- `build_national_risk_reference.py` - one-off builder for the 1.6 national risk CSV (run once)
- `canonical_v3_activities.csv` - activity + Triple Win benefit + QB catalog, joined on
  (cat_code, ecosystem)
- `DATA_STATUS.md` - living checklist: what is wired, what is missing, which sections run
- `docs/backend_analysis_pseudocode.md` - superseded by the notebooks, kept for reference
- `environment.yml` - conda environment
