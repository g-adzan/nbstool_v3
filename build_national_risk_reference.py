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

Caveat carried over from 1.6: if prob.tif is a mosaic of separately fitted regional models, the
0-100 scale is not guaranteed comparable across regions, so a national percentile pools models
with possibly different calibrations. This builder does not correct for that.
"""

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask as rio_mask

from config import (
    ADMIN_BOUNDARIES,
    NATIONAL_FOREST_RISK_CSV,
    PROB_RASTER,
    PROB_SCALE_MAX,
)

PERCENTILES = list(range(10, 100, 10))   # 10, 20, ..., 90
COUNTRY_FIELD = "COUNTRY"                # matches ADMIN_LEVELS["country"] and 1.2


def main() -> None:
    admin = gpd.read_file(ADMIN_BOUNDARIES)
    if COUNTRY_FIELD not in admin.columns:
        raise ValueError(f"{ADMIN_BOUNDARIES} has no '{COUNTRY_FIELD}' field.")

    with rasterio.open(PROB_RASTER) as src:
        # Match the admin CRS to the raster so the mask lines up.
        admin = admin.to_crs(src.crs)
        # One geometry per country. dissolve on the name field is fine here: countries are
        # unique, and we only need the union polygon.
        countries = admin.dissolve(by=COUNTRY_FIELD, as_index=False)

        if src.nodata is None:
            print("WARNING: prob.tif has no nodata value. Forest masking relies on it, so every "
                  "in-country pixel (including non-forest) will be included. Set a nodata value "
                  "on prob.tif for a forest-only baseline.")

        rows = []
        for _, c in countries.iterrows():
            name = c[COUNTRY_FIELD]
            geom = [c.geometry.__geo_interface__]
            try:
                out, _ = rio_mask(src, geom, crop=True, filled=False, nodata=src.nodata)
            except ValueError:
                # No overlap between this country and the raster window.
                print(f"  {name}: no raster overlap, skipped")
                continue

            band = out[0]
            valid = band.compressed() if np.ma.isMaskedArray(band) else band[~np.isnan(band)]
            if valid.size == 0:
                print(f"  {name}: no forest pixels with a risk value, skipped")
                continue

            risk = valid.astype("float64") / PROB_SCALE_MAX * 100.0
            values = np.percentile(risk, PERCENTILES)
            rows.append({
                "country": name,
                **{f"p{p}": round(float(v), 3) for p, v in zip(PERCENTILES, values)},
            })
            print(f"  {name}: {int(valid.size):,} forest pixels, "
                  f"median risk {np.median(risk):.1f}")

    if not rows:
        raise RuntimeError("No country produced any percentiles; check prob.tif and the admin layer.")

    df = pd.DataFrame(rows).sort_values("country")
    df.to_csv(NATIONAL_FOREST_RISK_CSV, index=False)
    print(f"\nWrote {len(df)} countries to {NATIONAL_FOREST_RISK_CSV}")


if __name__ == "__main__":
    main()
