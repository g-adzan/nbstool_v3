"""
config.py - shared configuration for the NBS screening tool (Backend Analysis).

Single source of truth for the pre-defined layer paths, the reference CRS, class codes, and the
thresholds locked in the design spec (docs/backend_analysis_pseudocode.md). Set every path
marked <SET ...> to your own file before running. This file also serves as the input checklist.
"""

# ============================ REFERENCE CRS ============================
# The AOI is accepted in any CRS and reprojected to this equal-area CRS for all area work.
REFERENCE_CRS = "ESRI:54034"   # World Cylindrical Equal Area (interim, team to finalize)

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
NATIONAL_DEFOR_RATE_CSV = r"<SET: path to national_deforestation_rate.csv>"

# Deforestation risk (1.6)
PROB_RASTER = r"<SET: path to prob.tif>"
NATIONAL_FOREST_RISK_CSV = r"<SET: path to national_forest_risk_reference.csv>"

# Natural disaster hazard, 5-class intensity (1.7)
HAZARD_RASTERS = {
    "landslide":  r"<SET: path to hazard_landslides.tif>",
    "flood":      r"<SET: path to hazard_flood.tif>",
    "flashflood": r"<SET: path to hazard_flashflood.tif>",
    "fire":       r"<SET: path to hazard_fire.tif>",
    "drought":    r"<SET: path to hazard_drought.tif>",
}

# Forest landscape integrity, FLII (Nature module, 2.1). Grantham et al. 2020 concept,
# SEA-calibrated (pooled beta), landscape scale ~300 m, masked to forest.
FLII_CLASS_RASTER  = r"<SET: path to flii_class_mosaic_SEA_300m.tif>"   # 1=Low, 2=Medium, 3=High
FLII_FOREST_RASTER = r"<SET: path to flii_forest_mosaic_SEA_300m.tif>"  # continuous 0-10
FLII_CLASSES = {1: "Low", 2: "Medium", 3: "High"}

# Key Biodiversity Areas (Nature module, 2.2). World Database of KBAs (BirdLife / KBA Partnership).
KBA_POLYGON = r"<SET: path to KBA_polygon.shp>"

# ============================ CLASS CODES AND LABELS ============================
ECOSYSTEM_CLASSES = {1: "Dryland", 2: "Mangrove", 3: "Peatland"}

# LC 2024 forest definition, Tier 1-2 (Scenario 2A), same as the backend
FOREST_CODES = [1, 6, 7, 8, 10]
FC2014_FOREST_CODES = [1]

SLOPE_CLASSES = {1: "Flat", 2: "Gently sloping", 3: "Moderately steep",
                 4: "Steep", 5: "Very steep"}
ELEVATION_CLASSES = {1: "Lowland", 2: "Submontane / hill", 3: "Montane", 4: "Upper montane"}

HAZARD_LEVELS = {1: "Very Low", 2: "Low", 3: "Moderate", 4: "High", 5: "Very High"}

# ============================ THRESHOLDS AND PARAMETERS ============================
ADMIN_SLIVER_PCT   = 1.0            # 1.2 report an admin unit only if >= 1% of the AOI
DEFOR_SIMILAR_BAND = 0.20          # 1.5 within +/- 20% of the national rate reads as "similar"
DEFOR_PERIOD_YEARS = 2024 - 2014   # 1.5 Puyravaud t2 - t1
RISK_HIGHER_PCTL   = 60            # 1.6 above this national percentile is "higher than"
RISK_LOWER_PCTL    = 40            # 1.6 below this national percentile is "lower than"
PROB_SCALE_MAX     = 65535         # 1.6 prob raster UInt16 encodes 0-100 as 0-65535
HAZARD_PRESENCE_PCT = 20           # 1.7 representative level = highest class covering >= this % of AOI
