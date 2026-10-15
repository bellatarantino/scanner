"""Turn a scanned PDF into a set of images"""

import cv2 as cv
import numpy as np
import pymupdf

def pdf_to_images(pdf_path, start=1, dpi=200):
    """
    Return a list of (name, image) pairs
        name:      e.g. "p01", "p02", etc. 
        image:     page as a color image 
    """
    pages = []
    doc = pymupdf.open(pdf_path)

    for i, page in enumerate(doc, start=0):
        pix = page.get_pixmap(dpi=dpi)

        # convert to numpy array 
        image = np.frombuffer(pix.samples, dtype=np.uint8)
        image = image.reshape(pix.height, pix.width, pix.n)

        # convert for OpenCV
        image = cv.cvtColor(image, cv.COLOR_RGB2BGR)

        # save and export 
        name = f"p{i + start:02d}"
        pages.append((name, image))

    doc.close()
    return pages