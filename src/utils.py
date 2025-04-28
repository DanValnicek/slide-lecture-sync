from datetime import timedelta

import cv2
import numpy as np


def ms_to_hms(time_ms):
    return str(timedelta(milliseconds=time_ms)).split('.')[0]


def hms_to_ms(hms):
    """Convert HH:MM:SS.mmm format to milliseconds."""
    h, m, s = map(float, hms.split(":"))
    return int((h * 3600 + m * 60 + s) * 1000)


def draw_matches(img1, img2, kp_mtch, mask=None):
    if mask is None:
        mask = [1 for i in kp_mtch]
    best_keypoints1 = [cv2.KeyPoint(*x[0].ravel(), 10) for x in kp_mtch]
    best_keypoints2 = [cv2.KeyPoint(*x[1].ravel(), 10) for x in kp_mtch]
    return cv2.drawMatchesKnn(
        np.array(img1),
        best_keypoints2,
        np.array(img2),
        best_keypoints1,
        [[cv2.DMatch(i, i, 0)] if mask[i] else [] for i in range(len(kp_mtch))],
        None,
        matchColor=(0, 255, 0),
        singlePointColor=(0, 0, 255),
        flags=cv2.DrawMatchesFlags_DRAW_RICH_KEYPOINTS)

def warpPerspectivePadded(
        src, dst, M,
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0):
    """Performs a perspective warp with padding.

    Parameters
    ----------
    src : array_like
        source image, to be warped.
    dst : array_like
        destination image, to be padded.
    M : array_like
        `3x3` perspective transformation matrix.

    Returns
    -------
    src_warped : ndarray
        padded and warped source image
    dst_padded : ndarray
        padded destination image, same size as src_warped

    Optional Parameters
    -------------------
    flags : int, optional
        combination of interpolation methods (`cv2.INTER_LINEAR` or
        `cv2.INTER_NEAREST`) and the optional flag `cv2.WARP_INVERSE_MAP`,
        that sets `M` as the inverse transformation (`dst` --> `src`).
    borderMode : int, optional
        pixel extrapolation method (`cv2.BORDER_CONSTANT` or
        `cv2.BORDER_REPLICATE`).
    borderValue : numeric, optional
        value used in case of a constant border; by default, it equals 0.

    See Also
    --------
    warpAffinePadded() : for `2x3` affine transformations
    cv2.warpPerspective(), cv2.warpAffine() : original OpenCV functions
    """

    assert M.shape == (3, 3), \
        'Perspective transformation shape should be (3, 3).\n' \
        + 'Use warpAffinePadded() for (2, 3) affine transformations.'

    M = M / M[2, 2]  # ensure a legal homography
    if flags in (cv2.WARP_INVERSE_MAP,
                 cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
                 cv2.INTER_NEAREST + cv2.WARP_INVERSE_MAP):
        M = cv2.invert(M)[1]
        flags -= cv2.WARP_INVERSE_MAP

    # it is enough to find where the corners of the image go to find
    # the padding bounds; points in clockwise order from origin
    src_h, src_w = src.shape[:2]
    lin_homg_pts = np.array([
        [0, src_w, src_w, 0],
        [0, 0, src_h, src_h],
        [1, 1, 1, 1]])

    # transform points
    transf_lin_homg_pts = M.dot(lin_homg_pts)
    transf_lin_homg_pts /= transf_lin_homg_pts[2, :]

    # find min and max points
    min_x = np.floor(np.min(transf_lin_homg_pts[0])).astype(int)
    min_y = np.floor(np.min(transf_lin_homg_pts[1])).astype(int)
    max_x = np.ceil(np.max(transf_lin_homg_pts[0])).astype(int)
    max_y = np.ceil(np.max(transf_lin_homg_pts[1])).astype(int)

    # add translation to the transformation matrix to shift to positive values
    anchor_x, anchor_y = 0, 0
    transl_transf = np.eye(3, 3)
    if min_x < 0:
        anchor_x = -min_x
        transl_transf[0, 2] += anchor_x
    if min_y < 0:
        anchor_y = -min_y
        transl_transf[1, 2] += anchor_y
    shifted_transf = transl_transf.dot(M)
    shifted_transf /= shifted_transf[2, 2]

    # create padded destination image
    dst_h, dst_w = dst.shape[:2]

    pad_widths = [anchor_y, max(max_y, dst_h) - dst_h,
                  anchor_x, max(max_x, dst_w) - dst_w]

    dst_padded = cv2.copyMakeBorder(dst, *pad_widths,
                                    borderType=borderMode, value=borderValue)

    dst_pad_h, dst_pad_w = dst_padded.shape[:2]
    src_warped = cv2.warpPerspective(
        src, shifted_transf, (dst_pad_w, dst_pad_h),
        flags=flags, borderMode=borderMode, borderValue=borderValue)

    return dst_padded, src_warped
