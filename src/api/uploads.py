"""Safe handling of an uploaded file (Step 24a): type, size, pixel count and storage.

Rules, in plain words:
- The type comes from the first bytes of the file (PNG, JPEG or PDF signatures), never from the filename or the
  Content-Type header the client sent.
- The client's filename is not used at all. The stored name is `<sha256>.<ext>`, so a name like `../../x.png`
  cannot escape the uploads folder (and two uploads of the same bytes share one file).
- At most 15 MB (`MAX_BYTES`) and at most 40 million pixels (`MAX_PIXELS`), read from the image header before
  anything is decoded, so a small file that claims a huge canvas ("decompression bomb") is refused.
- PDF files are checked by signature; they are rendered to a PNG of the first page for extraction when the
  optional `pypdfium2` package is installed.
"""

from __future__ import annotations

import hashlib
import io
import os
import re
from dataclasses import dataclass
from pathlib import Path

from src.api.errors import ApiError
from src.api.extractor import ExtractorUnavailable

MAX_BYTES = 15 * 1024 * 1024
MAX_PIXELS = 40_000_000
MIN_SIDE = 64  # a smaller picture cannot hold a readable label
MAX_PDF_PAGES = 50
PDF_DPI = 200
PDF_MAX_SIDE = 4000  # longest side of the rendered page in pixels
UPLOAD_DIR = "uploads"  # under the files folder (data/api by default), git-ignored

SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", "image/png", "png"),
    (b"\xff\xd8\xff", "image/jpeg", "jpg"),
    (b"%PDF-", "application/pdf", "pdf"),
)
PIL_FORMAT = {"image/png": "PNG", "image/jpeg": "JPEG"}
SHA_NAME = re.compile(r"^[0-9a-f]{64}\.(png|jpg|pdf)$")


@dataclass(frozen=True)
class CheckedUpload:
    """A file that passed validation: its bytes' hash, detected type and, for images, the size in pixels."""

    sha256: str
    mime: str
    ext: str
    size: int
    pages: int | None
    pixels: tuple[int, int] | None


def sniff(data: bytes) -> tuple[str, str]:
    """(mime, extension) from the first bytes, or 422 unsupported_media_type. Filenames play no part."""
    for signature, mime, ext in SIGNATURES:
        if data.startswith(signature):
            return mime, ext
    raise ApiError(422, "unsupported_media_type", "Only PNG, JPEG and PDF files can be uploaded.")


def pdf_page_count(data: bytes) -> int | None:
    """Number of pages, or None when the PDF library is not installed. A PDF that cannot be parsed is a 422."""
    try:
        import pypdfium2
    except ImportError:
        return None
    try:
        pdf = pypdfium2.PdfDocument(data)
        count = len(pdf)
        pdf.close()
    except Exception as error:
        raise ApiError(422, "invalid_file", "The PDF could not be read.") from error
    if count < 1 or count > MAX_PDF_PAGES:
        raise ApiError(422, "invalid_file", f"The PDF must have between 1 and {MAX_PDF_PAGES} pages.")
    return count


def image_size(data: bytes, mime: str) -> tuple[int, int]:
    """Pixel size from the header (nothing is decoded), after checking the file really is that format."""
    from PIL import Image

    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format != PIL_FORMAT[mime]:
                raise ApiError(422, "invalid_file", "The file content does not match its type.")
            size = image.size
    except ApiError:
        raise
    except Image.DecompressionBombError as error:
        raise ApiError(422, "image_too_large", f"The image has more than {MAX_PIXELS:,} pixels.") from error
    except Exception as error:
        raise ApiError(422, "invalid_file", "The image could not be read.") from error
    return size


def validate_upload(data: bytes) -> CheckedUpload:
    """Run every check on the raw bytes. Raises ApiError (422) with a specific code on the first failure."""
    if not data:
        raise ApiError(422, "invalid_file", "The file is empty.")
    if len(data) > MAX_BYTES:
        raise ApiError(422, "file_too_large", f"The file is larger than {MAX_BYTES // (1024 * 1024)} MB.")
    mime, ext = sniff(data)
    pages: int | None = None
    pixels: tuple[int, int] | None = None
    if mime == "application/pdf":
        pages = pdf_page_count(data)
    else:
        pages = 1
        pixels = image_size(data, mime)
        width, height = pixels
        if width * height > MAX_PIXELS:
            raise ApiError(422, "image_too_large", f"The image has more than {MAX_PIXELS:,} pixels.")
        if min(width, height) < MIN_SIDE:
            raise ApiError(422, "invalid_file", f"The image is smaller than {MIN_SIDE} pixels on one side.")
        try:  # check the whole stream (PNG chunk CRCs, JPEG markers) without decoding the pixels
            from PIL import Image

            with Image.open(io.BytesIO(data)) as image:
                image.verify()
        except Exception as error:
            raise ApiError(422, "invalid_file", "The image file is damaged.") from error
    return CheckedUpload(hashlib.sha256(data).hexdigest(), mime, ext, len(data), pages, pixels)


def uploads_root(files_dir: Path) -> Path:
    """The uploads folder, created on demand."""
    root = files_dir / UPLOAD_DIR
    root.mkdir(parents=True, exist_ok=True)
    return root


def relative_path(upload: CheckedUpload) -> str:
    """Path stored in the database, relative to the files folder. Built only from the hash and detected type."""
    return f"{UPLOAD_DIR}/{upload.sha256}.{upload.ext}"


def resolve_stored(files_dir: Path, relative: str) -> Path:
    """Absolute path of a stored upload. Refuses anything that is not `uploads/<sha256>.<ext>` (no traversal)."""
    folder, _, name = relative.partition("/")
    if folder != UPLOAD_DIR or not SHA_NAME.match(name):
        raise ApiError(404, "artwork_not_found", "The stored upload path is not valid.")
    path = (files_dir / UPLOAD_DIR / name).resolve()
    if (files_dir / UPLOAD_DIR).resolve() not in path.parents:
        raise ApiError(404, "artwork_not_found", "The stored upload path is not valid.")
    return path


def store_bytes(files_dir: Path, upload: CheckedUpload, data: bytes) -> str:
    """Write the file once under its hash name (atomic: temp file, then rename). Returns the relative path."""
    target = resolve_stored(files_dir, relative_path(upload))
    uploads_root(files_dir)
    if not target.exists():
        temp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        temp.write_bytes(data)
        os.replace(temp, target)
    return relative_path(upload)


def render_pdf_page(pdf_path: Path, out_png: Path) -> None:
    """Render page 1 of a PDF to a PNG (200 dpi, longest side at most 4000 px). Needs `pypdfium2`."""
    try:
        import pypdfium2
    except ImportError as error:
        raise ExtractorUnavailable(f"PDF rendering is not installed (pypdfium2): {error}") from error
    pdf = pypdfium2.PdfDocument(str(pdf_path))
    try:
        page = pdf[0]
        width, height = page.get_size()
        scale = min(PDF_DPI / 72, PDF_MAX_SIDE / max(width, height))
        page.render(scale=scale).to_pil().convert("RGB").save(out_png, format="PNG")
    finally:
        pdf.close()
