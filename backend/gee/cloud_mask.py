"""
Sentinel-2 Cloud Masking Module

Implements cloud masking using the Scene Classification Layer (SCL)
band from Sentinel-2 Level-2A products.

SCL Classes:
    0  = No Data
    1  = Saturated/Defective
    2  = Dark Area Pixels (topographic shadow)
    3  = Cloud Shadow
    4  = Vegetation  ✓ (keep)
    5  = Bare Soil   ✓ (keep)
    6  = Water       ✓ (keep)
    7  = Cloud Low Probability  ✓ (keep)
    8  = Cloud Medium Probability  ✗ (mask)
    9  = Cloud High Probability    ✗ (mask)
    10 = Thin Cirrus               ✗ (mask)
    11 = Snow/Ice                  ✗ (mask)
"""

import ee
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# SCL values to mask out (clouds, cloud shadow, snow, saturated)
MASK_VALUES = [0, 1, 2, 3, 8, 9, 10, 11]

# SCL values to keep (vegetation, bare soil, water, low-prob cloud)
KEEP_VALUES = [4, 5, 6, 7]


def mask_sentinel2_clouds(image: ee.Image) -> ee.Image:
    """
    Apply cloud masking to a Sentinel-2 Level-2A image using the SCL band.

    The Scene Classification Layer (SCL) provides per-pixel classification
    including cloud probability. We mask out pixels classified as clouds,
    cloud shadows, snow/ice, and saturated/defective pixels.

    Additionally, optical bands are scaled from their native integer format
    (stored as uint16 with scale factor 0.0001) to reflectance values [0, 1].

    Args:
        image: A Sentinel-2 Level-2A ee.Image with SCL band.

    Returns:
        Cloud-masked ee.Image with scaled reflectance values.
    """
    # Get the Scene Classification Layer
    scl = image.select("SCL")

    # Create a mask where SCL is in the "keep" list
    # Pixels with clouds, shadows, snow, etc. are masked out
    mask = (
        scl.eq(4)        # Vegetation
        .Or(scl.eq(5))   # Bare Soil
        .Or(scl.eq(6))   # Water
        .Or(scl.eq(7))   # Cloud Low Probability
    )

    # Scale optical bands from uint16 to float reflectance
    # Sentinel-2 L2A stores reflectance * 10000
    scaled = image.select(["B2", "B3", "B4", "B8", "B11", "B12"]).divide(10000)

    # Apply the cloud mask and copy properties
    return (
        scaled.updateMask(mask)
        .copyProperties(image, image.propertyNames())
    )


def get_cloud_percentage(image: ee.Image) -> ee.Image:
    """
    Add a 'cloud_percentage' property to the image based on SCL analysis.

    Useful for filtering out images with excessive cloud cover before
    compositing.

    Args:
        image: A Sentinel-2 Level-2A ee.Image.

    Returns:
        Same image with added 'cloud_pct' property.
    """
    scl = image.select("SCL")
    total_pixels = scl.reduceRegion(
        reducer=ee.Reducer.count(),
        scale=20,
        maxPixels=1e9,
    ).get("SCL")

    cloud_pixels = scl.eq(8).Or(scl.eq(9)).Or(scl.eq(10)).reduceRegion(
        reducer=ee.Reducer.sum(),
        scale=20,
        maxPixels=1e9,
    ).get("SCL")

    cloud_pct = ee.Number(cloud_pixels).divide(ee.Number(total_pixels)).multiply(100)
    return image.set("cloud_pct", cloud_pct)
