"""
config.py - shared configuration for the NBS screening tool (Backend Analysis).

Single source of truth for the pre-defined layer paths, the reference CRS, class codes, and the
thresholds locked in the design spec (docs/backend_analysis_pseudocode.md). Set every path
marked <SET ...> to your own file before running. This file also serves as the input checklist.
"""

# ============================ REFERENCE CRS ============================
# The AOI is accepted in any CRS and reprojected to this equal-area CRS for all area work.
REFERENCE_CRS = "ESRI:54034"   # World Cylindrical Equal Area. Locked by the team.

# ============================ PRE-DEFINED LAYERS (placeholders) ============================
# Ecosystem type (1.1): derived from the pathway raster's ecosystem band (band 2), not a separate
# raster. Dryland forest and savanna are merged into one "Dryland" class per the team.
# pathway band-2 code -> Axis 3 class (1 Dryland, 2 Mangrove, 3 Peatland); band-2 0 (none) -> Other.
PATHWAY_ECO_TO_AXIS3 = {1: 1, 4: 1, 2: 2, 3: 3}   # 1 dryland forest & 4 savanna both -> 1 Dryland

# Administrative boundaries (1.2). ONE district-level shapefile carrying GADM-style fields for
# all three levels. 1.2 dissolves it per level to build country / province / district, so no
# separate L0/L1/L2 files are needed.
# NB: dissolve by the NAME columns, NOT the GID columns. In this "(revised)" file GID_1 and GID_2
# are BLANK for Indonesia (the province/district live in NAME_1/NAME_2), so grouping by GID drops
# every Indonesian unit. The ancestor names are included in each level's group so same-named
# units in different parents are not merged.
ADMIN_BOUNDARIES = r"D:\NBSTOOLV3\SEA_Administrative_Boundaries_4326_(revised).shp"
# per level: (columns to group on, name field to display, parent name field or None)
ADMIN_LEVELS = {
    "country":  (["COUNTRY"], "COUNTRY", None),
    "province": (["COUNTRY", "NAME_1"], "NAME_1", "COUNTRY"),
    "district": (["COUNTRY", "NAME_1", "NAME_2"], "NAME_2", "NAME_1"),
}

# Protected areas, WDPA (1.3)
WDPA_POLYGON = r"D:\NBSTOOLV3\WDPA_SEA.shp"   # verify fields: STATUS, MARINE, DESIG_ENG, IUCN_CAT, NAME

# Terrain (1.4). One continuous elevation raster in metres. Slope is DERIVED from it by the tool
# (slope_percent_from_dem), so no separate slope raster is needed. 1.4 bins both itself; the
# inputs are not pre-classified.
ELEVATION_RASTER = r"D:\NBSTOOLV3\SEA_ELEVATION_54034.tif"   # continuous metres
# Upper-exclusive bin edges: digitize(value, breaks) + 1 -> class code.
ELEVATION_BREAKS = [500, 1000, 2000]   # metres  -> elevation classes 1..4
SLOPE_BREAKS     = [8, 15, 25, 40]     # percent -> slope classes 1..5

# Historical deforestation (1.5)
FC2014_RASTER = r"D:\NBSTOOLV3\SEA_FC2014.tif"   # binary 0/1
FC2024_RASTER = r"D:\NBSTOOLV3\SEA_FC2024.tif"   # binary 0/1; forest_mask_2024 reads THIS now
FC2024_FOREST_CODES = [1]
LC2024_RASTER = r"D:\NBSTOOLV3\SEA_LC2024.tif"   # 20-class + 0; kept for reference, not the 2024 mask

# Deforestation risk (1.6)
PROB_RASTER = r"D:\NBSTOOLV3\SEA_DEFRISKS_PROB.tif"   # verify UInt16 0-65535 scale on first run
NATIONAL_FOREST_RISK_CSV = r"<SET: path to national_forest_risk_reference.csv>"

# Natural disaster hazard, 5-class intensity (1.7)
HAZARD_RASTERS = {
    "landslide":  r"<SET: path to hazard_landslides.tif>",
    "flood":      r"<SET: path to hazard_flood.tif>",
    "flashflood": r"<SET: path to hazard_flashflood.tif>",
    "fire":       r"<SET: path to fire_hazard.tif>",
    "drought":    r"<SET: path to hazard_drought.tif>",
}

# Fire susceptibility (Climate module, 3.5). Deliberately an alias, not a second path: 1.7 and
# 3.5 report the same raster in two different ways, so there must be only one path to set. If
# these ever become two layers, split them here and say why in the 3.5 markdown cell.
FIRE_HAZARD_RASTER = HAZARD_RASTERS["fire"]

# Forest landscape integrity, FLII (Nature module, 2.1). Grantham et al. 2020 concept,
# SEA-calibrated (pooled beta), landscape scale ~300 m, masked to forest.
FLII_CLASS_RASTER  = r"D:\NBSTOOLV3\flii_class_mosaic_SEA_300m.tif"   # 1=Low, 2=Medium, 3=High
FLII_FOREST_RASTER = r"D:\NBSTOOLV3\flii_mosaic_SEA_300m.tif"         # continuous 0-10, forest-masked
FLII_CLASSES = {1: "Low", 2: "Medium", 3: "High"}

# Key Biodiversity Areas (Nature module, 2.2). World Database of KBAs (BirdLife / KBA Partnership).
KBA_POLYGON = r"D:\NBSTOOLV3\SouthEast_Asia_KBA.shp"   # name field IntName (2.2 uses it)

# Biomass (Climate module 3.1, Benefit module 5.2). Continuous raster, DRY BIOMASS DENSITY in
# Mg/ha, not carbon. AGB is the in-house layer: GEDI AGBD calibrated with Alpha Earth (AEF). The
# tool applies the carbon fraction and the CO2 conversion itself (CARBON_FRACTION, CO2_PER_C), so
# both conversions stay visible here rather than hidden upstream.
AGB_RASTER = r"D:\NBSTOOLV3\AGBD_GEDI_AEF_pred_SEA_2024.tif"   # aboveground biomass, Mg/ha

# Belowground biomass is DERIVED from AGB by a fixed root-to-shoot ratio, not read from a raster:
#     BGB_Mg/ha = AGB_Mg/ha * ROOT_TO_SHOOT_RATIO
# TEMPORARY stand-in until a mapped BGB layer exists. Consequence to keep in mind: a fixed ratio
# makes BGB a constant multiple of AGB, so any AGB/BGB pool split is constant by construction
# (about 78 / 22 at 0.28) and is NOT a site-specific finding. 3.1 flags this; 5.2 only sums the
# two pools, so it is unaffected. When a mapped BGB raster arrives, set BGB_RASTER below and
# switch 3.1 and 5.2 back to reading it.
ROOT_TO_SHOOT_RATIO = 0.28
# BGB_RASTER = r"<SET: path to bgb_mgha.tif>"   # reinstate when a mapped BGB layer exists

# Soil organic carbon (Climate module, 3.2). Values are CARBON, tC/ha, not biomass and not CO2e.
# Five SoilGrids depth-interval rasters: stock1..5 = 0-5, 5-15, 15-30, 30-60, 60-100 cm.
# 3.2 reports 0-30 cm, so it SUMS the top three (stock1 + stock2 + stock3) per pixel.
SOIL_CARBON_STOCK_RASTERS = [
    rf"D:\NBSTOOLV3\soil_carbon_stock{i}_t_ha.tif" for i in range(1, 6)
]
SOIL_CARBON_0_30_RASTERS = SOIL_CARBON_STOCK_RASTERS[:3]   # 0-5, 5-15, 15-30 cm
SOIL_CARBON_DEPTH_CM = 30   # depth the reported stock represents; label every SOC figure with it

# Monthly climatology (Climate module, 3.3 and 3.4). Each variable is ONE 12-band raster, band
# m = month m (Jan..Dec). Read band by band by _read_monthly_stack.
# VERIFY the source and period of these "_v3" files: the labels below are WorldClim defaults and
# may not match. The period is written into every 3.3/3.4 result, so a wrong label mislabels the
# output.
WORLDCLIM_VERSION    = "v3 (verify source)"
WORLDCLIM_PERIOD     = "verify"
WORLDCLIM_RESOLUTION = "verify"
WORLDCLIM_MONTHS     = 12

WORLDCLIM_TAVG_RASTER = r"D:\NBSTOOLV3\temperature_v3.tif"     # 12-band monthly mean temp, deg C (verify unit)
WORLDCLIM_PREC_RASTER = r"D:\NBSTOOLV3\precipitation_v3.tif"   # 12-band monthly precipitation, mm (verify unit)

MONTH_LABELS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

# 3.3 and 3.4: below this many valid pixels the spatial range is not meaningful, because a
# 30 arc-second grid gives a small AOI only a handful of cells.
CLIMATE_MIN_PIXELS = 5

# ---------------------------------------------------------------------------------------
# Soil classification, WRB 2006 (Climate module, 3.6)
# ---------------------------------------------------------------------------------------
# One raster per WRB reference soil group, holding the modelled probability of that group on a
# 0 to 100 scale. Across all groups the probabilities sum to 100 at every pixel, which is what
# lets the component report a mean probability per group that also sums to 100.
#
# Class names below are the WRB 2006 reference soil groups used by SoilGrids. Note two spellings
# to watch in the UI copy: it is Acrisols, not "Aricsols", and Nitisols, not "Nitsols".
WRB_CLASSES = (
    "Acrisols", "Albeluvisols", "Alisols", "Andosols", "Arenosols", "Calcisols", "Cambisols",
    "Chernozems", "Cryosols", "Durisols", "Ferralsols", "Fluvisols", "Gleysols", "Gypsisols",
    "Histosols", "Kastanozems", "Leptosols", "Lixisols", "Luvisols", "Nitisols", "Phaeozems",
    "Planosols", "Plinthosols", "Podzols", "Regosols", "Solonchaks", "Solonetz", "Stagnosols",
    "Umbrisols", "Vertisols",
)

WRB_PROBABILITY_RASTERS = {
    cls: rf"<SET: path to wrb_{cls.lower()}_probability.tif>" for cls in WRB_CLASSES
}

# Categorical soil raster available: soil_groups.tif, 1 band, values 0-29 (30 classes).
# STILL NEEDED: the code -> WRB name lookup. The raster codes are NOT guaranteed to follow the
# alphabetical WRB_CLASSES order above (SoilGrids uses its own legend order), so the mapping must
# come from the data provider, not be assumed. load_soil_class_table is also still a stub.
SOIL_CLASS_RASTER = r"D:\NBSTOOLV3\soil_groups.tif"          # categorical, 0-29
SOIL_CLASS_TABLE  = r"<SET: code -> WRB name lookup for soil_groups.tif>"

# Which input 3.6 uses. "categorical" is the interim path and reports SHARE OF AREA.
# "probability" is the target path and reports MEAN PROBABILITY. The two are different
# quantities, so the component labels whichever it produced rather than calling both "%".
WRB_MODE = "categorical"   # "categorical" or "probability"

WRB_MIN_PROBABILITY_PCT = 1.0   # 3.6 drop groups below this mean probability from the list
WRB_DISPLAY_TOP_N = 5           # 3.6 how many rows the frontend shows before "see the table"
WRB_SUM_TOLERANCE_PCT = 2.0     # 3.6 flag when the group probabilities do not sum to ~100

# ---------------------------------------------------------------------------------------
# Pathway assignment (F02-P4) - canonical_v3, locked 2026-07-24
# ---------------------------------------------------------------------------------------
# One raster, three bands, produced by nbs_trajectory_pathway_v3.js. This is the v3 band layout
# and it is NOT the v2 layout: v2 band 2 was a secondary pathway and band 3 was the ecosystem.
# v3 drops the secondary pathway entirely, moves the ecosystem to band 2, and puts the 17 class
# category index in band 3. Reading a v2 raster with these constants, or the reverse, silently
# swaps ecosystem and cat_code.
PATHWAY_RASTER = r"D:\NBSTOOLV3\SEA_NBS_PATHWAY.tif"

PATHWAY_BAND           = 1   # primary pathway, exactly one value per pixel
PATHWAY_ECOSYSTEM_BAND = 2   # reference ecosystem, passed through for activity selection
PATHWAY_CATCODE_BAND   = 3   # 1..17 canonical_v3 category index, passed through for activities

# Band 1. Code 5 "Not eligible for NBS" from v2 is GONE: settlement now folds into 4 Ineligible.
# So codes are 0 to 4 only.
PATHWAY_CODES = {
    0: "No data",
    1: "Protect",
    2: "Manage",
    3: "Restore",
    4: "Ineligible",
}

PROTECT_CODE = 1   # named because F02-P5 selects on it; the other codes are only tabulated

# Codes 1 to 3 are the actual NBS pathways. Code 4 is a screening outcome in the same band:
# the site cannot generate carbon credits, though non carbon options may still exist.
PATHWAY_ELIGIBLE_CODES = (1, 2, 3)

# Band 2, reference ecosystem. Four classes plus none. Not the three class layer used by 1.1;
# the two are not interchangeable, this one carries savanna, which is what makes the savanna
# guardrail work at the activity level.
PATHWAY_ECOSYSTEM_CODES = {
    0: "None",
    1: "Dryland forest",
    2: "Mangrove",
    3: "Peatland",
    4: "Savanna",
}

# Band 3, canonical_v3 category index. 17 categories as a clean 1..17 index, 0 mask. This is the
# join key, together with the ecosystem band, into the canonical_v3_activities table (F02-P5).
PATHWAY_CATCODE_LABELS = {
    0: "Mask",
    1: "Cat 1",  2: "Cat 2",  3: "Cat 3A", 4: "Cat 3B", 5: "Cat 4A", 6: "Cat 4B",
    7: "Cat 5",  8: "Cat 6",  9: "Cat 7",  10: "Cat 8A", 11: "Cat 8B", 12: "Cat 8C",
    13: "Cat 9A", 14: "Cat 9B", 15: "Cat 9C", 16: "Cat 9D", 17: "Cat 10",
}

PATHWAY_UNCLASSIFIED_WARN_PCT = 20.0   # 4.1 flag when this much of the AOI carries no pathway

# Primary pathway per canonical_v3 category. Lets 4.2 label the pathway of a category and know
# which categories are Ineligible (pathway 4) and therefore carry no activity by design.
PATHWAY_CATCODE_TO_PATHWAY = {
    1: 1,   # Cat 1  Protect
    2: 4,   # Cat 2  Ineligible
    3: 4,   # Cat 3A Ineligible (savanna)
    4: 3,   # Cat 3B Restore
    5: 4,   # Cat 4A Ineligible (savanna)
    6: 3,   # Cat 4B Restore
    7: 3,   # Cat 5  Restore
    8: 2,   # Cat 6  Manage
    9: 4,   # Cat 7  Ineligible
    10: 4,  # Cat 8A Ineligible (stable natural savanna)
    11: 2,  # Cat 8B Manage
    12: 3,  # Cat 8C Restore
    13: 2,  # Cat 9A Manage
    14: 3,  # Cat 9B Restore
    15: 2,  # Cat 9C Manage
    16: 4,  # Cat 9D Ineligible (settlement)
    17: 3,  # Cat 10 Restore
}

# ---------------------------------------------------------------------------------------
# Activity catalog, canonical_v3_activities (F02-P4, component 4.2)
# ---------------------------------------------------------------------------------------
# The activity + Triple Win benefit + carbon QB layer, joined to the pathway raster on the pair
# (cat_code, ecosystem). Source of truth is the "NBS Pathway Logic" Google Sheet, tab
# canonical_v3_activities; the CSV below is a direct export of it, kept in the repo.
#
# `load_activity_table` reads the Sheet's own headers: `Cat_ID` (1..17, the join key = band 3),
# `Ecosystem` as TEXT (Dryland Forest / Mangrove / Peatland / Savanna, mapped to the band-2
# integer 1..4), `Activity ID`, `Activity`, `Benefit Nature/People/Climate`, and
# `QB Avoided Emissions` / `QB Carbon Sequestration` (Yes/No). The 6 ineligible categories appear
# with a blank Ecosystem and are skipped; 4.2 handles them via PATHWAY_CATCODE_TO_PATHWAY.
# To update, re-export the tab over this file.
ACTIVITY_TABLE = r"C:\Users\carbo\Documents\Claude\Projects\NBS Tool\nbs_screening_tool\canonical_v3_activities.csv"

# ---------------------------------------------------------------------------------------
# Benefit quantification (F02-P5)
# ---------------------------------------------------------------------------------------

# 5.1 General Benefit. The three ASEAN Triple Win pillars, in the order the tool reports them.
# The keys match the three benefit columns of canonical_v3_activities, mapped to the pillar name
# used across the GUI Phase 5 (Triple Win adoption, May 2026). 5.1 collects the benefit phrases
# each activity declares, groups them under these pillars, and merges the duplicates.
TRIPLE_WIN_PILLARS = {
    "benefit_nature":  "Forestry, Ecosystem Health and Biodiversity",
    "benefit_people":  "People and Communities",
    "benefit_climate": "Climate Resilience and Mitigation",
}

# 5.1 reports every benefit that occurs, however small the area behind it, and ranks them by
# supporting area instead of dropping any. This is the denominator warning threshold only: a
# flag, not a filter, when a benefit is carried by less than this share of the AOI.
BENEFIT_SLIVER_WARN_PCT = 1.0

# 5.2 Avoided Emissions from Unplanned Deforestation reads no new layer. It combines three
# layers that other components already declare: PATHWAY_RASTER (which pixels are Protect),
# PROB_RASTER (how the projected loss is placed), and AGB_RASTER + the derived BGB (how much carbon
# each of those pixels holds).

# The historical rate in 1.5 is measured over 2014 to 2024. Projecting it further than the
# window it was measured in is the largest assumption in the whole calculation, so 5.2 flags a
# project duration above this. VM0048 requires a baseline to be reassessed every six years for
# the same reason. The tool still returns a full figure; it does not truncate.
BASELINE_RATE_MAX_YEARS = 10

# 5.2 flag when the risk layer covers less than this share of the Protect area. Protect pixels
# without a risk value cannot receive projected loss, so they drop out of the estimate.
PROTECT_RISK_COVERAGE_WARN_PCT = 90.0

# Reference ecosystem code (pathway band 3) whose carbon is dominated by a pool 5.2 cannot see.
PATHWAY_ECOSYSTEM_PEATLAND = 3

# The word 5.2 puts in its narrative for each reference ecosystem. Only three of the five band 3
# classes appear, and that is not an omission: prob.tif is forest masked upstream, so Protect
# pixels on grassland or savanna (code 4) and on water or other (code 0) carry no risk value and
# never enter the Protect pool. A pool pixel outside this mapping means the risk layer and the
# ecosystem band disagree about what is forest, which 5.2 raises as a flag.
PROTECT_ECOSYSTEM_WORDS = {1: "forest", 2: "mangrove", 3: "peatland"}

# ============================ CLASS CODES AND LABELS ============================
ECOSYSTEM_CLASSES = {1: "Dryland", 2: "Mangrove", 3: "Peatland"}

# LC 2024 forest definition, Tier 1-2 natural forest (Scenario 2A), same as the backend.
# In the 20-class LC 2024 legend: 1 flooded forest, 6 mangrove, 7 deciduous, 8 evergreen,
# 10 mixed forest. Plantation classes (2 rubber, 3 palm, 4 forest plantation, 5 crop
# plantation) are deliberately excluded.
FOREST_CODES = [1, 6, 7, 8, 10]

# FC2014 is a binary product, so this is a raster VALUE (1 = forest), not an LC legend code.
# The Tier 1-2 rule was applied upstream when FC2014 was built, so both dates carry the same
# forest definition.
FC2014_FOREST_CODES = [1]

SLOPE_CLASSES = {1: "Flat", 2: "Gently sloping", 3: "Moderately steep",
                 4: "Steep", 5: "Very steep"}
ELEVATION_CLASSES = {1: "Lowland", 2: "Submontane / hill", 3: "Montane", 4: "Upper montane"}

HAZARD_LEVELS = {1: "Very Low", 2: "Low", 3: "Moderate", 4: "High", 5: "Very High"}

# ============================ THRESHOLDS AND PARAMETERS ============================
ADMIN_SLIVER_PCT   = 1.0            # 1.2 report an admin unit only if >= 1% of the AOI
DEFOR_PERIOD_YEARS = 2024 - 2014   # 1.5 Puyravaud t2 - t1
RISK_HIGHER_PCTL   = 60            # 1.6 above this national percentile is "higher than"
RISK_LOWER_PCTL    = 40            # 1.6 below this national percentile is "lower than"
PROB_SCALE_MAX     = 65535         # 1.6 prob raster UInt16 encodes 0-100 as 0-65535
HAZARD_PRESENCE_PCT = 20           # 1.7 representative level = highest class covering >= this % of AOI

# Carbon conversion (3.1). Both steps are applied in the tool, not upstream.
CARBON_FRACTION = 0.47             # IPCC 2006 GL Vol 4 Ch 4, default carbon fraction of dry matter
CO2_PER_C = 44.0 / 12.0            # molecular weight ratio, tCO2e per tC
CARBON_COVERAGE_WARN_PCT = 90.0    # 3.1 flag when the biomass raster covers less of the AOI

# ============================ RESULT HANDOFF ============================
# Each notebook writes its results here as JSON, and the next notebook reads them back. This is
# the only channel between notebooks, because notebook filenames (for example
# "F02-P2 General.ipynb") are not importable Python module names.
OUTPUT_DIR = r"outputs"

# Stage keys used in the result filenames: <aoi_id>__<stage>.json
STAGE_GENERAL = "F02-P2-general"
STAGE_NATURE  = "F02-P2-nature"
STAGE_CLIMATE = "F02-P2-climate"
STAGE_THREATS = "F02-P3-threats"
STAGE_PATHWAY = "F02-P4-pathway"
STAGE_BENEFIT = "F02-P5-benefit"
