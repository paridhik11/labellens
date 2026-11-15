"""Blind barcode decoding: no template, no known barcode position.

"Blind" means the decoder gets only pixels. It looks for barcode-like regions
itself, then tries several deblurring strengths, scales and thresholds on each
region, and finally on the whole image. The template-assisted mode in
``src.cv.barcode`` (which crops the known barcode slot) is kept and reported
separately.

Why this helps: the test symbol is an 8 by 96 module rectangular DataMatrix
drawn at 3 pixels per module. zxing-cpp needs crisp module edges, so blur of
1 to 2 pixels makes it give up. Wiener deconvolution (an inverse blur filter
that does not amplify noise without limit) followed by upscaling restores
edges that the decoder can trace.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

import cv2
import numpy as np
import zxingcpp

from src.common.schemas import BarcodeResult
from src.cv.barcode import TEMPLATE_PATH, parse_gs1
from src.cv.preprocess import _validate_image

# Symbologies that can carry GS1 data on a device label.
FORMATS = (
    zxingcpp.BarcodeFormat.DataMatrix,
    zxingcpp.BarcodeFormat.QRCode,
    zxingcpp.BarcodeFormat.Code128,
    zxingcpp.BarcodeFormat.EAN13,
)
DEBLUR_SIGMAS = (1.8, 1.4, 1.0, 0.6, 2.2)
CROP_SCALES = (2.0, 3.0)


def wiener_deblur(gray: np.ndarray, sigma: float, noise_to_signal: float = 0.02) -> np.ndarray:
    """Undo a Gaussian blur of the given sigma with a Wiener filter.

    The blur multiplies each spatial frequency by H = exp(-2 pi^2 sigma^2 f^2).
    Dividing by H would restore the image but also multiply noise by 1 / H.
    The Wiener filter H / (H^2 + K) behaves like 1 / H where the signal is
    strong and fades out where H is small. K is ``noise_to_signal``.
    """
    if gray.ndim != 2 or gray.dtype != np.uint8:
        raise ValueError("Expected a uint8 grayscale image")
    if not np.isfinite(sigma) or sigma <= 0 or not np.isfinite(noise_to_signal) or noise_to_signal <= 0:
        raise ValueError("sigma and noise_to_signal must be positive and finite")
    spectrum = np.fft.rfft2(gray.astype(np.float32))
    fy = np.fft.fftfreq(gray.shape[0])[:, None]
    fx = np.fft.rfftfreq(gray.shape[1])[None, :]
    response = np.exp(-2 * np.pi**2 * sigma**2 * (fx**2 + fy**2))
    restored = np.fft.irfft2(spectrum * response / (response**2 + noise_to_signal), s=gray.shape)
    return np.clip(restored, 0, 255).astype(np.uint8)


def unsharp_mask(gray: np.ndarray, sigma: float = 2.0, amount: float = 2.0) -> np.ndarray:
    """Sharpen by adding back the difference between the image and a blurred copy."""
    blurred = cv2.GaussianBlur(gray, (0, 0), sigma)
    return cv2.addWeighted(gray, 1 + amount, blurred, -amount, 0)


def _read(gray: np.ndarray) -> list[zxingcpp.Barcode]:
    """Run zxing-cpp on one grayscale view and keep symbols that carry bytes."""
    return [item for item in zxingcpp.read_barcodes(np.ascontiguousarray(gray), formats=FORMATS) if item.bytes]


def _is_valid_gs1(item: zxingcpp.Barcode) -> bool:
    """Tell whether a decoded symbol is GS1 data that parses completely."""
    if item.content_type != zxingcpp.ContentType.GS1:
        return False
    try:
        parse_gs1(item.bytes.decode("latin-1"))
    except ValueError:
        return False
    return True


def crop_views(gray: np.ndarray) -> Iterator[tuple[str, float, np.ndarray]]:
    """Yield (name, scale, image) decode attempts for a small crop, most promising first.

    Deblur strengths, scales and thresholds are combined: multi-scale and
    multi-threshold decoding. The first attempts are the ones that worked most
    often on the dev seeds, so easy cases stop early.
    """
    enhanced = [(f"wiener{sigma}", wiener_deblur(gray, sigma)) for sigma in DEBLUR_SIGMAS]
    enhanced.append(("unsharp", unsharp_mask(gray)))
    enhanced.append(("plain", gray))
    for threshold in ("none", "otsu", "adaptive"):
        for scale in CROP_SCALES:
            for name, view in enhanced:
                resized = cv2.resize(view, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                if threshold == "otsu":
                    _, resized = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                elif threshold == "adaptive":
                    block = 2 * (max(15, min(resized.shape) // 2) // 2) + 1
                    resized = cv2.adaptiveThreshold(
                        resized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block, 0
                    )
                yield f"{name}_x{scale:g}_{threshold}", scale, resized


def locate_barcode_candidates(gray: np.ndarray, max_candidates: int = 10) -> list[np.ndarray]:
    """Find compact dark regions that could hold a barcode, as 4-corner boxes.

    After smoothing, a barcode is a solid grey block, darker than the paper
    around it. Pixels clearly darker than a local estimate of the paper
    brightness are grouped into connected regions; each region's minimum-area
    rotated rectangle is a candidate if it is big enough and well filled.
    Text lines and pictograms also pass. That is fine, they simply fail to
    decode. Candidates are sorted with the best filled, largest boxes first.
    """
    if gray.ndim != 2 or gray.dtype != np.uint8:
        raise ValueError("Expected a uint8 grayscale image")
    height, width = gray.shape
    short_side = min(height, width)
    smooth = cv2.GaussianBlur(gray, (0, 0), max(1.5, short_side / 350))
    kernel_size = 2 * max(7, short_side // 30) + 1
    paper = cv2.dilate(smooth, np.ones((kernel_size, kernel_size), np.uint8))
    paper = cv2.GaussianBlur(paper, (0, 0), kernel_size / 2)
    dark = (smooth.astype(np.float32) < 0.82 * paper.astype(np.float32)).astype(np.uint8)
    close = 2 * max(1, short_side // 300) + 1
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((close, close), np.uint8))
    # RETR_CCOMP also reports regions that lie inside a closed dark ring, such as
    # everything enclosed by a printed label border. Holes (entries with a parent) are skipped.
    contours, hierarchy = cv2.findContours(dark, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    scored = []
    for index, contour in enumerate(contours):
        if hierarchy[0][index][3] != -1:
            continue
        area = cv2.contourArea(contour)
        if area < 0.0006 * height * width or area > 0.25 * height * width:
            continue
        (cx, cy), (w, h), angle = cv2.minAreaRect(contour)
        if min(w, h) < max(8.0, short_side / 90) or w * h <= 0:
            continue
        fill = area / (w * h)
        if fill < 0.6:
            continue
        scored.append((fill * np.sqrt(area), cv2.boxPoints(((cx, cy), (w, h), angle))))
    scored.sort(key=lambda item: -item[0])
    return [box.astype(np.float32) for _, box in scored[:max_candidates]]


def _upright_crop(gray: np.ndarray, box: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Cut a rotated box out as an upright, landscape crop with a quiet margin.

    Returns the crop and the 3 by 3 matrix that maps crop pixels back to the
    source image. This is the rotation try: whatever angle the barcode has in
    the photo, the decoder sees it level.
    """
    edges = [np.linalg.norm(box[(i + 1) % 4] - box[i]) for i in range(4)]
    start = int(np.argmax(edges))
    ordered = np.roll(box, -start, axis=0)
    long_side, short_side = edges[start], edges[(start + 1) % 4]
    margin = 0.25 * short_side + 6
    out_w, out_h = int(round(long_side + 2 * margin)), int(round(short_side + 2 * margin))
    target = np.array(
        [
            [margin, margin], [margin + long_side, margin],
            [margin + long_side, margin + short_side], [margin, margin + short_side],
        ],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(ordered.astype(np.float32), target)
    crop = cv2.warpPerspective(gray, matrix, (out_w, out_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return crop, np.linalg.inv(matrix)


def _to_result(
    item: zxingcpp.Barcode, to_source: np.ndarray, image_size: tuple[int, int]
) -> tuple[BarcodeResult, list[str]]:
    """Convert a zxing symbol to the shared schema, mapping its corners to source pixels."""
    warnings = []
    raw = item.bytes.decode("latin-1")
    parsed: dict[str, str] = {}
    if item.content_type == zxingcpp.ContentType.GS1:
        try:
            parsed = parse_gs1(raw)
        except ValueError as error:
            warnings.append(f"GS1_PARSE_FAILED: {error}")
    else:
        warnings.append("NON_GS1_BARCODE: raw data retained without GS1 parsing")
    position = item.position
    corners = np.array(
        [[[p.x, p.y] for p in (position.top_left, position.top_right, position.bottom_right, position.bottom_left)]],
        dtype=np.float64,
    )
    points = cv2.perspectiveTransform(corners, to_source)[0]
    width, height = image_size
    points[:, 0] = np.clip(points[:, 0], 0, width)
    points[:, 1] = np.clip(points[:, 1], 0, height)
    left, top = points.min(axis=0)
    right, bottom = points.max(axis=0)
    bbox = None
    if np.isfinite(points).all() and right > left and bottom > top:
        bbox = (float(left), float(top), float(right - left), float(bottom - top))
    else:
        warnings.append("BARCODE_POSITION_INVALID: raw data retained without a bounding box")
    return BarcodeResult(type=str(item.format), raw=raw, parsed=parsed, bbox=bbox), warnings


def decode_crop(
    gray: np.ndarray, to_source: np.ndarray, image_size: tuple[int, int]
) -> tuple[list[BarcodeResult], list[str], str | None]:
    """Try every enhancement on one crop and stop at the first complete GS1 decode."""
    for name, scale, view in crop_views(gray):
        valid = [item for item in _read(view) if _is_valid_gs1(item)]
        if valid:
            unscale = to_source @ np.diag([1 / scale, 1 / scale, 1.0])
            result, warnings = _to_result(valid[0], unscale, image_size)
            return [result], warnings, name
    return [], [], None


def decode_barcodes_blind(
    image: np.ndarray, *, whole_image_fallback: bool = True
) -> tuple[list[BarcodeResult], list[str], str | None]:
    """Decode barcodes in an RGB image without any layout knowledge.

    Order: (1) the image as it is; (2) each located candidate region, levelled
    and tried with every deblur, scale and threshold combination; (3) the
    whole image deblurred and upscaled twice. Stages 2 and 3 accept only
    complete GS1 decodes, because aggressive enhancement of a non-barcode
    region must never produce a result. Returns results with boxes in the
    input image's pixels, warnings, and the name of the attempt that worked.
    """
    _validate_image(image)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    size = (image.shape[1], image.shape[0])
    identity = np.eye(3)
    plain = _read(gray)
    if plain:
        results, warnings = [], []
        for item in plain:
            result, item_warnings = _to_result(item, identity, size)
            results.append(result)
            warnings.extend(item_warnings)
        return results, warnings, "plain"
    for box in locate_barcode_candidates(gray):
        crop, to_source = _upright_crop(gray, box)
        results, warnings, name = decode_crop(crop, to_source, size)
        if results:
            return results, warnings, f"located_{name}"
    if whole_image_fallback:
        for sigma in DEBLUR_SIGMAS[:4]:
            view = cv2.resize(wiener_deblur(gray, sigma), None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            valid = [item for item in _read(view) if _is_valid_gs1(item)]
            if valid:
                result, warnings = _to_result(valid[0], np.diag([0.5, 0.5, 1.0]), size)
                return [result], warnings, f"whole_wiener{sigma}_x2"
    return [], ["BARCODE_NOT_DECODED: blind decoding found no barcode"], None


def decode_barcode_slot_enhanced(image: np.ndarray) -> tuple[list[BarcodeResult], list[str], str | None]:
    """Template-assisted decode: crop the known barcode slot, then deblur, scale and threshold it.

    This is the template-dependent counterpart of ``decode_barcodes_blind``.
    It uses the slot position from the test-device template on an upright,
    corrected label and the same enhancement attempts as the blind mode.
    Boxes are in the corrected image's pixels.
    """
    _validate_image(image)
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    slots = [slot for slot in template["slots"] if slot["type"] == "barcode"]
    if len(slots) != 1:
        raise ValueError("Slot recovery supports exactly one barcode slot")
    height, width = image.shape[:2]
    scale_x = (width - 1) / template["size_mm"]["w"]
    scale_y = (height - 1) / template["size_mm"]["h"]
    x, y, slot_width, slot_height = slots[0]["bbox_mm"]
    padding = 3.0
    left = max(0, round((x - padding) * scale_x))
    top = max(0, round((y - padding) * scale_y))
    right = min(width, round((x + slot_width + padding) * scale_x))
    bottom = min(height, round((y + slot_height + padding) * scale_y))
    if right - left < 15 or bottom - top < 15:
        return [], ["BARCODE_SLOT_TOO_SMALL: corrected image cannot resolve the template slot"], None
    gray = cv2.cvtColor(image[top:bottom, left:right], cv2.COLOR_RGB2GRAY)
    to_source = np.array([[1.0, 0.0, left], [0.0, 1.0, top], [0.0, 0.0, 1.0]])
    results, warnings, name = decode_crop(gray, to_source, (width, height))
    if not results:
        return [], ["BARCODE_NOT_DECODED: enhanced template-slot recovery found no barcode"], None
    return results, warnings, name
