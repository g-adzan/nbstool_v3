"""
build_national_risk_reference.py

One-off builder for the 1.6 national reference table. Computes, per country, the p10..p90
percentile breakpoints of the deforestation-risk layer over that country's forest, and writes
`config.NATIONAL_FOREST_RISK_CSV`.

Run once, in the nbs-screening environment, whenever prob.tif or the admin layer changes:

    conda activate nbs-screening
    python build_national_risk_reference.py

Definition of "forest" here matches component 1.6 exactly: prob.tif is forest-masked upstream,
so its VALID (non-nodata) pixels inside a country are that country's forest. No separate forest
mask is applied, so the national baseline and the per-AOI value in 1.6 use one definition.

Country names are taken from the COUNTRY field of ADMIN_BOUNDARIES, the same field 1.2 reports as
`dominant_country`, so the loader's country lookup matches. The risk scale is prob_raw /
PROB_SCALE_MAX * 100, the same rescale 1.6 uses.

Memory note: a country like Indonesia or Malaysia has a bounding box almost as wide as the whole
SEA raster. Reading that box at full resolution in one go needs tens of GiB, so this builder never
holds a whole country window in RAM. It streams each country in row chunks and accumulates a
histogram of the raw UInt16 risk values, then reads the percentiles off the cumulative histogram.
prob.tif is UInt16 (discrete 0..PROB_SCALE_MAX), so the histogram is exact: its percentiles equal
np.percentile by nearest rank on the same pixels, at a fraction of the memory.

Caveat carried over from 1.6: if prob.tif is a mosaic of separately fitted regional models, the
0-100 scale is not guaranteed comparable across regions, so a national percentile pools models
with possibly different calibrations. This builder does not correct for that.
"""

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds

from config import (
    ADMIN_BOUNDARIES,
    NATIONAL_FOREST_RISK_CSV,
    PROB_RASTER,
    PROB_SCALE_MAX,
)

PERCENTILES = list(range(10, 100, 10))   # 10, 20, ..., 90
COUNTRY_FIELD = "COUNTRY"                # matches ADMIN_LEVELS["country"] and 1.2
ROWS_PER_CHUNK = 256                     # row-strip height; caps peak RAM per read


def percentiles_from_histogram(hist: np.ndarray, percentiles: list[int]) -> list[int] | None:
    """Nearest-rank percentiles from a value-indexed count histogram.

    hist[v] is the number of pixels whose raw value is v. Returns the raw value at each
    requested percentile (the smallest value at which the cumulative count reaches p% of total).
    """
    total = int(hist.sum())
    if total == 0:
        return None
    cum = np.cumsum(hist)
    out = []
    for p in percentiles:
        rank = p / 100.0 * total
        idx = int(np.searchsorted(cum, rank, side="left"))
        out.append(min(idx, hist.size - 1))
    return out


def country_histogram(src, geom, nodata) -> np.ndarray:
    """Accumulate a raw-value histogram over one country's forest pixels, streaming in row chunks.

    Only the country's window is scanned, and only ROWS_PER_CHUNK rows are held at a time, so peak
    memory is bounded regardless of how wide the country's bounding box is.
    """
    hist = np.zeros(PROB_SCALE_MAX + 1, dtype=np.int64)

    # Country window, as integer pixel offsets clamped to the raster. Computed by hand (floor the
    # start, ceil the end) rather than Window.round_offsets, whose signature varies by rasterio
    # version.
    fwin = from_bounds(*geom.bounds, transform=src.transform)
    col0 = max(0, int(np.floor(fwin.col_off)))
    row0 = max(0, int(np.floor(fwin.row_off)))
    col1 = min(src.width, int(np.ceil(fwin.col_off + fwin.width)))
    row1 = min(src.height, int(np.ceil(fwin.row_off + fwin.height)))
    width, height = col1 - col0, row1 - row0
    if width <= 0 or height <= 0:
        return hist
    geoms = [geom.__geo_interface__]

    for r in range(0, height, ROWS_PER_CHUNK):
        h = min(ROWS_PER_CHUNK, height - r)
        sub = rasterio.windows.Window(col0, row0 + r, width, h)
        arr = src.read(1, window=sub)
        sub_transform = src.window_transform(sub)

        # True where the pixel centre falls inside the country polygon.
        inside = geometry_mask(geoms, out_shape=arr.shape, transform=sub_transform, invert=True)
        if nodata is not None:
            valid = inside & (arr != nodata)
        else:
            valid = inside
        if not valid.any():
            continue

        vals = arr[valid].astype(np.int64).ravel()
        # Guard against any stray value outside the expected 0..PROB_SCALE_MAX range.
        np.clip(vals, 0, PROB_SCALE_MAX, out=vals)
        hist += np.bincount(vals, minlength=PROB_SCALE_MAX + 1)

    return hist


def main() -> None:
    admin = gpd.read_file(ADMIN_BOUNDARIES)
    if COUNTRY_FIELD not in admin.columns:
        raise ValueError(f"{ADMIN_BOUNDARIES} has no '{COUNTRY_FIELD}' field.")

    with rasterio.open(PROB_RASTER) as src:
        admin = admin.to_crs(src.crs)
        # One geometry per country. dissolve on the name field is fine: country names are unique
        # and we only need the union polygon.
        countries = admin.dissolve(by=COUNTRY_FIELD, as_index=False)
        nodata = src.nodata

        if nodata is None:
            print("WARNING: prob.tif has no nodata value. Forest masking relies on it, so every "
                  "in-country pixel (including non-forest) will be included. Set a nodata value "
                  "on prob.tif for a forest-only baseline.")

        rows = []
        for _, c in countries.iterrows():
            name = c[COUNTRY_FIELD]
            hist = country_histogram(src, c.geometry, nodata)
            n = int(hist.sum())
            if n == 0:
                print(f"  {name}: no forest pixels with a risk value, skipped")
                continue

            raw = percentiles_from_histogram(hist, PERCENTILES)
            values = [round(v / PROB_SCALE_MAX * 100.0, 3) for v in raw]

            # Median risk for a quick sanity read, also off the histogram.
            med_raw = percentiles_from_histogram(hist, [50])[0]
            med = med_raw / PROB_SCALE_MAX * 100.0

            rows.append({
                "country": name,
                **{f"p{p}": v for p, v in zip(PERCENTILES, values)},
            })
            print(f"  {name}: {n:,} forest pixels, median risk {med:.1f}")

    if not rows:
        raise RuntimeError("No country produced any percentiles; check prob.tif and the admin layer.")

    df = pd.DataFrame(rows).sort_values("country")
    df.to_csv(NATIONAL_FOREST_RISK_CSV, index=False)
    print(f"\nWrote {len(df)} countries to {NATIONAL_FOREST_RISK_CSV}")


if __name__ == "__main__":
    main()
