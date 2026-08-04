# NBS Tool v3: Backend Analysis Pseudo-code

Running specification for the NBS Tool v3 runtime screening layer. This document is
written component by component as pseudo-code. When all Data Analyzer outputs are
complete, the sections are reorganised into the notebook repo (see Repo layout below).

Status: draft, in progress. Abstraction level: narrative pseudo-code (not runnable).

---

## Scope and repo layout

Standalone repo (working name `nbs_screening_tool`). It consumes pre-defined geospatial
layers that are produced upstream by other methods (the `sea_deforestation_risk` pipeline
is one of those upstream methods, not part of this repo).

The tool follows the F02 phased structure. This document is written module by module.

| Module | Phase | Status |
|--------|-------|--------|
| Site Characterization: General Context | F02-P2 | done (1.1 to 1.7) |
| Site Characterization: Nature | F02-P2 | done (2.1 FLII, 2.2 KBA) |
| Site Characterization: People | F02-P2 | done (Gridded WorldPop) |
| Site Characterization: Climate | F02-P2 | upcoming |
| Threat Profiles | F02-P3 | upcoming |
| Pathway Recommendation | F02-P4 | upcoming |
| Benefit Quantification | F02-P5 | upcoming |

The notebook split for the repo is decided when each module is built. General Context takes the
AOI polygon only; later modules also consume earlier outputs, and Benefit Quantification
additionally takes user parameters.

Shared configuration (layer registry, paths, class codes, constants) lives in `config.py`,
mirroring the `sea_deforestation_risk` house style (`from config import *`).

---

## Global conventions

- **Input CRS:** the AOI is accepted in any CRS. It is reprojected to the reference CRS
  before any measurement.
- **Reference CRS:** ESRI:54034 (World Cylindrical Equal Area). Interim choice while the
  team finalises the reference CRS. Equal-area, so hectare figures are consistent globally.
  This differs from the backend per-region conformal CRS on purpose: the tool needs area,
  not distance or shape.
- **AOI is heterogeneous:** an AOI spans many pixels and can cover several categories at
  once. Outputs are area-weighted distributions, not single labels.
- **Unresolved logic is explicit:** category branches that are not yet settled (for example
  trajectory Cat 8 and Cat 9) are marked UNRESOLVED or NEEDS_REFERENCE_LOOKUP, never
  silently skipped.

---

## [F02-P2] Site Characterization: General Context

Overlay the AOI with pre-defined layers using simple operations (clip, mask, count, area). This
is the General Context module of Site Characterization (form F02, phase P2).

### 1.1 Ecosystem Type

Reports the ecosystem setting of the AOI as area and share per ecosystem, for a pie chart
on the frontend, plus a composition narrative. The result is also the Axis 3 reference
ecosystem that drives downstream logic.

**Data:** `ecosystem_type.tif` (categorical raster; 1 = Dryland, 2 = Mangrove,
3 = Peatland; nodata elsewhere).

**Decisions locked:**
- Percentage denominator = total AOI area. An "Other/Unclassified" slice absorbs nodata and
  non-ecosystem pixels so the pie sums to 100.
- Composition uses pure presence: a class counts as present if its area is above zero (no
  threshold). Open risk: a single stray edge pixel can flip "single" to "combination".

**Pseudo-code:**

```
COMPONENT 1.1: ECOSYSTEM TYPE
Input: AOI polygon in ANY CRS
       ecosystem_type.tif (1=Dryland, 2=Mangrove, 3=Peatland; nodata elsewhere)
Output: per-ecosystem area (ha) and percentage, plus an "Other/Unclassified" share -> pie chart
        composition narrative (7 cases)
        present_set  -> Axis 3 reference ecosystem, passed downstream

STEP 0  Normalise CRS
  - Read the AOI's own CRS (accept whatever it is).
  - Reproject the AOI to the reference CRS ESRI:54034 (equal-area).
  - AOI_area_ha = polygon area in ESRI:54034 / 10000 # authoritative denominator

STEP 1  Align raster to AOI in the equal-area CRS
  - Clip / reproject ecosystem_type.tif to the AOI in ESRI:54034.
  - Nearest-neighbour resampling (categorical, values must not be interpolated).

STEP 2  Zonal tabulation
  - Mask the raster to the AOI polygon.
  - Count pixels per ecosystem class inside the AOI.
  - pixel_area_ha = (pixel_width * pixel_height) / 10000 # constant in an equal-area CRS
  - area_ha[class] = pixel_count[class] * pixel_area_ha

STEP 3  Percentage (denominator = total AOI area)
  - percent[class] = area_ha[class] / AOI_area_ha * 100
  - other_ha = max(0, AOI_area_ha - sum(area_ha[all 3 classes]))
  - percent_other = other_ha / AOI_area_ha * 100
  # pie chart = 3 ecosystem slices + one "Other/Unclassified" slice, sums to 100

STEP 4  Determine composition (pure presence)
  - present_set = { class : area_ha[class] > 0 }
  - single if |present_set| == 1, combination otherwise
  # "Other" is never part of present_set; it does not drive ecosystem logic

STEP 5  Select narrative
  - narrative = NARRATIVE_LOOKUP[frozenset(present_set)] # 7 keyed cases

STEP 6  Emit
  - table [ecosystem, area_ha, percent] + Other row  -> pie chart
  - narrative string
  - present_set  -> feeds Cat 8 conditional (Section 2) and activity ecosystem applicability (Section 3)
```

**Narrative lookup (7 cases):**

Single type:

- **Dryland.** This area sits on mineral soil that is not regularly flooded, unlike peatland
  or mangrove. Its natural reference ecosystem is dryland forest, dominated by trees growing
  on well-drained land.
- **Mangrove.** This area sits in a coastal zone with salt or brackish water shaped by the
  tides. Its natural reference ecosystem is mangrove, made up of trees and shrubs adapted to
  waterlogged, salty ground.
- **Peatland.** This area sits on peat, a soil built up from layers of organic material that
  stays wet for most of the year. Its natural reference ecosystem is peatland, a waterlogged
  system shaped by its deep organic soil.

Combinations:

- **Mangrove + Peatland.** This area is a coastal zone with tidal salt or brackish water that
  also sits on peat soil. It combines mangrove and peatland features in the same place.
- **Dryland + Peatland.** This area includes both mineral-soil ground and peat soil. Part of
  it follows a dryland reference, and part follows a peatland reference shaped by its wet,
  organic soil.
- **Dryland + Mangrove.** This area spans both non-flooded mineral soil inland and a tidal
  coastal zone. It combines dryland and mangrove references across different parts of the site.
- **Dryland + Mangrove + Peatland.** This area spans all three settings: non-flooded mineral
  soil inland, a tidal coastal zone with salt or brackish water, and ground built on wet peat
  soil. It combines dryland, mangrove, and peatland references across different parts of the site.

**Downstream use:** `present_set` is the Axis 3 reference ecosystem. It drives the Cat 8
ecosystem-conditional branch in Section 2 and the Ecosystem Applicability filter
(Dryland / Peatland / Mangrove) in the Activity Catalog used by Section 3.

### 1.2 Administrative Boundaries

Reports which administrative units the AOI overlaps, at three levels (country, province,
district), with the intersection area and share for each unit, plus a narrative.

**Data:** GADM v4.1 boundaries. L0 = country, L1 = province, L2 = district. The same source
already used elsewhere in the project (`gadm41_L1_with_region.csv`).

**Decisions locked:**
- Sliver threshold: an admin unit is reported only if its intersection is at least 1% of the
  AOI. This removes false slivers caused by the generalised GADM boundary lines. This is
  stricter than the pure presence rule in 1.1, on purpose, because boundary geometry is
  coarser than the ecosystem raster.
- The narrative shows percentages (share of AOI) as well as hectares.

**Pseudo-code:**

```
COMPONENT 1.2: ADMINISTRATIVE BOUNDARIES
Input: AOI polygon in ANY CRS
       GADM v4.1 boundaries: L0 (country), L1 (province), L2 (district)
Output: per-level list of intersecting admin units with area (ha) and share (%)
        composition narrative (text)

STEP 0  Normalise CRS
  - Reproject AOI to ESRI:54034 (equal-area).
  - AOI_area_ha = polygon area / 10000

STEP 1  Intersect per level
  - for level in [country L0, province L1, district L2]:
      for each admin unit that intersects the AOI:
        inter = geometric intersection(AOI, unit)
        area_ha[unit] = inter area / 10000
        pct[unit] = area_ha[unit] / AOI_area_ha * 100

STEP 2  Filter slivers
  - keep a unit only if pct[unit] >= 1.0  # share of AOI

STEP 3  Order and roll up
  - within each level, sort units by area descending (dominant first)
  - retained districts define their parent provinces and country (hierarchy stays consistent)

STEP 4  Build narrative (three adaptive clauses, joined into text)
  - opening: "This area covers {AOI_area_ha} ha."
  - country clause:
      if n_country == 1: "It lies within {country}."
      if n_country >= 2: "It is transboundary, crossing {c1} ({pct1}%) and {c2} ({pct2}%), ..."
  - province clause (when single country):
      if n_province == 1: "within {province} province"
      if n_province >= 2: "It spans {n} provinces: most of it is in {p1} ({area1} ha, {pct1}%), ..."
  - district clause:
      if n_district == 1: "in {district} district"
      if n_district >= 2: "Across these it falls within {n} districts: {d1} ({area1} ha), ..."
  - when country, province, and district are each single, merge into one sentence:
      "It lies entirely within {district} district, {province} province, {country}."

STEP 5  Emit
  - three tables [name, area_ha, pct] for country, province, district
  - narrative string
  - admin context passed downstream (jurisdiction, national dataset selection, reporting)
```

**Example renders:**

Single district:
> This area covers 1,240 ha. It lies entirely within Pelalawan district, Riau province, Indonesia.

Multiple provinces, one country:
> This area covers 1,240 ha and lies within Indonesia. It spans two provinces: most of it is in
> Riau (about 900 ha, 73%), and the rest is in Jambi (about 340 ha, 27%). Across these it falls
> within three districts: Pelalawan (620 ha), Indragiri Hulu (280 ha), and Tebo (340 ha).

Transboundary:
> This area covers 1,240 ha and is transboundary. It crosses Indonesia (about 1,000 ha, 81%) and
> Malaysia (about 240 ha, 19%).

**Downstream use:** the country result gates which national datasets and policies apply (for
example the APD land-status overlay, which is Indonesia-first). The province result links to
`gadm41_L1_with_region.csv` for mapping to the deforestation-risk regions. L2 availability
varies by country, so the emitter reports only the levels that exist for each country.

### 1.3 Protected Areas (WDPA)

Reports how much of the AOI overlaps protected areas, with a per-site breakdown and a
narrative. This is a key eligibility and additionality signal.

**Data:** `WDPA_polygon_4326.shp` (WDPA polygons in EPSG:4326; same source as the backend
`prep_wdpa_by_region.ipynb` / `pa_binary`).

**Decisions locked:**
- Headline overlap is computed on the union of protected areas (dissolve first, then
  intersect), because WDPA sites overlap each other and summing per site can exceed the AOI.
- No sliver threshold: even a small overlap is legally meaningful, so all overlap is reported.
- Narrative fields per site: name, designation (DESIG_ENG), IUCN category, status.
- Filter: keep STATUS in {Designated, Inscribed, Established}; drop pure marine (MARINE == 2),
  keep coastal (MARINE == 1) for mangrove; use polygon features only.

**Pseudo-code:**

```
COMPONENT 1.3: PROTECTED AREAS (WDPA)
Input: AOI polygon in ANY CRS
       WDPA_polygon_4326.shp (WDPA polygons, EPSG:4326)
Output: total protected overlap area (ha) and share (%)
        per-site list [name, designation, IUCN category, status, area_ha]
        narrative

STEP 0  Normalise CRS
  - Reproject AOI to ESRI:54034 (equal-area).
  - AOI_area_ha = polygon area / 10000

STEP 1  Filter WDPA
  - keep STATUS in {Designated, Inscribed, Established}
  - drop pure marine sites (MARINE == 2), keep coastal (MARINE == 1) for mangrove
  - use polygon features only (ignore WDPA point features)
  - select sites that intersect the AOI

STEP 2  Headline overlap (union, avoids double counting)
  - pa_union = dissolve/union of all selected WDPA polygons
  - overlap = intersection(AOI, pa_union)
  - protected_ha = overlap area / 10000
  - protected_pct = protected_ha / AOI_area_ha * 100
  # union first because WDPA sites overlap each other; summing per site can exceed the AOI

STEP 3  Per-site breakdown (for the narrative)
  - for each selected site:
      site_area_ha = intersection(AOI, site) area / 10000
  - sort sites by area descending (dominant first)

STEP 4  Build narrative
  - if protected_ha == 0: "This project area does not overlap any protected areas."
  - else choose single vs multiple template, dominant-first, with designation + IUCN + status

STEP 5  Emit
  - protected_ha, protected_pct
  - per-site table [name, designation, IUCN category, status, area_ha]
  - narrative
  - PA flag passed downstream (eligibility, additionality, pathway design constraint)
```

**Example renders:**

Overlap, single site:
> This project area overlaps 320 ha (26%) of protected areas. The overlap falls within Tesso
> Nilo National Park, designated as a National Park (IUCN category II, Designated).

Overlap, multiple sites:
> This project area overlaps 320 ha (26%) of protected areas, across 2 designated sites. The
> largest is Tesso Nilo National Park (210 ha), a National Park (IUCN category II); the rest is
> in Bukit Rimbang Baling Wildlife Reserve (110 ha), a Wildlife Reserve (IUCN category IV).

No overlap:
> This project area does not overlap any protected areas.

**Downstream use:** protected-area overlap is a critical eligibility and additionality signal.
A project inside a strict protected area (IUCN Ia, Ib, II) is generally hard to justify on
additionality, while overlap with unprotected land can strengthen the PROTECT pathway. This
flag is passed to Section 2 as a pathway design constraint.

### 1.4 Terrain (Slope and Elevation)

Reports the slope and elevation profile of the AOI as two distributions, each shown as a bar
chart, plus a short narrative.

**Data:** two pre-classified rasters, already in a metric CRS (not EPSG:4326, so pixel area is
constant): `slope_class_metric.tif` (5 slope classes) and `elevation_class_metric.tif`
(4 elevation classes).

**Class definitions (encoding):**

| Slope class code | Label | Range |
|---|---|---|
| 1 | Flat | 0-8% |
| 2 | Gently sloping | 8-15% |
| 3 | Moderately steep | 15-25% |
| 4 | Steep | 25-40% |
| 5 | Very steep | >40% |

| Elevation class code | Label | Range |
|---|---|---|
| 1 | Lowland | 0-500 m |
| 2 | Submontane / hill | 500-1000 m |
| 3 | Montane | 1000-2000 m |
| 4 | Upper montane | >2000 m |

**Decisions locked:**
- Input is already binned, so the tool only tallies class codes (no reclassification in the tool).
- Rasters are metric. If a raster is not in the reference CRS, reproject with nearest neighbour.
- Denominator for the bars = valid (non-nodata) area, so each bar chart sums to 100.
- Narrative uses class-based ranges (option a), not exact metres, because the input is binned.

**Pseudo-code:**

```
COMPONENT 1.4: TERRAIN (SLOPE AND ELEVATION)
Input: AOI polygon in ANY CRS
       slope_class_metric.tif      (classified slope, 5 classes, metric CRS)
       elevation_class_metric.tif  (classified elevation, 4 classes, metric CRS)
Output: slope distribution [class, area_ha, pct]      -> bar chart
        elevation distribution [class, area_ha, pct]  -> bar chart
        dominant classes, class range
        narrative

STEP 0  Normalise CRS
  - Reproject AOI to ESRI:54034 (equal-area).
  - Terrain rasters are already in a metric CRS. If not the reference CRS, reproject nearest (categorical).
  - pixel_area_ha = (pixel_width * pixel_height) / 10000 # constant in a metric CRS

STEP 1  Mask to AOI, drop nodata
  - mask each raster to the AOI polygon
  - keep valid (non-nodata) pixels

STEP 2  Tabulate per class (raster already binned, no reclassification)
  - count pixels per class code
  - area_ha[class] = pixel_count[class] * pixel_area_ha
  - pct[class] = area_ha[class] / valid_area * 100 # denominator = valid area, bars sum to 100

STEP 3  Summary
  - dominant_slope = slope class with largest area
  - dominant_elev = elevation class with largest area
  - elev_low, elev_high = lowest and highest elevation classes present

STEP 4  Build narrative (class-based ranges)
  - "Elevation ranges from {elev_low} to {elev_high}, predominantly {dominant_elev}."
  - "Slopes are predominantly {dominant_slope}."

STEP 5  Emit
  - two distribution tables -> two bar charts
  - narrative
  - terrain summary passed downstream (activity feasibility, erosion / landslide design constraint)
```

**Example render:**

> Elevation ranges from Lowland to Montane, predominantly Lowland. Slopes are predominantly
> Gently sloping.

**Downstream use:** terrain is a design constraint, not only a description. Steep slopes limit
some activities and raise erosion risk (links to Triple Win Pillar 1 and to landslide hazard),
while elevation guides species and forest-type choice (lowland vs montane). This summary is
passed to Section 2 and Section 3.

### 1.5 Historical Deforestation (2014-2024)

Reports how much forest the AOI lost between 2014 and 2024, the annual rate using the
Puyravaud method, and how that rate compares to the national rate.

**Data:** `FC2014.tif` (binary forest cover 2014, Tier 1-2), `LC2024.tif` (20-class land cover
2024), and a per-country lookup of the national deforestation rate. The tool derives the
forest change itself from the two rasters, so both dates use the same Tier 1-2 forest
definition (`FOREST_CODES = [1, 6, 7, 8, 10]`, Scenario 2A). Dominant country comes from 1.2.

**Decisions locked:**
- `A2 = A1 - loss_ha` (gross loss of 2014 forest; forest gain on non-forest-2014 land is
  excluded, so the rate stays consistent with the reported loss).
- Similar band = 0.20 (within plus or minus 20% of the national rate reads as "similar to").
- Comparison uses the dominant country from 1.2; the narrative notes when the AOI is transboundary.
- The national lookup rate is computed with Puyravaud too, so the comparison is valid.

**Puyravaud (2003) annual rate:** `rate = (1 / (t2 - t1)) * ln(A2 / A1) * 100`.

**Pseudo-code:**

```
COMPONENT 1.5: HISTORICAL DEFORESTATION (2014-2024)
Input: AOI polygon in ANY CRS
       FC2014.tif  (binary forest cover 2014, Tier 1-2)
       LC2024.tif  (20-class land cover 2024)
       national_deforestation_rate lookup (rate_pct per year, per country)
       dominant country (from 1.2)
Output: A1, A2, loss_ha, rate_pct (Puyravaud), comparison
        narrative

STEP 0  Normalise CRS
  - Clip FC2014 and LC2024 to the AOI, reproject to ESRI:54034 (nearest, categorical).
  - pixel_area_ha = constant

STEP 1  Derive forest at both dates (same Tier 1-2 definition)
  - forest_2014 = (FC2014 == forest)
  - forest_2024 = (LC2024 in FOREST_CODES)            # [1,6,7,8,10], Scenario 2A
  - A1 = area(forest_2014)
  - loss_ha = area(forest_2014 AND NOT forest_2024)   # gross loss of 2014 forest
  - A2 = A1 - loss_ha                                 # forest remaining (gain excluded)

STEP 2  Guard edge cases (before the log)
  - if A1 == 0: not applicable ("no forest present in 2014")
  - if loss_ha == 0: rate_pct = 0 ("no forest loss detected between 2014 and 2024")
  - if A2 == 0: total loss, report as such (avoid ln(0))

STEP 3  Puyravaud annual rate
  - t = 2024 - 2014 = 10
  - rate = (1 / t) * ln(A2 / A1) * 100   # negative for loss
  - rate_pct = abs(rate)

STEP 4  Compare to national rate
  - national_rate_pct = lookup[dominant_country]
  - if rate_pct > national_rate_pct * (1 + 0.20): comparison = "higher than"
    elif rate_pct < national_rate_pct * (1 - 0.20): comparison = "lower than"
    else: comparison = "similar to"

STEP 5  Build narrative
  - "Between 2014 and 2024, the project area lost {loss_ha} ha of forest, an average of
     {rate_pct}% per year. This is {comparison} the national rate for {country}, which is
     {national_rate_pct}% per year."

STEP 6  Emit
  - A1, A2, loss_ha, rate_pct, national_rate_pct, comparison
  - narrative
  - passed downstream (trajectory / threat intensity, AUD pathway signal)
```

**Example render:**

> Between 2014 and 2024, the project area lost 180 ha of forest, an average of 1.6% per year.
> This is higher than the national rate for Indonesia, which is 0.8% per year.

**Downstream use:** the observed forest loss is the empirical basis of the trajectory (Axis 2)
and a direct threat-intensity signal. A rate higher than the national rate supports an AUD
pathway (active deforestation pressure).

### 1.6 Deforestation Risk

Reports how the deforestation risk of the AOI forest compares to the national forest, as a
comparative narrative. There is no chart, only text.

**Data:** `prob.tif` (forestatrisk model output, UInt16 where 0-65535 encodes a 0-100 relative
risk score), the `forest_2024` mask from 1.5, `national_forest_risk_reference.csv` (per-country
percentile breakpoints of forest risk on the 0-100 scale), and the dominant country from 1.2.

**Important note on interpretation:** the forestatrisk value is a relative spatial risk ranking,
not an absolute probability. The tool never states an absolute "chance of deforestation". It
only places the AOI forest within the national distribution, expressed as a percentile.

**Decisions locked:**
- Pure comparative narrative (the risk-class bar chart option was dropped).
- Risk is summarised over AOI forest pixels only (non-forest land has no deforestation risk).
- AOI summary = median risk of AOI forest (robust to the skewed risk distribution).
- Comparison from the national percentile position: above p60 is "higher than", p40 to p60 is
  "similar to", below p40 is "lower than". No arbitrary band.
- Baseline is national, computed from the same `prob.tif` masked to the same Tier 1-2 forest,
  per country, so the comparison is apples-to-apples.

**Reference data to prepare:** `national_forest_risk_reference.csv`, one row per country:
`country, p10, p20, p30, p40, p50, p60, p70, p80, p90` (risk values on the 0-100 scale), derived
from `prob.tif` masked to that country's Tier 1-2 forest.

**Pseudo-code:**

```
COMPONENT 1.6: DEFORESTATION RISK (comparative, national)
Input: AOI polygon in ANY CRS
       prob.tif (UInt16; 0-65535 encodes a 0-100 relative risk score)
       forest_2024 mask (from 1.5)
       national_forest_risk_reference.csv (per-country percentile breakpoints, 0-100)
       dominant country (from 1.2)
Output: aoi_risk (median, 0-100), national_percentile, comparison
        narrative

STEP 0  Normalise CRS
  - Clip prob.tif to the AOI, reproject to ESRI:54034 if needed (bilinear or nearest per source).

STEP 1  Rescale to 0-100
  - risk_0_100 = prob_raw / 65535 * 100

STEP 2  Restrict to forest
  - keep risk only where forest_2024 is true (non-forest has no deforestation risk)
  - if AOI forest area == 0: not applicable ("no forest present to assess for deforestation risk")

STEP 3  Summarise the AOI
  - aoi_risk = median(risk_0_100 over AOI forest pixels)

STEP 4  Locate in the national distribution
  - national_percentile = interpolate aoi_risk within the country's percentile breakpoints
  - top_share = 100 - national_percentile

STEP 5  Comparison
  - if national_percentile > 60: comparison = "higher than"
    elif national_percentile < 40: comparison = "lower than"
    else: comparison = "similar to"

STEP 6  Build narrative
  - higher: "Forest in this area is at higher deforestation risk than the national average,
             ranking in the top {top_share}% of the country's forest for deforestation risk."
  - similar: "Forest in this area is at deforestation risk similar to the national average,
              around the national median."
  - lower: "Forest in this area is at lower deforestation risk than the national average, in
            the bottom {national_percentile}% of the country's forest."

STEP 7  Emit
  - aoi_risk, national_percentile, comparison
  - narrative
  - passed downstream (AUD pathway signal: standing forest + high risk = strong AUD candidate)
```

**Example render:**

> Forest in this area is at higher deforestation risk than the national average, ranking in the
> top 22% of the country's forest for deforestation risk.

**Downstream use:** together with the observed loss in 1.5 (past) this modelled risk (future)
frames the deforestation story. Standing forest at high risk is the core AUD signal for
Section 2.

### 1.7 Natural Disaster Hazard

Reports the natural disaster hazards the AOI is exposed to, one card per hazard, each with a
representative intensity level. This is hazard, not risk: the tool characterises the physical
threat at the site, and leaves risk (which needs an exposed asset and its vulnerability) to
Section 2 and Section 3. See the note below.

**Data:** five pre-classified 5-class intensity rasters: `hazard_landslides.tif`,
`hazard_flood.tif`, `hazard_flashflood.tif`, `hazard_fire.tif`, `hazard_drought.tif`.

**Encoding:** 1 = Very Low, 2 = Low, 3 = Moderate, 4 = High, 5 = Very High.

**Hazard, not risk:** in the disaster risk framework, `Risk = f(Hazard, Exposure, Vulnerability)`
and risk is always "risk to something". At the screening stage the tool has hazard layers but
not reliable exposure or vulnerability, so it reports hazard. The same hazard feeds two risk
lenses downstream: permanence risk (threat to the project forest and carbon, Activity Catalog
Role 2) and disaster risk reduction co-benefit (risk to communities that the NBS reduces,
Triple Win Pillar 3). Keeping the analyzer output as hazard serves both without bias.

**Decisions locked:**
- Show all five cards always, so the absence of a hazard is informative too.
- Representative level is conservative: the highest class that covers at least 20% of the AOI
  valid hazard area. Rationale: in hazard screening a false negative (calling a site safe when
  part of it is dangerous) is more costly than a false positive.
- No composite hazard index: the five hazards are not commensurable, so they stay separate.

**Pseudo-code:**

```
COMPONENT 1.7: NATURAL DISASTER HAZARD
Input: AOI polygon in ANY CRS
       5 hazard rasters, 5-class intensity (1=Very Low ... 5=Very High):
       hazard_landslides.tif, hazard_flood.tif, hazard_flashflood.tif,
       hazard_fire.tif, hazard_drought.tif
Output: per hazard -> representative level + 5-class distribution (drill-down)
        narrative highlighting elevated hazards
        {hazard: level} passed downstream

CONSTANTS
  HAZARDS = [landslide, flood, flashflood, fire, drought]
  LEVELS = {1: Very Low, 2: Low, 3: Moderate, 4: High, 5: Very High}
  PRESENCE_THRESHOLD = 20   # percent of the AOI valid hazard area

STEP 0  Normalise CRS
  - Reproject AOI to ESRI:54034 (equal-area). pixel_area_ha = constant.

for each hazard H in HAZARDS:
  STEP 1  Clip and align
    - clip H to the AOI, reproject nearest (categorical), keep valid (non-nodata) pixels
    - valid_area = area of valid hazard pixels in the AOI
  STEP 2  Distribution
    - for class c in 1..5: area_ha[c] = count(c) * pixel_area_ha; pct[c] = area_ha[c]/valid_area*100
  STEP 3  Representative level (conservative)
    - rep_class = highest c with pct[c] >= PRESENCE_THRESHOLD  # at least one class always qualifies
    - rep_level = LEVELS[rep_class]
  STEP 4  Emit per hazard
    - card: hazard name + rep_level
    - keep pct[1..5] for drill-down

STEP 5  Narrative (highlight elevated)
  - name hazards with rep_class >= 3 (Moderate or above) with their level
  - group hazards with rep_class <= 2 as "low"

STEP 6  Emit
  - five cards (all shown), each hazard + representative level
  - narrative
  - {hazard: rep_class} passed downstream (permanence-risk sensitivity + DRR opportunity)
```

**Example render:**

> The project area faces high fire hazard and moderate flood hazard. Landslide, flash flood,
> and drought hazards are low.

**Downstream use:** each hazard level is kept as structured output and read twice in Section 2
and Section 3. As permanence-risk sensitivity it constrains activity design and durability
(fire and drought are common threats to restored forest). As a DRR co-benefit it maps to the
Triple Win pillars (flood, flash flood, and landslide to Pillar 3; fire and erosion to Pillar 1;
drought to both).

<!-- General Context complete: components 1.1 to 1.7 -->

---

## [F02-P2] Site Characterization: Nature

Characterizes the ecological quality of the AOI forest and habitat.

### 2.1 Forest Landscape Integrity (FLII)

Reports the landscape integrity of the AOI forest as a headline mean score out of 10, with a
High / Medium / Low breakdown in the narrative. Integrity is the degree to which a forest is
still intact, connected, and free of human pressure.

**Data:** `flii_forest_mosaic_SEA_300m.tif` (continuous 0 to 10, on forest) and
`flii_class_mosaic_SEA_300m.tif` (1 = Low, 2 = Medium, 3 = High, on forest). Based on the Forest
Landscape Integrity Index (Grantham et al. 2020, Nat. Commun. 11:5978), reimplemented and
calibrated on the SEA data stack. Landscape scale, native 300 m.

**Note on calibration:** the 0 to 10 values are calibrated on the pooled SEA distribution, so
they are not one to one with the published global FLII product. Present them as the SEA forest
integrity layer, internally consistent within this run. Do not claim absolute global integrity.
Class breaks follow the paper (High at or above 9.6, Low at or below 6.0, Medium in between).

**Decisions locked:**
- FLII is a property of forest, so the summary is over AOI forest area only. Denominator = AOI
  forest area (same forest as 1.5 and 1.6).
- Headline is the mean FLII score out of 10 (a big number), over AOI forest.
- The narrative reports the High, Medium, and Low share of the forest and names the predominant
  (largest area) class.

**Pseudo-code:**

```
COMPONENT 2.1: FOREST LANDSCAPE INTEGRITY (FLII)
Input: AOI polygon in ANY CRS
       flii_forest_mosaic_SEA_300m.tif  (continuous 0-10, on forest)
       flii_class_mosaic_SEA_300m.tif   (1=Low, 2=Medium, 3=High, on forest)
Output: mean_flii (0-10, headline big number)
        integrity distribution [class, area_ha, pct] over AOI forest
        dominant class, pct_high
        narrative

STEP 0  Normalise CRS
  - Reproject AOI to ESRI:54034 (equal-area). pixel_area_ha = constant.

STEP 1  Restrict to forest
  - clip both rasters to the AOI (nearest for the class raster)
  - keep valid (forest) pixels only; forest_area = valid pixel area
  - if forest_area == 0: not applicable ("no forest present to assess for landscape integrity")

STEP 2  Headline score
  - mean_flii = mean(continuous FLII over AOI forest pixels)  # 0-10, one decimal

STEP 3  Distribution
  - for class c in {Low, Medium, High}: area_ha[c] = count(c) * pixel_area_ha
  - pct[c] = area_ha[c] / forest_area * 100  # shares sum to 100 of forest
  - dominant_class = class with largest area; pct_high = pct[High]

STEP 4  Build narrative
  - "Of the forest in this area, {pct_high}% has high landscape integrity, {pct_med}% medium,
     and {pct_low}% low. The forest is predominantly {dominant_class} integrity, {gloss}."
  - gloss by dominant class:
      High   -> "indicating largely intact and well-connected forest under low human pressure"
      Medium -> "indicating moderately modified forest with some fragmentation or human pressure"
      Low    -> "indicating heavily modified and fragmented forest under high human pressure"

STEP 5  Emit
  - mean_flii (big number), distribution table, narrative
  - passed downstream (Triple Win Pillar 1 ecosystem quality; PROTECT vs RESTORE/MANAGE signal)
```

**Example renders (one per predominant class; numbers illustrative but internally consistent):**

Predominantly High:
> Forest landscape integrity: 8.8 / 10
>
> Of the forest in this area, 68% has high landscape integrity, 24% medium, and 8% low. The
> forest is predominantly high integrity, indicating largely intact and well-connected forest
> under low human pressure.

Predominantly Medium:
> Forest landscape integrity: 7.2 / 10
>
> Of the forest in this area, 15% has high landscape integrity, 60% medium, and 25% low. The
> forest is predominantly medium integrity, indicating moderately modified forest with some
> fragmentation or human pressure.

Predominantly Low:
> Forest landscape integrity: 5.0 / 10
>
> Of the forest in this area, 5% has high landscape integrity, 28% medium, and 67% low. The
> forest is predominantly low integrity, indicating heavily modified and fragmented forest under
> high human pressure.

**Downstream use:** FLII is a biodiversity and ecosystem-quality proxy that feeds Triple Win
Pillar 1, and a pathway signal (high integrity favours PROTECT, low integrity favours RESTORE or
MANAGE). It also underpins the SCeNe high-integrity NbS criteria.

### 2.2 Key Biodiversity Areas (KBA)

Reports whether the AOI overlaps Key Biodiversity Areas, with the overlap area and share and a
narrative. KBAs are sites of biodiversity importance, not legal protection.

**Data:** `KBA_polygon.shp` (World Database of Key Biodiversity Areas, BirdLife International and
the KBA Partnership).

**KBA is not a protected area:** a Key Biodiversity Area is a site that contributes significantly
to the global persistence of biodiversity (IUCN KBA Standard 2016). It may or may not be legally
protected. This is a different lens from 1.3 (WDPA, legal status), and the two complement each
other. The narrative emphasises biodiversity importance, not protection.

**Decisions locked:**
- Mirrors 1.3 mechanics: headline overlap = union of KBA polygons (dissolve then intersect), so
  overlapping or nested sites are not double counted; no sliver threshold, because any overlap
  with a KBA is material for biodiversity.
- Denominator = total AOI area (a KBA concerns the whole site, not only its forest).
- The narrative gives the KBA name only (no criteria or type).

**Pseudo-code:**

```
COMPONENT 2.2: KEY BIODIVERSITY AREAS (KBA)
Input: AOI polygon in ANY CRS
       KBA_polygon.shp (World Database of KBAs)
Output: total KBA overlap area (ha) and share (% of AOI)
        per-site list [name, area_ha]; narrative

STEP 0  Normalise CRS
  - Reproject AOI to ESRI:54034 (equal-area). AOI_area_ha = polygon area / 10000

STEP 1  Select sites
  - select KBA sites that intersect the AOI

STEP 2  Headline overlap (union, avoids double count)
  - kba_union = dissolve/union of the selected KBA polygons
  - overlap = intersection(AOI, kba_union)
  - kba_ha = overlap area / 10000
  - kba_pct = kba_ha / AOI_area_ha * 100

STEP 3  Per-site breakdown (for the narrative)
  - for each selected site: site_area_ha = intersection(AOI, site) / 10000
  - sort sites by area descending (dominant first)

STEP 4  Build narrative
  - if kba_ha == 0: "This project area does not overlap any Key Biodiversity Areas."
  - else single vs multiple template, dominant-first, name only, plus the KBA definition sentence

STEP 5  Emit
  - kba_ha, kba_pct, per-site table, narrative
  - passed downstream (Triple Win Pillar 1 biodiversity; safeguard / eligibility signal)
```

**Example renders:**

No overlap:
> This project area does not overlap any Key Biodiversity Areas.

Single site:
> This project area overlaps 210 ha (17%) of a Key Biodiversity Area, Bukit Tigapuluh. Key
> Biodiversity Areas are sites that contribute significantly to the global persistence of
> biodiversity.

Multiple sites:
> This project area overlaps 340 ha (27%) of Key Biodiversity Areas, across 2 sites. The largest
> is Bukit Tigapuluh (210 ha), followed by Kerumutan (130 ha). Key Biodiversity Areas are sites
> that contribute significantly to the global persistence of biodiversity.

**Downstream use:** KBA overlap feeds Triple Win Pillar 1 (biodiversity) and is a safeguard and
eligibility signal. A KBA that is not also under WDPA protection (1.3) is a biodiversity-important
but unprotected site, which is a strong PROTECT and additionality rationale.

<!-- NEXT: 2.3 (awaiting narrative from user) -->

---

## Roadmap (upcoming modules)

- [F02-P2] Site Characterization: Climate
- [F02-P3] Threat Profiles
- [F02-P4] Pathway Recommendation
- [F02-P5] Benefit Quantification

Each module is specified the same way: input, decisions locked, pseudo-code, example render,
downstream use.
