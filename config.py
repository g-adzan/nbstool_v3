"""
config.py - shared configuration for the NBS screening tool (Backend Analysis).

Single source of truth for the pre-defined layer paths, the reference CRS, class codes, and the
thresholds locked in the design spec (docs/backend_analysis_pseudocode.md). Set every path
marked <SET ...> to your own file before running. This file also serves as the input checklist.
"""

# ============================ REFERENCE CRS ============================
# The AOI is accepted in any CRS and reprojected to this equal-area CRS for all area work.
from pathlib import Path


REFERENCE_CRS = "ESRI:54034"   # World Cylindrical Equal Area. Locked by the team.

# ============================ AOI (change it HERE, one place) ============================
# To switch AOI: edit these two lines, then RESTART every notebook kernel (config is cached at
# import). Every notebook reads AOI_PATH and AOI_ID from here; do not hardcode them per notebook.
# AOI_ID also names the per-AOI output subfolder and the stage-handoff filenames, so results for
# different AOIs never mix.
AOI_PATH = r"D:\NBSTOOLV3\AOI1.shp"
AOI_ID   = "aoi1"

# ============================ OUTPUTS (per AOI) ============================
# Everything a run writes goes under OUTPUT_ROOT\<AOI_ID>: the JSON stage handoff in the folder
# itself, and saved output rasters under a rasters\ subfolder. Switching AOI_ID above points all
# of this at a fresh folder automatically.
OUTPUT_ROOT       = r"D:\NBSTOOLV3\OUTPUTS"
OUTPUT_DIR        = rf"{OUTPUT_ROOT}\{AOI_ID}"            # JSON stage handoff files
RASTER_OUTPUT_DIR = rf"{OUTPUT_ROOT}\{AOI_ID}\rasters"   # saved output GeoTIFFs, one per section
CSV_OUTPUT_DIR    = rf"{OUTPUT_ROOT}\{AOI_ID}\tables"    # saved output tables as CSV, one per table

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
LC2024_RASTER = r"D:\NBSTOOLV3\SEA_LC2024.tif"   # 20-class + 0; used by 1.8 Land Cover (not the 2024 mask)

# LC 2024 legend (RLCMS, 20 classes; 0 = no data). Names from the "Class Mapping" sheet of the
# NBS Pathway Logic workbook. Used by 1.8 Land Cover.
LC2024_CLASSES = {
    1: "Flooded forest", 2: "Rubber", 3: "Palm", 4: "Plantation", 5: "Crop plantation",
    6: "Mangrove", 7: "Deciduous Forest", 8: "Evergreen Forest", 9: "Shrubland", 10: "Mixed forest",
    11: "Snow", 12: "Water", 13: "Aquaculture", 14: "Rice", 15: "Building", 16: "Cropland",
    17: "Grassland", 18: "Wetland", 19: "Bareland", 20: "Other land",
}
LC_TOP_N = 6   # 1.8 subset table: the N largest land cover classes

# Deforestation risk (1.6)
PROB_RASTER = r"D:\NBSTOOLV3\SEA_DEFRISKS_PROB.tif"   # verify UInt16 0-65535 scale on first run
# Per-country percentile breakpoints of prob.tif over that country's forest, 0-100 scale.
# CSV columns: country, p10, p20, p30, p40, p50, p60, p70, p80, p90.
# If the file is missing or a country is absent, 1.6 reports "no national reference" (no crash).
NATIONAL_FOREST_RISK_CSV = r"D:\NBSTOOLV3\national_forest_risk_reference.csv"

# Natural disaster hazard, 5-class intensity (1.7). Files in D:\NBSTOOLV3\disaster_risks.
# That folder also has hazard_cyclone.tif and hazard_storm.tif; deliberately NOT wired,
# the team keeps 1.7 to these five hazards.
HAZARD_DIR = r"D:\NBSTOOLV3\disaster_risks"
HAZARD_RASTERS = {
    "landslide":  rf"{HAZARD_DIR}\hazard_landslides.tif", #assets-geo/v3/risk_landslide_v3.tif
    "flood":      rf"{HAZARD_DIR}\hazard_flood.tif", #assets-geo/v3/risk_flood_v3.tif
    "flashflood": rf"{HAZARD_DIR}\hazard_flashflood.tif", #assets-geo/v3/risk_flashflood_v3.tif
    "fire":       rf"{HAZARD_DIR}\hazard_fire.tif", #assets-geo/v3/risk_fire_v3.tif
    "drought":    rf"{HAZARD_DIR}\hazard_drought.tif", #assets-geo/v3/risk_drought_v3.tif
}

# Fire susceptibility (Climate module, 3.5). Deliberately an alias, not a second path: 1.7 and
# 3.5 report the same raster in two different ways, so there must be only one path to set. If
# these ever become two layers, split them here and say why in the 3.5 markdown cell.
# NOTE: 1.7 has moved to the RISK_RASTERS layers below; 3.5 still reads this old fire hazard file
# and will be reconciled when 3.5 is rebuilt. So 1.7 and 3.5 no longer read the same fire raster.
FIRE_HAZARD_RASTER = HAZARD_RASTERS["fire"]

# Natural disaster RISK, 4-class level (1.7 Natural Disaster Risks). Pre-classified risk rasters
# in D:\NBSTOOLV3 (risk_*.tif). These are true risk layers: exposure and vulnerability are already
# folded in upstream, so 1.7 reports risk, not bare hazard. Values are 1..4 with 0 as nodata.
# The five layers sit at very different native resolutions (flood, landslide ~100 m; fire ~1 km;
# cyclone ~11 km; drought ~28 km), so a small AOI may fall in one coarse cell for cyclone/drought,
# giving a single-class distribution. That is expected, not an error.
RISK_DIR = r"D:\NBSTOOLV3"
RISK_RASTERS = {
    "cyclone":   rf"{RISK_DIR}\risk_cyclone.tif",
    "drought":   rf"{RISK_DIR}\risk_drought.tif",
    "fire":      rf"{RISK_DIR}\risk_fire.tif",
    "flood":     rf"{RISK_DIR}\risk_flood.tif",
    "landslide": rf"{RISK_DIR}\risk_landslide.tif",
}
RISK_LEVELS = {1: "Very Low", 2: "Low", 3: "Moderate", 4: "High"}
RISK_PRESENCE_PCT = 20   # 1.7 representative level = highest class covering >= this % of AOI area

# Historical burned area, GABAM annual burned maps (Climate 3.7). One binary raster per year in
# D:\NBSTOOLV3\MOSAIC_2, named GABAM_<year>.tif, value 1 = burned and 0 = nodata, ~30 m, EPSG:4326.
# A pixel can burn in more than one year, so 3.7 reports the union (area burned at least once) as
# the headline and the per-year areas as a bar chart. GABAM_RASTER_TEMPLATE keeps a literal
# {year} placeholder, filled per year with .format(year=...).
GABAM_DIR = r"D:\NBSTOOLV3\MOSAIC_2"
GABAM_YEARS = list(range(2014, 2025))          # 2014..2024 inclusive, the years present in MOSAIC_2
GABAM_RASTER_TEMPLATE = GABAM_DIR + r"\GABAM_{year}.tif"

# Forest landscape integrity, FLII (Nature module, 2.1). Grantham et al. 2020 concept,
# SEA-calibrated (pooled beta), landscape scale ~300 m, masked to forest.
FLII_CLASS_RASTER  = r"D:\NBSTOOLV3\flii_class_mosaic_SEA_300m.tif"   # 1=Low, 2=Medium, 3=High
FLII_FOREST_RASTER = r"D:\NBSTOOLV3\flii_mosaic_SEA_300m.tif"         # continuous 0-10, forest-masked
FLII_CLASSES = {1: "Low", 2: "Medium", 3: "High"}

# Key Biodiversity Areas (Nature module, 2.2). World Database of KBAs (BirdLife / KBA Partnership).
KBA_POLYGON = r"D:\NBSTOOLV3\SouthEast_Asia_KBA.shp"   # name field IntName (2.2 uses it)

# NatureMap priority ranks (Nature module 2.6). Ranked global-priority rasters from Jung et al.
# (2021), not raw biodiversity, carbon, or water stocks. Native resolution is 10 km
# (100 km² per pixel), suitable for landscape-context analysis rather than site-level estimates.
NATUREMAP_LAYERS = {
    "Biodiversity": "Z:\Biodiversity\biodiversity_only_v3.tif", #assets-geo/v3/biodiversity_only_v3.tif
    "Carbon":       "Z:\Biodiversity\biodiversity_carbon_v3.tif", #assets-geo/v3/biodiversity_carbon_v3.tif
    "Water":        "Z:\Biodiversity\biodiversity_water_v3.tif", #assets-geo/v3/biodiversity_water_v3.tif
}



# Biodiversity habitat intersection (Nature module 2.3). Species habitat rasters are filtered using
# the master GeoParquet footprint, then DN = 1 pixels inside the AOI are counted to calculate habitat
# area and % of AOI.
USER_POLYGON = r"Z:\NbS_Tools\Dummy\AOI2_4326.shp"

BIODIVERSITY_ROOT = (
    r"\\OPENMEDIAVAULT\geospatial\NBSTOOLV3\BIODIVERSITY\habitat_area" #assets-geo/v3/habitat_area
)

INVENTORY_PATH = (
    r"\\OPENMEDIAVAULT\geospatial\NBSTOOLV3\BIODIVERSITY\habitat_area\species_iucn_v3.geoparquet" #assets-geo/v3/habitat_area/species_iucn_v3.geoparquet
)

TARGET_DN = 1
GEOD_ELLPS = "WGS84"

# Key species presence (Nature module 2.5). GBIF occurrence points are intersected with the AOI,
# then summarised by species using record count, individual count, latest event date, and the most
# frequent Darwin Core basisOfRecord value.
KEY_SPECIES_POINTS = (
    r"\\OPENMEDIAVAULT\geospatial\NBSTOOLV3\BIODIVERSITY\GBIF\key_species.shp" #Postgis Database: nbs/sea/key_species
)

KEY_SPECIES_USER_POLYGON = r"Z:\NbS_Tools\Dummy\AOI_4326.shp" #user input

KEY_SPECIES_OUTPUT = (
    r"\\OPENMEDIAVAULT\geospatial\NBS\AoH\temp_pilot"
    r"\species_occurrence_summary.xlsx"
)

KEY_SPECIES_COLUMN = "species"
KEY_SPECIES_COUNT_COLUMN = "individualCount"
KEY_SPECIES_DATE_COLUMN = "eventDate"
KEY_SPECIES_BASIS_COLUMN = "basisOfRecord"

# "intersects" includes occurrence points on the AOI boundary.
KEY_SPECIES_SPATIAL_PREDICATE = "intersects"

# -----------------------------------------------------------------------------
# People data (F02-P2), seven pre-defined local rasters
# -----------------------------------------------------------------------------
POP_TOTAL_RASTER = r"D:\3_project\nbstool_v3\dataset\gridded_population_v3.tif" #assets-geo/v3/gridded_population_v3.tif
POP_FEMALE_RASTER = r"D:\3_project\nbstool_v3\dataset\female_pop_v3.tif" #assets-geo/v3/female_pop_v3.tif
POP_MALE_RASTER = r"D:\3_project\nbstool_v3\dataset\male_pop_v3.tif" #assets-geo/v3/male_pop_v3.tif
PEOPLE_VULNERABILITY_RASTERS = {
    "physical": r"D:\3_project\nbstool_v3\dataset\vulnerability_physical_v3.tif", #assets-geo/v3/vulnerability_physical_v3.tif
    "environmental": r"D:\3_project\nbstool_v3\dataset\vulnerability_natural_v3.tif", #assets-geo/v3/vulnerability_natural_v3.tif
    "economic": r"D:\3_project\nbstool_v3\dataset\vulnerability_economic_v3.tif", #assets-geo/v3/vulnerability_economic_v3.tif
    "social": r"D:\3_project\nbstool_v3\dataset\vulnerability_social_v3.tif", #assets-geo/v3/vulnerability_social_v3.tif
}
PEOPLE_VULNERABILITY_LEVELS = {
    1: "Very Low",
    2: "Low",
    3: "Moderate",
    4: "High",
    5: "Very High",
}
PEOPLE_AGE_GROUPS = {
    "0-4": (1, 2),
    "5-9": (3,),
    "10-14": (4,),
    "15-19": (5,),
    "20-24": (6,),
    "25-29": (7,),
    "30-34": (8,),
    "35-39": (9,),
    "40-44": (10,),
    "45-49": (11,),
    "50-54": (12,),
    "55-59": (13,),
    "60-64": (14,),
    "65+": (15, 16, 17, 18, 19, 20),
}

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
# Threat assignment (F02-P3) - locked 2026-07-24
# ---------------------------------------------------------------------------------------
# Forest degradation screening (Threat module). Structural decline is assessed from canopy-height
# deficit relative to an undisturbed reference population >=120 m from disturbed forest. Thresholds
# represent relative/absolute height loss and severe degradation signals; results are intended for
# area-level reporting rather than per-pixel interpretation at 30 m resolution.
USER_AOI = r"Z:\NbS_Tools\Dummy\AOI2_4326.shp"

ECOSYSTEM = (
    r"\\OPENMEDIAVAULT\geospatial\NBSTOOLV3\FOREST DEGRADATION" #assets-geo/v3/ecosystem_v3.tif
)

DISTURBANCE = (
    r"\\OPENMEDIAVAULT\geospatial\NBSTOOLV3\FOREST DEGRADATION" #assets-geo/v3/forest_disturbance_v3.tif
)

ECOSYSTEM_CLASSES = {
    1: "Dryland forest",
    2: "Mangrove",
    3: "Peatland",
    4: "Other",
}

DISTURBANCE_RULE = "greater_than_zero"
GEOD_ELLPS = "WGS84"

# =============================================================================
# Dryland Forest Disturbance
# =============================================================================
# Threat datasets
DATA = Path(
    r"\\OPENMEDIAVAULT\geospatial\NBSTOOLV3\Testing_folder\Threat"
)

ECOSYSTEM = DATA / "ecosystem_v3.tif" #assets-geo/v3/threat/ecosystem_v3.tif
HISTORICAL = DATA / "historical_deforestation_v3.tif" #assets-geo/v3/threat/historical_deforestation_v3.tif
FOREST_2024 = DATA / "forest_2024_v3.tif" #assets-geo/v3/threat/forest_2024_v3.tif
DISTURBANCE = DATA / "forest_disturbance_v3.tif" #assets-geo/v3/threat/forest_disturbance_v3.tif
FOREST_GAIN = DATA / "forest_gain_v3.tif" #assets-geo/v3/threat/forest_gain_v3.tif
FOREST_DRIVERS = DATA / "drivers_disturbance_v3.tif" #assets-geo/v3/threat/drivers_disturbance_v3.tif

# Additional driver/risk rasters
DRIVERS_DISTURBANCE = DATA / "drivers_disturbance_v3.tif" #assets-geo/v3/threat/drivers_disturbance_v3.tif
FLOOD_RISK = DATA / "risk_flood_v3.tif" #assets-geo/v3/threat/risk_flood_v3.tif
LANDSLIDE_RISK = DATA / "risk_landslide_v3.tif" #assets-geo/v3/threat/risk_landslide_v3.tif
STORM_RISK = DATA / "risk_storm_v3.tif" #assets-geo/v3/threat/risk_storm_v3.tif

DRYLAND = 1

REMAINING_FOREST = 1
FOREST_LOSS = 2

CURRENT_FOREST = 1
FOREST_GAIN_VALUE = 1

FOREST_DRIVER_CLASSES = {
    1: "Small-scale agriculture",
    2: "Small-scale agriculture (fire)",
    3: "Large-scale agriculture",
    4: "Large-scale agriculture (fire)",
    5: "Road development",
    6: "Selective logging",
    7: "Mining",
    8: "Non-productive conversion",
}

# Disaster risk. The values are the raster values that indicate a risk e.g., 4 and 5 except forest_fire
NATURAL_DRIVERS = {
    "Flooding": {
        "raster": FLOOD_RISK,
        "values": [4]
    },
    "Forest fire": {
        "raster": DRIVERS_DISTURBANCE,
        "values": [10]
    },
    "Landslide": {
        "raster": LANDSLIDE_RISK,
        "values": [4]
    },
    "Extreme climate event": {
        "raster": STORM_RISK,
        "values": [4]
    }
}


# =============================================================================
# Mangrove Disturbance
# =============================================================================

USER_AOI = Path(
    r"Z:\NbS_Tools\Dummy\AOI5_4326.shp"
)

DATA_DIR = Path(
    r"\\OPENMEDIAVAULT\geospatial\NBSTOOLV3\Testing_folder\Threat"
)

ECOSYSTEM = DATA_DIR / "ecosystem_v3.tif" #assets-geo/v3/threat/ecosystem_v3.tif
HISTORICAL = DATA_DIR / "historical_deforestation_v3.tif" #assets-geo/v3/threat/historical_deforestation_v3.tif
FOREST_2024 = DATA_DIR / "forest_2024_v3.tif" #assets-geo/v3/threat/forest_2024_v3.tif
DISTURBANCE = DATA_DIR / "forest_disturbance_v3.tif" #assets-geo/v3/threat/forest_disturbance_v3.tif
DRIVERS = DATA_DIR / "drivers_disturbance_v3.tif" #assets-geo/v3/threat/drivers_disturbance_v3.tif
STORM_RISK = DATA_DIR / "risk_storm_v3.tif" #assets-geo/v3/threat/risk_storm_v3.tif

# PIXEL CLASSES ===========================================================

# ecosystem_v3.tif
MANGROVE_CLASS = 2

# historical_deforestation_v3.tif
REMAINING_FOREST_CLASS = 1

# forest_2024_v3.tif
CURRENT_FOREST_CLASS = 1

# forest_disturbance_v3.tif
# Any value > 0 = disturbed
DISTURBANCE_THRESHOLD = 0

# drivers_disturbance_v3.tif
COMMODITY_CLASSES = [1, 2, 3, 4]
SETTLEMENT_CLASS = 5

# risk_storm_v3.tif
STORM_RISK_CLASSES = [4, 5]

# =============================================================================
# Peatland Disturbance
# =============================================================================

USER_AOI = Path(
    r"Z:\NbS_Tools\Dummy\AOI6_4326.shp"
)

DATA = Path(
    r"\\OPENMEDIAVAULT\geospatial\NBSTOOLV3\Testing_folder\Threat"
)

PEAT_CANALS_DENSITY = DATA / "peat_canals_density_v3.tif"
FIRE_RISK = DATA / "risk_fire_v3.tif"

DRAINAGE_CANALS = DATA / "peat_canal.tif"



# PIXEL CLASSES ============================================================
# ecosystem_v3.tif
PEATLAND = 3

# historical_deforestation_v3.tif
REMAINING_FOREST = 1
FOREST_LOSS = 2

# forest_2024_v3.tif
CURRENT_FOREST = 1

# forest_disturbance_v3.tif
# Any value > 0 = disturbed
DISTURBANCE_THRESHOLD = 0

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
RESTORE_CODE = 3   # named because 5.3 selects Restore pixels on it

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
ACTIVITY_TABLE = r"D:\NBSTOOLV3\canonical_v3_activities.csv"

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

# ---------------------------------------------------------------------------------------
# ARR carbon sequestration (Benefit module 5.3), per NBS-v3-ANX-B v2 (2026-07-28)
# ---------------------------------------------------------------------------------------
# Reference-rate / yield-curve method: accumulate living biomass (AGB + BGB) on a restoring
# stand over the project years, deduct the biomass already on site, scale by a stocking factor,
# convert to tCO2e. Rates and parameters are from ANX-B Section 4; that doc carries the sources
# and confidence levels. Biomass ONLY: no soil, no peat soil, no avoided emissions, no dead wood
# or litter. This is an ex-ante, pre-feasibility estimate, not project-grade MRV.

# Which (cat_code, ecosystem) pairs get carbon quantified. Encodes ANX-B Section 3.2
# "Sequestration calculated", keyed on the pathway raster's band-3 cat_code and band-2 ecosystem.
# Deliberately NOT the sheet's QB Carbon Sequestration flag: the sheet currently contradicts the
# method on peat (sheet No, method Yes biomass-only) and savanna (sheet Yes, method defers), and
# is flagged for reconciliation. Savanna (eco 4) is absent here = deferred; Cat 9B peat (14, 3)
# is absent = rewetting only, no planting.
ARR_SEQ_PAIRS = frozenset({
    (4, 1), (4, 2), (4, 3),     # Cat 3B  dryland, mangrove, peat
    (6, 1), (6, 2), (6, 3),     # Cat 4B
    (7, 1), (7, 2), (7, 3),     # Cat 5   (savanna 7,4 excluded)
    (12, 1), (12, 2), (12, 3),  # Cat 8C
    (14, 2),                    # Cat 9B  mangrove only (peat 14,3 is rewetting only)
    (17, 1), (17, 2), (17, 3),  # Cat 10  (savanna 17,4 excluded)
})

# Growth phases, ANX-B Section 4.4. Young Y1-20, Old Y21-40. The curve is defined only to Y40;
# beyond that no further accumulation is credited.
ARR_YOUNG_END_YEAR = 20
ARR_OLD_END_YEAR = 40

# Reference accumulation rates, Mg DRY MATTER per ha per year, ANX-B Section 4.6. Mangrove and
# peatland use one rate each; dryland is split into three zones, derived per pixel (below).
ARR_RATE_DM = {                        # non-dryland ecosystems, keyed on ecosystem code
    2: {"young": 12.0, "old": 7.0},    # mangrove
    3: {"young": 5.7, "old": 3.5},     # peatland, biomass only
}
ARR_RATE_DM_DRYLAND = {                # dryland, keyed on zone code (see ARR_DRYLAND_ZONES)
    1: {"young": 3.4, "old": 2.7},     # humid lowland (rainforest)
    2: {"young": 2.4, "old": 2.0},     # seasonal lowland (conservative, wide range)
    3: {"young": 2.4, "old": 1.9},     # humid montane
}

# Root-to-shoot ratio R (BGB / AGB), ANX-B Section 4.7, low-biomass classes.
ARR_ROOT_TO_SHOOT = {2: 0.39, 3: 0.25}                    # mangrove, peat
ARR_ROOT_TO_SHOOT_DRYLAND = {1: 0.21, 2: 0.44, 3: 0.32}   # humid lowland, seasonal, montane

# Dryland zone derivation, ANX-B Section 4.5. Derived per pixel from elevation (metres,
# ELEVATION_RASTER) and the 12-band monthly precipitation raster (WORLDCLIM_PREC_RASTER). A month
# below ARR_ZONE_DRY_MONTH_MM counts as a dry month (Walsh 1996, tropical dry-season standard).
# Rule: humid montane if elevation above 1000 m; else humid lowland if annual rainfall above
# 2000 mm AND fewer than 3 dry months; else seasonal lowland. Boundary and missing-data pixels
# fall to seasonal lowland, the lower-productivity zone, for a conservative estimate.
ARR_DRYLAND_ZONES = {1: "humid lowland", 2: "seasonal lowland", 3: "humid montane"}
ARR_ZONE_ELEV_MONTANE_M = 1000.0
ARR_ZONE_WET_ANNUAL_MM = 2000.0
ARR_ZONE_DRY_MONTH_MM = 100.0
ARR_ZONE_DRY_SEASON_MONTHS = 3
ARR_DRYLAND_DEFAULT_ZONE = 2   # seasonal lowland, used when zone inputs are missing

# Baseline mode for the primary 5.3 result (team decision, 2026-07-29):
#   "class"         - small assumed standing biomass per current LC state (ARR_BASELINE_CLASS_MGHA).
#                     This is the OFFICIAL mode. It matches the "small but non-zero" baseline the
#                     doc's Section 4.8 assumes for degraded classes, and avoids the GEDI problem.
#   "per_pixel_agb" - the per-pixel AGB raster baseline. Kept as a diagnostic only: on vegetated
#                     Restore land GEDI reads a high baseline (Section 4.9) and zeroes the result.
#   "none"          - no baseline deduction (gross). Upper-bound scenario.
# Whatever the mode, 5.3 reports all three totals in `values` for comparison.
ARR_BASELINE_MODE = "class"

# Small class-based baseline, AGB Mg/ha per current LC state. VALUES ARE PLACEHOLDERS pending
# literature references (team is sourcing them); the number scales with these, so treat the
# result as indicative until they are set. They are not from the doc.
ARR_BASELINE_CLASS_MGHA = {"C4": 25.0, "C5": 5.0, "C6": 0.0}   # AGB Mg/ha per current LC state
ARR_RESTORE_CAT_CSTATE = {                                     # Restore cat_code -> current state
    4: "C4",   # Cat 3B  Forest -> shrub / vegetation
    6: "C5",   # Cat 4B  Forest -> active use
    7: "C6",   # Cat 5   Forest -> barren
    12: "C4",  # Cat 8C  Non-forest -> vegetation
    14: "C5",  # Cat 9B  Non-forest -> active use
    17: "C6",  # Cat 10  Non-forest -> barren
}

# Carbon fraction, dry matter to carbon, ANX-B Section 4.6. Mangrove 0.451, others 0.47.
ARR_CARBON_FRACTION = {1: 0.47, 2: 0.451, 3: 0.47}

# Stocking factor, ANX-B Section 4.9. Active planting reaches full stocking; ANR and mangrove EMR
# rely on natural recruitment. The 0.8 for ANR/EMR is UNCALIBRATED (doc range 0.7 to 0.85, open
# item). ARR_ANR_PAIRS lists the (cat_code, ecosystem) whose activity is ANR or mangrove EMR:
# 3B dryland is literally ANR, and the ARR method treats Cat 4B/5/8C/10 mangrove as EMR. All
# other pairs are treated as planting. The split itself is uncalibrated and flagged.
ARR_STOCKING_PLANTING = 1.0
ARR_STOCKING_ANR = 0.8
ARR_ANR_PAIRS = frozenset({(4, 1), (6, 2), (7, 2), (12, 2), (17, 2)})

# Uncertainty band, ANX-B Section 4.11. Indicative screening range, NOT a confidence interval.
ARR_UNCERTAINTY_LOW = 0.7
ARR_UNCERTAINTY_HIGH = 1.2

# Ecosystem codes whose ARR carbon is NOT quantified: the activity and benefits still apply, but
# no carbon number is produced. 5.3 skips any (cat_code, ecosystem) in ARR_SEQ_PAIRS whose
# ecosystem is listed here, and reports the area as deferred instead.
#   4 savanna    : methodological deferral. Savanna stores carbon mainly in soil and roots,
#                  outside the biomass scope, and has no biomass rates.
#   3 peatland   : TEMPORARY exclusion (team decision, 2026-07-29). The biomass method and the
#                  peat rates exist and work; peat is held out for now. Remove 3 from this set to
#                  re-enable peat biomass quantification (it is flagged biomass-only, since peat
#                  soil and avoided emissions are out of scope).
ARR_CARBON_DEFERRED_ECO = frozenset({3, 4})

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
# Each notebook writes its results as JSON to OUTPUT_DIR (the per-AOI folder set above), and the
# next notebook reads them back. This is the only channel between notebooks, because notebook
# filenames (for example "F02-P2 General.ipynb") are not importable Python module names.
# common.save_results creates the folder if it does not exist.

# Stage keys used in the result filenames: <aoi_id>__<stage>.json
STAGE_GENERAL = "F02-P2-general"
STAGE_NATURE  = "F02-P2-nature"
STAGE_CLIMATE = "F02-P2-climate"
STAGE_THREATS = "F02-P3-threats"
STAGE_PATHWAY = "F02-P4-pathway"
STAGE_BENEFIT = "F02-P5-benefit"

# ---------------------------------------------------------------------------------------
# Enhanced Biodiversity and Ecosystem Function (Benefit module 5.4)
# ---------------------------------------------------------------------------------------

PROJECT_DURATION = 30
RATE_PCT = 1.5              # dummy annual deforestation rate
ECOSYSTEM_CLASS = 1         # 1 Forest, 2 Mangrove, 3 Peatland

DATA = Path(r"\\OPENMEDIAVAULT\geospatial\NBSTOOLV3")

ECOSYSTEM = DATA / "Testing_folder/Threat/ecosystem_v3.tif"
DEF_RISK = DATA / "DEFORESTATION_RISKS/prob_mosaic_SEA.tif"
HABITAT_ROOT = DATA / "BIODIVERSITY/habitat_area"

HABITAT_FOLDERS = [
    HABITAT_ROOT / x
    for x in ["Mammal", "Bird", "Reptile", "Amphibian"]
]

ECOSYSTEM_NAMES = {
    1: "forest",
    2: "mangrove",
    3: "peatland"
}

