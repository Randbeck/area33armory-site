"""Create private, lossless JPEG APP1/EXIF-cleared copies for owner review.

Never rewrites source images, removes no compressed pixel data, and cannot
authorize advertising rights. Rejects non-trivial EXIF orientation rather than
silently changing the pictured product. Full decode/pixel equality is required.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops, UnidentifiedImageError

MAX_BYTES = 16_000_000
MAX_PIXELS = 40_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


class PrivateDerivativeError(ValueError):
    pass


def strip_private_jpeg_metadata(raw: bytes) -> tuple[bytes, dict]:
    """Drop only header-level APP1 (EXIF/XMP), APP13 (IPTC) and comments.

    Retain DCT-encoded scan data verbatim. Keep ICC profiles (APP2) and Adobe
    color interpretation (APP14) to avoid damaging source colors. Reject
    orientation-dependent transformations and any other decoding differences.
    """
    if not isinstance(raw, bytes) or not 12 <= len(raw) <= MAX_BYTES:
        raise PrivateDerivativeError("JPEG original exceeds private verification size")
    if not raw.startswith(b"\xff\xd8"):
        raise PrivateDerivativeError("Not a JPEG start-of-image")
    try:
        with Image.open(BytesIO(raw)) as source:
            if source.format != "JPEG":
                raise PrivateDerivativeError("Not a JPEG")
            if source.width * source.height > MAX_PIXELS:
                raise PrivateDerivativeError("Source pixel limit exceeded")
            orientation = source.getexif().get(274, 1)
            if orientation not in (None, 1):
                raise PrivateDerivativeError(
                    "EXIF orientation needs human inspection; lossless copy held"
                )
            source.load()
            src_image = source.copy()
            tag_ids = sorted(int(key) for key in source.getexif().keys())
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise PrivateDerivativeError("Cannot decode original JPEG") from exc

    out = bytearray(raw[:2])
    at = 2
    removed = {"app1": 0, "app13": 0, "comments": 0}
    saw_scan = False
    while at < len(raw):
        start = at
        if raw[at] != 0xff:
            raise PrivateDerivativeError("Malformed JPEG before first scan")
        while at < len(raw) and raw[at] == 0xff:
            at += 1
        if at >= len(raw):
            raise PrivateDerivativeError("Truncated JPEG marker")
        marker = raw[at]
        at += 1
        if marker == 0xda:  # Start-of-scan: preserve all subsequent bytes verbatim
            if at + 2 > len(raw):
                raise PrivateDerivativeError("Invalid JPEG scan header")
            out.extend(raw[start:])
            saw_scan = True
            break
        if marker in (0xd8, 0xd9, 0x01) or 0xd0 <= marker <= 0xd7:
            raise PrivateDerivativeError("Unexpected JPEG marker before first scan")
        if at + 2 > len(raw):
            raise PrivateDerivativeError("Missing JPEG segment length")
        length = int.from_bytes(raw[at:at + 2], "big")
        end = at + length
        if length < 2 or end > len(raw):
            raise PrivateDerivativeError("Invalid JPEG segment length")
        if marker == 0xe1:
            removed["app1"] += 1
        elif marker == 0xed:
            removed["app13"] += 1
        elif marker == 0xfe:
            removed["comments"] += 1
        else:
            out.extend(raw[start:end])
        at = end
    if not saw_scan or not removed["app1"]:
        raise PrivateDerivativeError("Expected EXIF APP1 metadata was not present")
    copied = bytes(out)
    try:
        with Image.open(BytesIO(copied)) as clean:
            if clean.format != "JPEG" or clean.getexif():
                raise PrivateDerivativeError("Private copy still contains EXIF metadata")
            clean.load()
            if (clean.size != src_image.size or clean.mode != src_image.mode
                    or ImageChops.difference(src_image, clean).getbbox() is not None):
                raise PrivateDerivativeError("Pixels changed during metadata-only copy")
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise PrivateDerivativeError("Derived image failed verification") from exc
    return copied, {
        "source_exif_tag_ids": tag_ids,  # Keys only, NEVER GPS/user values
        "removed_segment_counts": removed,
        "same_compressed_image_scan_preserved": True,
        "private_only": True,
        "advertising_rights_approved": False,
        "publication_approved": False,
    }


def create_private_derivative(
    source_path: Path, output_root: Path, sku: str, filename: str,
    expected_sha256: str,
) -> tuple[Path, str, dict]:
    """Write new image bytes outside Git; never edit or replace original."""
    if not isinstance(source_path, Path) or source_path.is_symlink():
        raise PrivateDerivativeError("Source must be an original regular file")
    raw = source_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise PrivateDerivativeError("Original hash changed since Randbeck verification")
    copied, audit = strip_private_jpeg_metadata(raw)
    target = output_root / sku / filename
    if target.is_symlink() or target.exists() or target.parent.is_symlink():
        raise PrivateDerivativeError("Private derivative file already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as output:
        output.write(copied)
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != expected_sha256:
        target.unlink(missing_ok=True)
        raise PrivateDerivativeError("Original source was changed during copy")
    clean_hash = hashlib.sha256(copied).hexdigest()
    audit.update({
        "source_sha256": expected_sha256,
        "derived_sha256": clean_hash,
        "source_byte_count": len(raw),
        "derived_byte_count": len(copied),
        "private_copy_path": str(target.resolve()),
    })
    return target.resolve(), clean_hash, audit
