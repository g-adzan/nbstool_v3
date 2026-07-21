# NBS Screening Tool (Backend Analysis)

Pre-feasibility screening backend for Nature-Based Solutions (NBS) carbon projects, developed
for NBS Tool v3 under the SCeNe Coalition. Given a project Area of Interest (AOI) polygon, the
tool overlays it with pre-defined geospatial layers and returns site characterization, threat
profiles, a pathway recommendation, and a benefit estimate.

This repository is the runtime screening layer. It consumes pre-defined layers produced upstream
by other methods.

## Status

Design stage, specified as **Jupyter notebooks that are not yet runnable**. All analysis logic
is real Python: masking, tabulation, thresholds, narrative construction. Only file access is
stubbed. The three stubs in `common.py` (`load_raster_clipped`, `load_vector_intersecting`,
`load_national_forest_risk_percentiles`) raise `NotImplementedError`. Filling them is what makes
the tool run; nothing else needs rewriting.

Design rationale lives in the markdown cells next to each component, not in a separate document.

## Notebooks (F02 phased structure)

| Notebook               | Phase  | Status                              |
| ---------------------- | ------ | ----------------------------------- |
| `F02-P2 General.ipynb` | F02-P2 | done (1.1 to 1.7)                   |
| `F02-P2 Nature.ipynb`  | F02-P2 | 2.1 FLII, 2.2 KBA done; 2.3 pending |
| `F02-P2 Climate.ipynb` | F02-P2 | next                                |
| `F02-P3 Threats.ipynb` | F02-P3 | upcoming                            |
| `F02-P4 Pathway.ipynb` | F02-P4 | upcoming                            |
| `F02-P5 Benefit.ipynb` | F02-P5 | upcoming                            |

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

## Reference CRS

The AOI is accepted in any CRS and reprojected once to ESRI:54034 (World Cylindrical Equal Area)
for all area work, by `common.prepare_aoi`. No component reprojects the AOI again. **Locked by
the team.** It differs from the per-region conformal CRS in the backend on purpose: the tool
needs area, not distance or shape.

Consequence to keep in mind: an equal-area projection preserves area but distorts distance and
shape, increasingly so away from the equator. Every hectare figure in the tool is sound. Any
future component that measures a distance, a perimeter, or a shape index must not use this CRS.

## Data inputs

All pre-defined layer paths and locked constants live in `config.py`. Set every path marked
`<SET ...>` before running. That file is the full input checklist.

## Layout

- `config.py` - layer registry, reference CRS, class codes, thresholds, stage keys
- `common.py` - AOI contract, data access stubs, zonal tabulation, shared forest masks,
  narrative helpers, `ComponentResult`, result handoff (`save_results` / `load_results`)
- `F02-P2 General.ipynb` - components 1.1 to 1.7
- `F02-P2 Nature.ipynb` - components 2.1 and 2.2
- `outputs/` - per stage result JSON, written at run time
- `docs/backend_analysis_pseudocode.md` - superseded by the notebooks, kept only until the
  conversion is reviewed, then to be deleted
- `environment.yml` - conda environment
