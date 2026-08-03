"""
common.py - shared building blocks for the NBS screening tool.

Everything that more than one component needs lives here: the AOI contract, the data access
stubs, zonal tabulation, the shared forest 2024 mask, and the small text helpers used to build
narratives.

NOT RUNNABLE. The functions in the "Data access stubs" section raise NotImplementedError on
purpose. They are the only place where files are touched. All analysis logic in the component
modules is real Python and reads from these stubs, so wiring the tool up later means filling
four functions, not rewriting the analysis.

Design contract
---------------
1. The AOI is accepted in any CRS. `prepare_aoi` reprojects it once to REFERENCE_CRS
   (ESRI:54034, equal area) and every component works on that object. No component reprojects
   the AOI again.
2. `AOI.area_ha` is the authoritative denominator for any share that is "share of the site".
   Components that use a different denominator (valid pixels, forest only) say so explicitly.
3. Rasters are read through `load_raster_clipped`, which returns a masked array already aligned
   to the AOI plus the pixel area. In an equal area CRS the pixel area is a constant, so area
   is always pixel_count * pixel_area_ha.
4. Components never return raw arrays to the frontend. Arrays that a later component needs
   (the forest 2024 mask) are produced by a shared function here, not passed between results.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Iterable, Sequence

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from affine import Affine
from rasterio.features import geometry_mask
from rasterio.warp import Resampling, calculate_default_transform, reproject

# Resampling names the components pass, mapped to rasterio. nearest for categorical layers and
# any layer whose min or max is reported; average for stock and probability; bilinear for a
# continuous layer read only for its mean (the FLII score in 2.1).
_RESAMPLING = {
    "nearest": Resampling.nearest,
    "bilinear": Resampling.bilinear,
    "average": Resampling.average,
}

from config import (
    FC2014_RASTER,
    FC2014_FOREST_CODES,
    FC2024_RASTER,
    FC2024_FOREST_CODES,
    CSV_OUTPUT_DIR,
    OUTPUT_DIR,
    RASTER_OUTPUT_DIR,
    REFERENCE_CRS,
)

M2_PER_HA = 10_000.0


# ============================ AOI CONTRACT ============================


@dataclass(frozen=True)
class AOI:
    """The project area, already in REFERENCE_CRS.

    Attributes
    ----------
    geometry : single polygon or multipolygon in REFERENCE_CRS.
    area_ha  : total site area. Authoritative denominator for "share of the site".
    source_crs : the CRS the user supplied, kept for reporting only.
    """

    geometry: gpd.GeoSeries
    area_ha: float
    source_crs: str


def prepare_aoi(aoi_any_crs: gpd.GeoDataFrame | gpd.GeoSeries) -> AOI:
    """Normalise the AOI once, at the entry point of the tool.

    Accepts any CRS, reprojects to REFERENCE_CRS, dissolves multi part input into one geometry
    so that area is counted once, and measures the total area.
    """
    geoms = aoi_any_crs.geometry if isinstance(aoi_any_crs, gpd.GeoDataFrame) else aoi_any_crs
    source_crs = str(geoms.crs)

    if geoms.crs is None:
        raise ValueError("AOI has no CRS. The tool cannot measure area without one.")

    geoms = geoms.to_crs(REFERENCE_CRS)
    dissolved = gpd.GeoSeries([geoms.union_all()], crs=REFERENCE_CRS)
    area_ha = float(dissolved.area.sum()) / M2_PER_HA

    if area_ha <= 0:
        raise ValueError("AOI has zero area after reprojection.")

    return AOI(geometry=dissolved, area_ha=area_ha, source_crs=source_crs)


# ============================ DATA ACCESS STUBS ============================
# The only file touching code in the tool. Fill these to make the tool runnable.
#
# These four functions are also where the remaining dependencies enter. Nothing else in the
# tool needs them, which is why `import rasterio` and `import pandas` do not appear above yet:
#
#   load_raster_clipped              rasterio, rasterio.mask, rasterio.warp
#   load_vector_intersecting         geopandas (already imported)
#   load_soil_class_table            pandas
#   load_national_forest_risk_percentiles   pandas
#
# All of them are already declared in environment.yml, so filling the stubs needs no change to
# the environment. Add the imports at the top of this file when you implement them.
#
# Resampling values passed by the components, and why each one is used:
#   "nearest"   categorical rasters, and any layer whose minimum or maximum is reported, so the
#               reported values exist in the source instead of being interpolation artefacts
#   "average"   stock and probability layers, where reprojection must preserve the area
#               weighted mean
#   "bilinear"  continuous layers read only for their mean, currently the FLII score in 2.1


@dataclass(frozen=True)
class RasterSlice:
    """A raster clipped and reprojected to the AOI in REFERENCE_CRS.

    values : masked float array. Masked cells are nodata or outside the AOI polygon.
    pixel_area_ha : constant, because REFERENCE_CRS is equal area.
    transform, crs : the destination grid, so another load can be forced onto it with `like`.
    """

    values: np.ma.MaskedArray
    pixel_area_ha: float
    transform: object = None   # affine.Affine of the destination grid
    crs: object = None         # REFERENCE_CRS

    @property
    def valid_count(self) -> int:
        return int(self.values.count())

    @property
    def valid_area_ha(self) -> float:
        return self.valid_count * self.pixel_area_ha


def load_raster_clipped(
    path: str,
    aoi: AOI,
    resampling: str = "nearest",
    band: int = 1,
    like: "RasterSlice | None" = None,
) -> RasterSlice:
    """Clip `path` to the AOI, reproject to REFERENCE_CRS, mask to the polygon.

    `band` selects one band of a multi band raster. Only the pathway raster in F02-P4 uses it;
    every other layer is single band and takes the default.

    `resampling` is "nearest" for every categorical layer, which is all of them except the
    continuous FLII score. Categorical values must never be interpolated.

    `like` forces the output onto exactly the grid of an already loaded slice: same shape, same
    origin, same pixel size, so that `a.values[i]` and `b.values[i]` describe the same ground.
    Components that only sum or tabulate one raster at a time do not need it and leave it None,
    which is why every component before F02-P5 does. Component 5.1 does need it: it ranks pixels
    by one raster and then reads two other rasters at the pixels it selected, which is only
    meaningful if all three share a grid. Implementations must honour this or 5.1 silently pairs
    risk with the carbon of a different place.

    Returns an all masked array when the raster does not cover the AOI at all. Components
    handle that as "not applicable", not as an error.
    """
    rs = _RESAMPLING[resampling]
    geom = aoi.geometry.iloc[0]  # single dissolved polygon, already in REFERENCE_CRS

    with rasterio.open(path) as src:
        if like is not None:
            # Force the exact grid of an earlier slice, so pixels line up one to one.
            dst_transform = like.transform
            dst_h, dst_w = like.values.shape
        else:
            # Destination grid = source resolution carried into REFERENCE_CRS, cropped to the
            # AOI bounding box so only the AOI window is warped, not the whole SEA raster.
            base_transform, _, _ = calculate_default_transform(
                src.crs, REFERENCE_CRS, src.width, src.height, *src.bounds
            )
            minx, miny, maxx, maxy = geom.bounds
            inv = ~base_transform
            c0, r0 = inv * (minx, maxy)
            c1, r1 = inv * (maxx, miny)
            col_off, row_off = int(np.floor(c0)), int(np.floor(r0))
            dst_w = max(1, int(np.ceil(c1)) - col_off)
            dst_h = max(1, int(np.ceil(r1)) - row_off)
            dst_transform = base_transform * Affine.translation(col_off, row_off)

        # NaN fill separates "no source coverage" from a genuine 0 in a categorical raster.
        fill = float(src.nodata) if src.nodata is not None else np.nan
        dst = np.full((dst_h, dst_w), fill, dtype="float64")
        reproject(
            source=rasterio.band(src, band),
            destination=dst,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=REFERENCE_CRS,
            src_nodata=src.nodata,
            dst_nodata=fill,
            resampling=rs,
        )
        src_nodata = src.nodata

    # Mask everything outside the AOI polygon, then everything with no source value.
    outside = geometry_mask(
        [geom.__geo_interface__], out_shape=(dst_h, dst_w),
        transform=dst_transform, invert=False,  # True where a pixel is OUTSIDE the polygon
    )
    nodata_mask = np.isnan(dst) if src_nodata is None else (dst == src_nodata)
    values = np.ma.masked_array(dst, mask=(outside | nodata_mask))

    pixel_area_ha = abs(dst_transform.a * dst_transform.e) / M2_PER_HA
    return RasterSlice(
        values=values, pixel_area_ha=pixel_area_ha, transform=dst_transform, crs=REFERENCE_CRS
    )


def load_vector_intersecting(path: str, aoi: AOI) -> gpd.GeoDataFrame:
    """Load only the features of `path` that intersect the AOI, reprojected to REFERENCE_CRS.

    Two stages, so a SEA-wide layer is never read in full. `bbox=aoi.geometry` pushes the AOI
    bounding box down to the file reader (geopandas reprojects it to the file CRS), which uses
    the file's spatial index to return only nearby features. Then an exact `intersects` test
    drops the corners the bounding box let through. Returns an empty GeoDataFrame, never None.
    """
    gdf = gpd.read_file(path, bbox=aoi.geometry)
    if gdf.empty:
        return gdf.to_crs(REFERENCE_CRS) if gdf.crs is not None else gdf
    gdf = gdf.to_crs(REFERENCE_CRS)
    aoi_geom = aoi.geometry.iloc[0]
    return gdf[gdf.intersects(aoi_geom)].reset_index(drop=True)


# Column headers as they come out of the "NBS Pathway Logic" Sheet, mapped to the names the
# tool uses. Underscore variants are accepted too, so a hand-made CSV also loads.
_ACTIVITY_COL_ALIASES = {
    "cat_id": "cat_code", "cat_code": "cat_code",
    "ecosystem": "ecosystem",
    "activity id": "activity_id", "activity_id": "activity_id",
    "activity": "activity",
    "benefit nature": "benefit_nature", "benefit_nature": "benefit_nature",
    "benefit people": "benefit_people", "benefit_people": "benefit_people",
    "benefit climate": "benefit_climate", "benefit_climate": "benefit_climate",
    "qb avoided emissions": "qb_avoided", "qb_avoided": "qb_avoided",
    "qb carbon sequestration": "qb_sequestration", "qb_sequestration": "qb_sequestration",
}

# Ecosystem is text in the Sheet; the raster band 2 is an integer. This is the bridge.
_ECOSYSTEM_NAME_TO_CODE = {
    "dryland forest": 1, "mangrove": 2, "peatland": 3, "savanna": 4,
}


def load_activity_table(path: str) -> dict[tuple[int, int], list[dict]]:
    """Load canonical_v3_activities, keyed on the pair (cat_code, ecosystem).

    Reads the Sheet export directly: `Cat_ID`, `Ecosystem` (text), `Activity ID`, `Activity`,
    the three `Benefit ...` columns and the two `QB ...` columns. Returns
    {(cat_code, ecosystem_code): [row, ...]}, ecosystem mapped to the band-2 integer
    (1 dryland forest, 2 mangrove, 3 peatland, 4 savanna). Rows with no ecosystem, the ineligible
    categories, carry no join key and are skipped; those categories are handled in 4.2 by the
    cat_code to pathway map instead.
    """
    df = pd.read_csv(path)
    df.columns = [_ACTIVITY_COL_ALIASES.get(c.strip().lower(), c.strip().lower())
                  for c in df.columns]

    required = {"cat_code", "ecosystem", "activity_id", "activity",
                "benefit_nature", "benefit_people", "benefit_climate",
                "qb_avoided", "qb_sequestration"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing columns {sorted(missing)}.")

    def as_bool(v: object) -> bool:
        return str(v).strip().lower() in {"yes", "y", "true", "1"}

    def eco_code(v: object) -> int | None:
        s = str(v).strip()
        return int(s) if s.isdigit() else _ECOSYSTEM_NAME_TO_CODE.get(s.lower())

    def clean_id(v: object) -> str:
        if pd.isna(v):
            return ""
        try:
            return str(int(float(v)))   # "11.0" from a float column -> "11"
        except (ValueError, TypeError):
            return str(v).strip()

    def clean_text(v: object) -> str:
        return "" if pd.isna(v) else " ".join(str(v).split())  # collapse stray newlines

    table: dict[tuple[int, int], list[dict]] = {}
    for _, r in df.iterrows():
        if pd.isna(r["ecosystem"]) or str(r["ecosystem"]).strip() == "":
            continue  # ineligible category, no (cat_code, ecosystem) join key
        ec = eco_code(r["ecosystem"])
        if ec is None:
            raise ValueError(f"Unknown ecosystem {r['ecosystem']!r} in {path}.")
        table.setdefault((int(r["cat_code"]), ec), []).append({
            "activity_id": clean_id(r["activity_id"]),
            "activity": clean_text(r["activity"]),
            "benefit_nature": clean_text(r["benefit_nature"]),
            "benefit_people": clean_text(r["benefit_people"]),
            "benefit_climate": clean_text(r["benefit_climate"]),
            "qb_avoided": as_bool(r["qb_avoided"]),
            "qb_sequestration": as_bool(r["qb_sequestration"]),
        })
    return table


def load_soil_class_table(path: str) -> dict[int, str]:
    """Map soil class raster codes to WRB group names, from a two column lookup table.

    Returns {code: name}. Codes present in the raster but missing here are reported by 3.6 as
    unmapped rather than dropped, so a lookup that falls behind the raster is visible.
    """
    raise NotImplementedError("Data access stub. Wire to SOIL_CLASS_TABLE.")


def load_national_forest_risk_percentiles(country: str) -> dict[int, float] | None:
    """Percentile breakpoints of national forest deforestation risk, on the 0 to 100 scale.

    Returns {10: value, 20: value, ... 90: value}, or None when the country is missing.
    """
    raise NotImplementedError("Data access stub. Wire to NATIONAL_FOREST_RISK_CSV.")


# ============================ ZONAL TABULATION ============================


@dataclass(frozen=True)
class ClassShare:
    """One row of a class distribution."""

    code: int | str
    label: str
    area_ha: float
    pct: float


def tabulate_classes(
    raster: RasterSlice,
    class_labels: dict[int, str],
    denominator_ha: float,
) -> list[ClassShare]:
    """Count pixels per class code and turn them into area and share.

    `denominator_ha` is passed in rather than derived, because the choice of denominator is a
    locked decision that differs per component:
      - share of the whole site  -> aoi.area_ha        (1.1, 2.2)
      - share of valid pixels    -> raster.valid_area_ha (1.4, 1.7)
      - share of forest          -> forest area          (2.1)
    """
    rows: list[ClassShare] = []
    for code, label in class_labels.items():
        count = int((raster.values == code).sum())
        area_ha = count * raster.pixel_area_ha
        rows.append(
            ClassShare(
                code=code,
                label=label,
                area_ha=area_ha,
                pct=safe_pct(area_ha, denominator_ha),
            )
        )
    return rows


def slope_percent_from_dem(elev: RasterSlice, aoi: AOI) -> RasterSlice:
    """Slope in percent computed from a clipped elevation raster (metres), for 1.4.

    Slope is the horizontal gradient of elevation, so it needs true ground distances. But the
    reference CRS (ESRI:54034) is equal area: it preserves area and distorts distance with
    latitude. This corrects the per-pixel run using the AOI centroid latitude, first-order exact
    for a cylindrical equal-area sphere with the standard parallel at the equator: the east-west
    run shrinks by cos(lat), the north-south run grows by 1 / cos(lat). Near the equator the
    correction is tiny; it grows toward the tropics' edge.

    Returns a RasterSlice of slope percent on the same grid, so it can be binned like any layer.
    """
    z = elev.values.astype("float64").filled(np.nan)
    if min(z.shape) < 2:
        # Too few pixels for a gradient; report flat rather than error.
        flat = np.ma.masked_array(np.zeros_like(z), mask=np.ma.getmaskarray(elev.values))
        return RasterSlice(flat, elev.pixel_area_ha, elev.transform, elev.crs)

    lat = np.radians(float(aoi.geometry.centroid.to_crs(4326).y.iloc[0]))
    cos_lat = max(float(np.cos(lat)), 1e-6)
    run_x = abs(elev.transform.a) * cos_lat        # east-west ground metres per pixel
    run_y = abs(elev.transform.e) / cos_lat        # north-south ground metres per pixel

    gy, gx = np.gradient(z, run_y, run_x)
    slope_pct = np.sqrt(gx**2 + gy**2) * 100.0
    masked = np.ma.masked_array(
        slope_pct, mask=np.isnan(slope_pct) | np.ma.getmaskarray(elev.values)
    )
    return RasterSlice(masked, elev.pixel_area_ha, elev.transform, elev.crs)


def save_raster(rslice: RasterSlice, name: str) -> Path:
    """Write a RasterSlice to a GeoTIFF under the per-AOI raster output folder.

    Destination is RASTER_OUTPUT_DIR (config: OUTPUT_ROOT\\<AOI_ID>\\rasters), created if needed,
    so switching AOI_ID in config sends every saved raster to a fresh per-AOI folder. `name` is
    the file stem, for example "1.1_ecosystem"; ".tif" is added. Masked cells are written as the
    nodata value. Output is in REFERENCE_CRS, the grid the slice was clipped to.
    """
    out_dir = Path(RASTER_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.tif"

    nodata = -9999.0
    arr = np.ma.filled(rslice.values.astype("float32"), np.float32(nodata))
    with rasterio.open(
        path, "w", driver="GTiff",
        height=arr.shape[0], width=arr.shape[1], count=1, dtype="float32",
        crs=rslice.crs, transform=rslice.transform, nodata=nodata, compress="lzw",
    ) as dst:
        dst.write(arr, 1)
    return path


def save_table_csv(rows: list, name: str) -> Path:
    """Write a component table to CSV under the per-AOI tables folder.

    Destination is CSV_OUTPUT_DIR (config: OUTPUT_ROOT\\<AOI_ID>\\tables). `rows` is a table from
    ComponentResult.tables, a list of dataclasses (ClassShare, HazardCard, ...) or plain dicts;
    both become a flat DataFrame. `name` is the file stem, for example "1.8_land_cover_full".
    """
    out_dir = Path(CSV_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.csv"
    recs = [asdict(x) if is_dataclass(x) and not isinstance(x, type) else x for x in rows]
    pd.DataFrame(recs).to_csv(path, index=False)
    return path


def classify_continuous(raster: RasterSlice, breaks: Sequence[float]) -> RasterSlice:
    """Bin a continuous raster into integer class codes 1..len(breaks)+1.

    Upper-exclusive edges via np.digitize: a value below breaks[0] is class 1, and a value at or
    above breaks[-1] is the top class. Used by 1.4 to classify continuous elevation and slope
    itself, since the inputs are not pre-binned. The mask is preserved, so nodata stays nodata.
    """
    codes = np.digitize(raster.values.filled(np.nan), list(breaks), right=False) + 1
    masked = np.ma.masked_array(codes, mask=np.ma.getmaskarray(raster.values))
    return RasterSlice(
        values=masked,
        pixel_area_ha=raster.pixel_area_ha,
        transform=raster.transform,
        crs=raster.crs,
    )


def safe_pct(part: float, whole: float) -> float:
    """Share in percent, 0.0 when the denominator is zero. Keeps narratives free of NaN."""
    return 0.0 if whole <= 0 else part / whole * 100.0


def dominant(rows: Sequence[ClassShare]) -> ClassShare | None:
    """The class with the largest area, or None when every class is empty.

    Ties are broken by the order of `rows`, which follows the class code order in config. This
    is deterministic but arbitrary. Exact ties are unlikely on real rasters.
    """
    present = [r for r in rows if r.area_ha > 0]
    return max(present, key=lambda r: r.area_ha) if present else None


def sort_by_area(rows: list) -> list:
    """Sort any objects that carry `area_ha` descending. Dominant first, used in narratives."""
    return sorted(rows, key=lambda r: r.area_ha, reverse=True)


# ============================ SHARED MASKS ============================


@dataclass(frozen=True)
class ForestMask:
    """The AOI forest at a single date, as a boolean array plus its area.

    Produced here rather than passed between component results, so that 1.5, 1.6 and any later
    module all use one definition of forest and one alignment.
    """

    mask: np.ndarray
    pixel_area_ha: float
    area_ha: float
    transform: object = None   # grid the mask sits on, so it can be written as a raster
    crs: object = None

    @property
    def is_empty(self) -> bool:
        return self.area_ha <= 0

    def as_slice(self) -> "RasterSlice":
        """The mask as a 0/1 RasterSlice, for saving. Non-forest is 0, not masked."""
        return RasterSlice(
            values=np.ma.masked_array(self.mask.astype("float32"), mask=False),
            pixel_area_ha=self.pixel_area_ha,
            transform=self.transform,
            crs=self.crs,
        )


def forest_mask_2024(aoi: AOI) -> ForestMask:
    """Forest inside the AOI in 2024, from the binary FC2024 layer.

    Reads SEA_FC2024.tif (value 1 = forest), the same Tier 1-2 definition applied upstream to
    FC2014, so both dates are symmetric. This replaces the earlier derivation from LC2024
    FOREST_CODES; the switch was a team decision, LC2024 is still wired but no longer the source
    of the 2024 forest mask.
    """
    fc = load_raster_clipped(FC2024_RASTER, aoi, resampling="nearest")
    mask = np.isin(fc.values.filled(-1), FC2024_FOREST_CODES)
    return ForestMask(
        mask=mask,
        pixel_area_ha=fc.pixel_area_ha,
        area_ha=int(mask.sum()) * fc.pixel_area_ha,
        transform=fc.transform,
        crs=fc.crs,
    )


def forest_mask_2014(aoi: AOI) -> ForestMask:
    """Forest inside the AOI in 2014, from the binary FC2014 layer.

    FC2014 is already a binary product (1 = forest), so FC2014_FOREST_CODES = [1] is a raster
    value, not an LC legend code. The Tier 1 to 2 rule was applied upstream when FC2014 was
    built, so both dates carry the same forest definition.
    """
    fc = load_raster_clipped(FC2014_RASTER, aoi, resampling="nearest")
    mask = np.isin(fc.values.filled(-1), FC2014_FOREST_CODES)
    return ForestMask(
        mask=mask,
        pixel_area_ha=fc.pixel_area_ha,
        area_ha=int(mask.sum()) * fc.pixel_area_ha,
        transform=fc.transform,
        crs=fc.crs,
    )


# ============================ VECTOR OVERLAY ============================


def union_overlap_ha(aoi: AOI, features: gpd.GeoDataFrame) -> float:
    """Area of the AOI covered by the union of `features`.

    Union first, then intersect. Both WDPA (1.3) and KBA (2.2) contain sites that overlap or
    nest inside each other, so adding per site areas can exceed the AOI. The union is the only
    figure that can be reported as a share of the site.
    """
    if features.empty:
        return 0.0
    merged = features.geometry.union_all()
    return float(aoi.geometry.intersection(merged).area.sum()) / M2_PER_HA


def per_feature_overlap_ha(aoi: AOI, features: gpd.GeoDataFrame) -> np.ndarray:
    """Per feature intersection area with the AOI, in the row order of `features`.

    Used for the breakdown table only. These values may sum to more than the union area when
    sites overlap, which is expected and is why the headline uses `union_overlap_ha`.
    """
    if features.empty:
        return np.array([], dtype=float)
    aoi_geom = aoi.geometry.iloc[0]
    return np.array(
        [geom.intersection(aoi_geom).area / M2_PER_HA for geom in features.geometry],
        dtype=float,
    )


# ============================ NARRATIVE HELPERS ============================


def fmt_ha(value: float) -> str:
    """Hectares for prose. Thousands separator, no decimals. Screening precision, not cadastral."""
    return f"{value:,.0f} ha"


def fmt_pct(value: float, decimals: int = 0) -> str:
    return f"{value:.{decimals}f}%"


def oxford_join(items: Iterable[str]) -> str:
    """Join a list into readable prose: "a", "a and b", "a, b, and c"."""
    items = list(items)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def sentences(*parts: str) -> str:
    """Join non empty sentence fragments with a single space. Skips None and empty strings."""
    return " ".join(p.strip() for p in parts if p)


# ============================ RESULT BASE ============================


@dataclass
class ComponentResult:
    """Common shape returned by every component.

    `applicable` is False when the component has nothing to measure, for example FLII on an AOI
    with no forest. The frontend still renders the card and shows `narrative`, so the absence of
    a signal is visible rather than silently missing.
    """

    component: str
    applicable: bool
    narrative: str
    tables: dict[str, list] = field(default_factory=dict)
    values: dict[str, object] = field(default_factory=dict)
    flags: list[str] = field(default_factory=list)
    # Derived output rasters this section produced, {filename_stem: RasterSlice}. show_result
    # writes each to the per-AOI raster folder. Not serialised into the JSON handoff.
    rasters: dict = field(default_factory=dict)


def not_applicable(component: str, reason: str) -> ComponentResult:
    return ComponentResult(component=component, applicable=False, narrative=reason)


def show_result(r: ComponentResult) -> None:
    """Display one component's result inline in a notebook, section by section.

    Prints the component header, renders each table as a DataFrame, shows the `values` dict, and
    prints any flags. Each component cell calls this so its result is visible when the cell runs,
    even though the final cell still saves all results to one combined JSON. Import-light: pandas
    and IPython.display are imported here so the module still loads outside a notebook.
    """
    from IPython.display import display

    header = r.component + ("" if r.applicable else "  (not applicable)")
    section = r.component.split()[0] if r.component else "section"
    print(f"[{header}]")
    if r.narrative:
        print(f"  {r.narrative}")
    for name, tbl in r.tables.items():
        if tbl:
            rows = [asdict(x) if is_dataclass(x) and not isinstance(x, type) else x for x in tbl]
            print(f"  {name}:")
            display(pd.DataFrame(rows))
            print("  saved table:", save_table_csv(tbl, f"{section}_{name}"))
    if r.values:
        display(r.values)
    for f in r.flags:
        print("FLAG:", f)
    # Persist any derived output rasters to the per-AOI raster folder.
    for stem, rslice in r.rasters.items():
        if rslice is not None and rslice.transform is not None:
            saved = save_raster(rslice, stem)
            print("  saved raster:", saved)


# ============================ RESULT HANDOFF ============================
# Notebooks cannot import each other, because names like "F02-P2 General.ipynb" are not valid
# Python module names. JSON on disk is the contract instead. Each notebook ends by calling
# `save_results`, and any notebook that needs an earlier stage starts by calling `load_results`.
# Side effect worth keeping: the contract becomes inspectable. A reviewer can open the JSON and
# see exactly what one stage promises the next, without running anything.


def to_jsonable(obj: object) -> object:
    """Convert a result tree into plain JSON types.

    Handles the four things that appear in results and that json cannot take directly:
    dataclasses (ClassShare, AdminUnit, ProtectedSite, HazardCard, KbaSite), frozensets
    (present_set from 1.1), numpy scalars, and numpy arrays.

    Note the lossy step: `present_set` becomes a sorted list, so a consumer must not rely on
    set semantics after a round trip. Downstream code should read it back with `set(...)`.
    """
    if is_dataclass(obj) and not isinstance(obj, type):
        # Drop 'rasters': it holds RasterSlice grids (numpy arrays + Affine), not JSON, and is
        # persisted separately as GeoTIFFs, not in the stage handoff.
        return {k: to_jsonable(v) for k, v in asdict(obj).items() if k != "rasters"}
    if isinstance(obj, (set, frozenset)):
        return sorted(obj, key=str)
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def result_path(aoi_id: str, stage: str) -> Path:
    return Path(OUTPUT_DIR) / f"{aoi_id}__{stage}.json"


def save_results(results: dict[str, ComponentResult], aoi: AOI, aoi_id: str, stage: str) -> Path:
    """Write one stage of results to disk and return the path.

    The AOI block is repeated in every stage file on purpose. It makes each file self describing,
    so a stale file from a different AOI can be detected instead of silently mixed in.
    """
    path = result_path(aoi_id, stage)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "aoi_id": aoi_id,
        "stage": stage,
        "aoi": {
            "area_ha": aoi.area_ha,
            "source_crs": aoi.source_crs,
            "reference_crs": REFERENCE_CRS,
        },
        "components": {k: to_jsonable(v) for k, v in results.items()},
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_results(aoi_id: str, stage: str) -> dict:
    """Read one stage back. Returns the raw payload, not rehydrated dataclasses.

    Downstream modules read `values` and `tables`, which are plain dicts and lists after the
    round trip. Rebuilding the dataclasses would add a second definition of every result type
    with no benefit, so it is deliberately not done.
    """
    path = result_path(aoi_id, stage)
    if not path.exists():
        raise FileNotFoundError(
            f"Stage '{stage}' has not been run for AOI '{aoi_id}'. Expected {path}."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))

    if payload.get("aoi_id") != aoi_id:
        raise ValueError(
            f"{path} belongs to AOI '{payload.get('aoi_id')}', not '{aoi_id}'."
        )
    return payload


def component_values(payload: dict, component_key: str) -> dict:
    """Shortcut for the common read: `component_values(general, "1.2")["dominant_country"]`."""
    return payload["components"][component_key]["values"]
