#!/usr/bin/env python3
"""Prepare owner-supplied exact-product photos for offline Area 33 review.

No files are written into the public website repository. All publication flags
remain false until a human verifies identity, rights, content and release.

Install dependency: python -m pip install 'Pillow>=11,<13'
Example:
 python scripts/prepare_showroom_photos.py --manufacturer Mossberg \
  --model 'Patriot Super Bantam' --variant '7mm-08 Remington' \
  --photo left=C:/photos/left.jpg --photo right=C:/photos/right.jpg \
  --out C:/Area33-private-photo-review
"""
from __future__ import annotations
import argparse
from html import escape
import json
from pathlib import Path
import re
import secrets
import sys
import warnings

try:
    from PIL import Image, ImageOps, UnidentifiedImageError
except ImportError as e:
    raise SystemExit("Pillow required. Install using: python -m pip install 'Pillow>=11,<13'") from e

Image.MAX_IMAGE_PIXELS = 35_000_000
warnings.simplefilter("error", Image.DecompressionBombWarning)
ID_RE = re.compile(r"^[A-Za-z0-9_-]{12,64}$")
ANGLE_RE = re.compile(r"^[a-z0-9_-]{2,30}$")
MAX_ORIGINAL_BYTES = 40_000_000
VALID_FORMATS = {"JPEG", "PNG", "WEBP"}
REPO_ROOT = Path(__file__).resolve().parent.parent


class IntakeError(ValueError):
    pass


def parse_photos(photo_args):
    if not 2 <= len(photo_args) <= 48:
        raise IntakeError("Provide 2-48 individually labeled photos (for example left=left.jpg).")
    photos = []
    used = set()
    for spec in photo_args:
        if "=" not in spec:
            raise IntakeError("Each --photo must be ANGLE=PATH.")
        angle, name = spec.split("=", 1)
        if not ANGLE_RE.fullmatch(angle) or angle in used:
            raise IntakeError("Angles must be unique lowercase slugs, 2-30 characters.")
        if not name:
            raise IntakeError("A photo path is missing.")
        used.add(angle)
        photos.append((angle, Path(name).expanduser().absolute()))
    return photos


def render_review_html(record):
    title = escape(" ".join(x for x in [record["manufacturer"], record["model"], record["variant"]] if x))
    figures = "\n".join(
        f'<figure><img src="assets/approved/showroom/{escape(record["id"])}/{escape(frame["angle"])}.webp" '
        f'alt="{escape(frame["alt"], quote=True)}" loading="lazy"><figcaption>{escape(frame["angle"].title())}</figcaption></figure>'
        for frame in record["frames"]
    )
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>PRIVATE photo review - {title}</title>"
            "<style>body{background:#131316;color:#fff;font:16px system-ui;margin:0;padding:30px}"
            "main{max-width:1150px;margin:auto}h1{font-size:clamp(28px,5vw,54px)}"
            ".warning{padding:14px;border:1px solid #cf6262;color:#f8c7c7;border-radius:10px}"
            ".gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:22px;margin-top:25px}"
            "figure{margin:0;background:#26262b;padding:12px;border-radius:10px}"
            "img{width:100%;height:340px;object-fit:contain;background:#3c3c43}figcaption{padding:8px}"
            "</style></head><body><main><p>AREA 33 / PRIVATE PHOTO INTAKE</p>"
            f"<h1>{title}</h1><p class=\"warning\">DRAFT ONLY. Not licensed, identity-verified or approved "
            "for publication by this tool. Verify actual model, photo rights, backgrounds and sensitive details.</p>"
            f"<div class=\"gallery\">{figures}</div></main></body></html>\n")


def process_photos(*, manufacturer, model, variant, photo_args, out, public_id=None):
    """Create an off-repository intake bundle and private approval template."""
    manufacturer, model, variant = [str(x).strip() for x in (manufacturer, model, variant)]
    if not manufacturer or not model or any(len(x) > 100 for x in (manufacturer, model, variant)):
        raise IntakeError("Manufacturer and exact model required (max 100 characters per field).")
    photos = parse_photos(photo_args)
    public_id = public_id or "record_" + secrets.token_hex(10)
    if not ID_RE.fullmatch(public_id):
        raise IntakeError("Invalid public ID.")
    root = Path(out).expanduser().resolve()
    if root == REPO_ROOT or root.is_relative_to(REPO_ROOT):
        raise IntakeError("Private review output MUST be outside the public website repository.")
    dest = root / ("area33-review-" + public_id)
    if dest.exists():
        raise IntakeError("Existing review folder; refusing to overwrite: " + str(dest))
    for angle, path in photos:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_ORIGINAL_BYTES:
            raise IntakeError("Photo missing, symlinked or too large: " + str(path))
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise IntakeError("Only JPEG, PNG and WebP photos are supported: " + str(path))
    asset_rel = Path("assets") / "approved" / "showroom" / public_id
    img_dest = dest / asset_rel
    img_dest.mkdir(parents=True, exist_ok=False)
    frames = []
    try:
        for angle, path in photos:
            try:
                with Image.open(path) as src:
                    if src.format not in VALID_FORMATS:
                        raise IntakeError("Photo content is not JPEG/PNG/WebP: " + str(path))
                    src.load()
                    if min(src.size) < 400 or max(src.size) < 800:
                        raise IntakeError("Photo resolution too low for showroom: " + str(path))
                    img = ImageOps.exif_transpose(src)
                    if img.mode in ("RGBA", "LA") or "transparency" in img.info:
                        transparent = img.convert("RGBA")
                        white = Image.new("RGB", transparent.size, (255, 255, 255))
                        white.paste(transparent, mask=transparent.getchannel("A"))
                        img = white
                    else:
                        img = img.convert("RGB")
                    img.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
                    target = img_dest / (angle + ".webp")
                    img.save(target, "WEBP", quality=88, method=6, exif=b"", icc_profile=b"")
                    if target.stat().st_size > 18_000_000:
                        raise IntakeError("Optimized photo exceeds public size limit: " + str(path))
                    with Image.open(target) as verified:
                        verified.verify()
                        if verified.info.get("exif"):
                            raise IntakeError("Camera metadata not stripped.")
            except (OSError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning) as e:
                raise IntakeError("Unable to decode photo: " + str(path)) from e
            frames.append({
                "angle": angle,
                "src": (asset_rel / (angle + ".webp")).as_posix(),
                "alt": f"{manufacturer} {model} {variant}, {angle.replace('-', ' ')} view".strip(),
            })
        record = {
            "id": public_id,
            "status": "draft",
            "manufacturer": manufacturer,
            "model": model,
            "variant": variant,
            "rights_source": "",
            "identity_evidence_label": "",
            "checked_at": "",
            "frames": frames,
            "approvals": {
                "owner_publication": False,
                "exact_identity": False,
                "media_rights": False,
                "content_review": False,
            },
            "configurations": [],
        }
        (dest / "private-review.json").write_text(json.dumps([record], indent=2) + "\n", encoding="utf-8")
        (dest / "review.html").write_text(render_review_html(record), encoding="utf-8")
        (dest / "NEXT_STEPS.txt").write_text(
            "PRIVATE / NOT APPROVED FOR PUBLICATION\n\n"
            "1. Open review.html locally and visually inspect every photo.\n"
            "2. Verify exact manufacturer, model and variant using independent records.\n"
            "3. Confirm permission to publish EACH photo. Inspect for customer faces, names, serials, addresses, plates and sensitive surroundings.\n"
            "4. Keep private-review.json OFF GitHub; record the specific rights source and identity evidence label, current review date, and approve each true flag only after actual review.\n"
            "5. Once approved, change status from draft to published and copy ONLY the 'assets/approved/showroom' photo folder into the website working copy.\n"
            "6. Run python scripts/publish_showroom.py --input PATH_TO_PRIVATE_JSON --publish locally. Inspect sanitized showroom-public.json; run all tests.\n"
            "7. Commit only approved photos and sanitized JSON to site-refresh-v1. Live main deployment needs separate owner approval.\n"
            "8. The intake strips embedded EXIF; it CANNOT reliably detect identifying details visibly printed or pictured.\n",
            encoding="utf-8",
        )
    except Exception:
        import shutil
        shutil.rmtree(dest, ignore_errors=True)
        raise
    return dest


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manufacturer", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--variant", default="")
    p.add_argument("--photo", action="append", required=True, help="ANGLE=PATH. Specify at least two, e.g. left=C:/photos/left.jpg")
    p.add_argument("--out", required=True, help="PRIVATE staging directory OUTSIDE public website repository")
    args = p.parse_args(argv)
    try:
        out = process_photos(manufacturer=args.manufacturer, model=args.model, variant=args.variant,
                             photo_args=args.photo, out=args.out)
    except IntakeError as e:
        p.error(str(e))
    print("PRIVATE photo review created:", out)
    print("Open review.html to inspect; no publication approvals have been granted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
