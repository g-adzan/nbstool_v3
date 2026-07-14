# NBS Screening Tool (Backend Analysis)

Pre-feasibility screening backend for Nature-Based Solutions (NBS) carbon projects, developed
for NBS Tool v3 under the SCeNe Coalition. Given a project Area of Interest (AOI) polygon, the
tool overlays it with pre-defined geospatial layers and returns site characterization, threat
profiles, a pathway recommendation, and a benefit estimate.

This repository is the runtime screening layer. It consumes pre-defined layers produced upstream
by other methods. The `sea_deforestation_risk` pipeline is one of those upstream methods and is
not part of this repository.

## Status

Design stage. The analysis is specified as narrative pseudo-code in
`docs/backend_analysis_pseudocode.md`. Two modules are drafted: Site Characterization General
Context (components 1.1 to 1.7) and Site Characterization Nature (2.1 FLII, 2.2 KBA). The next
module is Site Characterization Climate. Other modules are upcoming.

## Modules (F02 phased structure)

| Module | Phase | Status |
|--------|-------|--------|
| Site Characterization: General Context | F02-P2 | done (1.1 to 1.7) |
| Site Characterization: Nature | F02-P2 | done (2.1 FLII, 2.2 KBA) |
| Site Characterization: Climate | F02-P2 | next |
| Threat Profiles | F02-P3 | upcoming |
| Pathway Recommendation | F02-P4 | upcoming |
| Benefit Quantification | F02-P5 | upcoming |

## Reference CRS

The AOI is accepted in any CRS and reprojected to ESRI:54034 (World Cylindrical Equal Area) for
all area work. This is interim while the team finalizes the reference CRS.

## Data inputs

All pre-defined layer paths and locked constants live in `config.py`. Set every path marked
`<SET ...>` before running. That file is the full input checklist.

## Layout

- `config.py` - layer registry, reference CRS, class codes, thresholds
- `docs/backend_analysis_pseudocode.md` - the design specification
- `environment.yml` - conda environment
