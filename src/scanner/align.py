"""Straighten a scanned page of PDF using ArUco markers."""

import cv2 as cv
import imutils
import numpy as np

class AlignmentError(RuntimeError):
    """
    Raised for any ArUco errors preventing automatic alignment.
        reason:     failure type
        page:       page name
    """

    BAD_IMAGE = "bad_image"
    NO_MARKERS = "no_markers"
    MISSING_MARKERS = "missing_markers"
    BAD_GEOMETRY = "bad_geometry"

    REASONS = {
        BAD_IMAGE: "Image is empty or too small",
        NO_MARKERS: "No ArUco markers detected",
        MISSING_MARKERS: "Some corner markers were not found",
        BAD_GEOMETRY: "Corner markers don't form a valid page outline",
    }

    def __init__(self, reason, page=None):
        self.reason = reason
        self.page = page
        super().__init__(str(self))

    def __str__(self):
        message = self.REASONS.get(self.reason, self.reason)
        return f"[{self.page}] {message}" if self.page else message

def align(image, config, page=None):
    """
    Prepares image, checks for alignment errors, and aligns 
        image:      image array
        config:     config file 
    """
    try:
        width = config["image"]["width_px"]
        _check_image_size(image)

        gray = grayscale(image, width)
        corners = find_corners(gray, config)
        _check_geometry(corners)

        result = transform(gray, corners, width)
        
        return result

    except AlignmentError as e:
        e.page = page
        raise

def grayscale(image, width=1000):
    """
    Converts image to greyscale.
        image:      image array
        width:      resize width
    """
    # resize
    image = imutils.resize(image, width=width)

    # grayscale if in color
    if image.ndim == 3:
        image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

    return image

def find_corners(image, config):
    """
    Finds the four corners using ArUco marks and returns their coordinates
        image:      image array
        config:     config file 
    """
    # setup
    corner_ids = config["aruco"]["corner_ids"]
    aruco_dict = cv.aruco.getPredefinedDictionary(
        getattr(cv.aruco, config["aruco"]["dictionary"])
    )
    detector = cv.aruco.ArucoDetector(aruco_dict, cv.aruco.DetectorParameters())

    # detect markers
    corners, ids, _ = detector.detectMarkers(image)
    if ids is None:
        raise AlignmentError(AlignmentError.NO_MARKERS)

    # map each id to its vertices
    markers = {int(mid): c.reshape((4, 2)) 
               for c, mid in zip(corners, ids.flatten())}

    missing = [name 
               for name, mid in corner_ids.items() 
               if mid not in markers]
    if missing:
        raise AlignmentError(AlignmentError.MISSING_MARKERS)

    # grab outer vertex of each
    outer = {name: markers[mid][mid] 
             for name, mid in corner_ids.items()}

    return (
        outer["top_left"],
        outer["bottom_left"],
        outer["bottom_right"],
        outer["top_right"],
    )

def transform(image, coords, width=1000):
    """
    Transforms the image based on the coordinates of the aruco marks
        image:      image array
        coords:     coordinates of top left, bottom left, bottom right, and top right corners
        width:      final image width
    """
    tl, bl, br, tr = coords

    # set output size based on current dimensions
    w = int(max(np.linalg.norm(tl - tr), np.linalg.norm(bl - br)))
    h = int(max(np.linalg.norm(tl - bl), np.linalg.norm(tr - br)))

    # original and new vertices
    input_pts = np.float32([tl, bl, br, tr])
    output_pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]])

    # transform
    M = cv.getPerspectiveTransform(input_pts, output_pts)
    corrected = cv.warpPerspective(image, M, (w, h), flags=cv.INTER_LINEAR)

    # resize to original width
    return imutils.resize(corrected, width=width)

def _check_image_size(image):
    """
    Checks image for validity and throws "bad image" alignment errors if not
        image:      image array
    """
    # image does not exist or is empty
    if (image is None) or (not hasattr(image, "shape")) or (image.size == 0):
        raise AlignmentError(AlignmentError.BAD_IMAGE)

    # image is too small
    h, w = image.shape[:2]
    if min(h, w) < 200:
        raise AlignmentError(AlignmentError.BAD_IMAGE)

def _check_geometry(corners):
    """
    Checks image for proper geometry and throws "bad image" alignment errors if not
        image:      image array
    """
    tl, bl, br, tr = corners
    quad = np.float32([tl, tr, br, bl])

    if not cv.isContourConvex(quad.reshape(-1, 1, 2)):
        raise AlignmentError(AlignmentError.BAD_GEOMETRY)