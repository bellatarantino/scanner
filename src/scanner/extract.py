"""Extract raw data from prepared files."""

import cv2 as cv
import numpy as np

def to_px(frac, shape):
    """
    Converts a region from fractions of the image to pixel coordinates.
        frac:       (x0, y0, x1, y1) as fractions between 0 and 1
        shape:      image shape (height, width)
    """
    H, W = shape[:2]
    return (int(frac[0] * W), int(frac[1] * H),
            int(frac[2] * W), int(frac[3] * H))

def stretch(region, percentiles=(1,99)):
    """
    Increases contrast within detection region for accuracy
        region:         image array
        percentiles:    (low, high) cutoff
    """
    # find darkest and lightest values (ignore outliers)
    lo, hi = np.percentile(region, percentiles)

    # whited / blacked out 
    if hi - lo < 1:
        return region.copy()
 
    out = (region.astype(np.float32) - lo) * 255 / (hi - lo)
    return np.clip(out, 0, 255).astype(np.uint8)

def brightness(region, circles, mask_radius=0.8):
    """
    Average brightness inside each circle 
        region:         image array 
        circles:        list of (x, y, r)
        mask_radius:    fraction of the circle to use 
    """
    means = []

    for (x,y,r) in circles:
        # only do 80% radius to avoid edges 
        mask = np.zeros_like(region)
        cv.circle(mask, (x, y), int(r * mask_radius), 255, -1)

        # mean of masked pixels only
        means.append(cv.mean(region, mask=mask)[0])
    return means 

def detect(region, config):
    """
    Finds circles in a region, sorted left to right.
        region:     image array
        hough:      Hough settings
    """
    settings = config["hough"]

    # smooth to reduce false positives
    blur = cv.medianBlur(region, settings["median_blur"])
 
    # detect circles 
    found = cv.HoughCircles(
        blur, cv.HOUGH_GRADIENT,
        dp=settings["dp"], minDist=settings["min_dist"],
        param1=settings["param1"], param2=settings["param2"],
        minRadius=settings["min_radius"], maxRadius=settings["max_radius"],
    )
 
    # none found
    if found is None:
        return []
 
    return sorted(tuple(c) for c in np.round(found[0]).astype(int).tolist())


def extract(image, config):
    """
    Finds circles and their brightness for every region on the page
        image:      image array
        config:     config file

    """
    results = {}
 
    for name, frac in config["regions"].items():
        # grab + crop region and boost colors 
        x0, y0, x1, y1 = to_px(frac, image.shape)
        region = stretch(image[y0:y1, x0:x1], config["stretch"]["percentiles"])
 
        # detect all circles and their avg brightness 
        circles = detect(region, config)
        values = brightness(region, circles, config["scoring"]["mask_radius"])

        # prepare results for filename 
        results[name] = {"circles": circles, "brightness": values}
 
    return results