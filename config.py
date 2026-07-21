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
