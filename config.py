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
# Ecosystem type (1.1): 1=Dryland, 2=Mangrove, 3=Peatland
ECOSYSTEM_TYPE_RASTER = r"<SET: path to ecosystem_type.tif>"

# Administrative boundaries, GADM v4.1 (1.2)
GADM_L0 = r"<SET: path to GADM level 0 (country) polygons>"
GADM_L1 = r"<SET: path to GADM level 1 (province) polygons>"
GADM_L2 = r"<SET: path to GADM level 2 (district) polygons>"
GADM_COUNTRY_FIELD  = "COUNTRY"   # verify against your GADM (COUNTRY or NAME_0)
GADM_PROVINCE_FIELD = "NAME_1"
GADM_DISTRICT_FIELD = "NAME_2"

# Protected areas, WDPA (1.3)
WDPA_POLYGON = r"<SET: path to WDPA_polygon_4326.shp>"

# Terrain, pre-classified metric rasters (1.4)
SLOPE_CLASS_RASTER     = r"<SET: path to slope_class_metric.tif>"
ELEVATION_CLASS_RASTER = r"<SET: path to elevation_class_metric.tif>"

# Historical deforestation (1.5)
FC2014_RASTER = r"<SET: path to FC2014.tif>"
LC2024_RASTER = r"<SET: path to LC2024.tif>"

# Deforestation risk (1.6)
PROB_RASTER = r"<SET: path to prob.tif>"
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
FLII_CLASS_RASTER  = r"<SET: path to flii_class_mosaic_SEA_300m.tif>"   # 1=Low, 2=Medium, 3=High
FLII_FOREST_RASTER = r"<SET: path to flii_forest_mosaic_SEA_300m.tif>"  # continuous 0-10
FLII_CLASSES = {1: "Low", 2: "Medium", 3: "High"}

# Key Biodiversity Areas (Nature module, 2.2). World Database of KBAs (BirdLife / KBA Partnership).
KBA_POLYGON = r"<SET: path to KBA_polygon.shp>"

# Biomass (Climate module, 3.1). Continuous rasters, DRY BIOMASS DENSITY in Mg/ha, not carbon.
# AGB is the in-house layer (Alpha Earth + GEDI). The tool applies the carbon fraction and the
# CO2 conversion itself, so both conversions stay visible here rather than hidden upstream.
AGB_RASTER = r"<SET: path to agb_mgha.tif>"   # aboveground biomass, Mg/ha
BGB_RASTER = r"<SET: path to bgb_mgha.tif>"   # belowground biomass, Mg/ha

# Soil organic carbon (Climate module, 3.2). Values are CARBON, tC/ha, not biomass and not CO2e.
SOIL_CARBON_RASTER = r"<SET: path to soil_carbon.tif>"   # SOC stock, tC/ha
SOIL_CARBON_DEPTH_CM = 30   # depth the raster represents; label every SOC figure with it

# WorldClim monthly climatology (Climate module, 3.3 and 3.4).
# NOT current climate: v2.1 is a 1970-2000 normal. Every figure derived from it must be labelled
# with the period, because mean temperature in SEA has risen since that window closed.
WORLDCLIM_VERSION    = "2.1"
WORLDCLIM_PERIOD     = "1970-2000"
WORLDCLIM_RESOLUTION = "30s"   # about 1 km at the equator

# Twelve files per variable, in calendar order January to December.
WORLDCLIM_TAVG_RASTERS = [
    rf"<SET: path to wc2.1_30s_tavg_{m:02d}.tif>" for m in range(1, 13)
]   # monthly mean temperature, degrees Celsius
WORLDCLIM_PREC_RASTERS = [
    rf"<SET: path to wc2.1_30s_prec_{m:02d}.tif>" for m in range(1, 13)
]   # monthly precipitation, mm

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

# Interim input, available now: one categorical raster of soil class codes plus a lookup table
# that maps each code to a WRB group name.
SOIL_CLASS_RASTER = r"<SET: path to soil_class.tif>"        # categorical, WRB class codes
SOIL_CLASS_TABLE  = r"<SET: path to soil_class_lookup.csv>" # columns: code, name

# Which input 3.6 uses. "categorical" is the interim path and reports SHARE OF AREA.
# "probability" is the target path and reports MEAN PROBABILITY. The two are different
# quantities, so the component labels whichever it produced rather than calling both "%".
WRB_MODE = "categorical"   # "categorical" or "probability"

WRB_MIN_PROBABILITY_PCT = 1.0   # 3.6 drop groups below this mean probability from the list
WRB_DISPLAY_TOP_N = 5           # 3.6 how many rows the frontend shows before "see the table"
WRB_SUM_TOLERANCE_PCT = 2.0     # 3.6 flag when the group probabilities do not sum to ~100

# ---------------------------------------------------------------------------------------
# Pathway assignment (F02-P4)
# ---------------------------------------------------------------------------------------
# One raster, three bands, produced by the pathway assignment script. See
# "NBS Pathway Assignment Framework" for the decision matrix behind the codes.
PATHWAY_RASTER = r"<SET: path to pathway.tif>"

PATHWAY_BAND           = 1   # primary pathway, exactly one value per pixel
PATHWAY_SECONDARY_BAND = 2   # supporting pathway, same codes, 0 = none
PATHWAY_ECOSYSTEM_BAND = 3   # reference ecosystem, passed through for activity selection

PATHWAY_CODES = {
    0: "No data",
    1: "Protect",
    2: "Manage",
    3: "Restore",
    4: "Carbon ineligible",
    5: "Not eligible for NBS",
}

PROTECT_CODE = 1   # named because F02-P5 selects on it; the other codes are only tabulated

# Codes 1 to 3 are the actual NBS pathways. Codes 4 and 5 are screening outcomes that sit in the
# same band: 4 means non carbon options may still exist, 5 means no NBS option at all.
PATHWAY_ELIGIBLE_CODES = (1, 2, 3)

# Reference ecosystem band. Five classes, unlike the three class ecosystem layer used by 1.1.
# The two are not interchangeable: this one separates grassland and savanna, which is what makes
# the savanna guardrail work at the activity level.
PATHWAY_ECOSYSTEM_CODES = {
    0: "Water or other",
    1: "Dryland forest",
    2: "Mangrove",
    3: "Peatland",
    4: "Grassland or savanna",
}

PATHWAY_UNCLASSIFIED_WARN_PCT = 20.0   # 4.1 flag when this much of the AOI carries no pathway

# ---------------------------------------------------------------------------------------
# Benefit quantification (F02-P5)
# ---------------------------------------------------------------------------------------
# 5.1 reads no new layer. It combines three layers that other components already declare:
# PATHWAY_RASTER (which pixels are Protect), PROB_RASTER (how the projected loss is placed),
# and AGB_RASTER / BGB_RASTER (how much carbon each of those pixels holds).

# The historical rate in 1.5 is measured over 2014 to 2024. Projecting it further than the
# window it was measured in is the largest assumption in the whole calculation, so 5.1 flags a
# project duration above this. VM0048 requires a baseline to be reassessed every six years for
# the same reason. The tool still returns a full figure; it does not truncate.
BASELINE_RATE_MAX_YEARS = 10

# 5.1 flag when the risk layer covers less than this share of the Protect area. Protect pixels
# without a risk value cannot receive projected loss, so they drop out of the estimate.
PROTECT_RISK_COVERAGE_WARN_PCT = 90.0

# Reference ecosystem code (pathway band 3) whose carbon is dominated by a pool 5.1 cannot see.
PATHWAY_ECOSYSTEM_PEATLAND = 3

# The word 5.1 puts in its narrative for each reference ecosystem. Only three of the five band 3
# classes appear, and that is not an omission: prob.tif is forest masked upstream, so Protect
# pixels on grassland or savanna (code 4) and on water or other (code 0) carry no risk value and
# never enter the Protect pool. A pool pixel outside this mapping means the risk layer and the
# ecosystem band disagree about what is forest, which 5.1 raises as a flag.
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
