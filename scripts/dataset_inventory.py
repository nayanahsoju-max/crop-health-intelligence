"""Inspect the checked-in crop datasets without changing any dataset files."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def image_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)


def verify_images(paths: list[Path]) -> tuple[list[Path], Counter, Counter]:
    bad: list[Path] = []
    formats: Counter = Counter()
    sizes: Counter = Counter()
    def inspect(path: Path) -> tuple[Path, tuple[int, int] | None]:
        try:
            with Image.open(path) as image:
                size = image.size
                image.verify()
            return path, size
        except Exception:
            return path, None

    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(inspect, path) for path in paths]
        for index, future in enumerate(as_completed(futures), 1):
            path, size = future.result()
            formats[path.suffix.lower()] += 1
            if size is None:
                bad.append(path)
            else:
                sizes[size] += 1
            if index % 5000 == 0:
                print(f"  verified {index}/{len(paths)}", flush=True)
    return bad, formats, sizes


def class_counts(root: Path, split: str | None = None) -> dict[str, int]:
    base = root / split if split else root
    counts: dict[str, int] = {}
    for folder in sorted(p for p in base.iterdir() if p.is_dir()):
        count = sum(1 for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)
        if count:
            name = folder.name
            if name == "PlantVillage" and not split:
                # Keep the nested extraction visible as a distinct path namespace.
                for child in sorted(p for p in folder.iterdir() if p.is_dir()):
                    child_count = sum(1 for p in child.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)
                    if child_count:
                        counts[f"PlantVillage/{child.name}"] = child_count
            else:
                counts[name] = count
    return counts


def report_dataset(name: str, paths: list[Path]) -> list[Path]:
    bad, formats, sizes = verify_images(paths)
    print(f"\n{name}: images={len(paths)} unreadable={len(bad)} formats={dict(formats)}")
    if sizes:
        widths, heights = zip(*sizes)
        print(f"  dimensions: width={min(widths)}..{max(widths)}, height={min(heights)}..{max(heights)}, unique={len(sizes)}")
    if bad:
        for path in bad[:50]:
            print(f"  UNREADABLE {path.relative_to(ROOT)}")
        if len(bad) > 50:
            print(f"  ... and {len(bad) - 50} more")
    return bad


def plantseg_report() -> tuple[dict[tuple[str, str], dict[str, int]], dict[tuple[str, str], int]]:
    root = DATA / "plantsegv3"
    by_class: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    metadata_rows: list[dict[str, str]] = []
    invalid_metadata: list[str] = []
    with (root / "Metadatav2.csv").open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            metadata_rows.append(row)
            plant = row.get("Plant", "").strip()
            disease = row.get("Disease", "").strip()
            split = row.get("Split", "").strip()
            if not plant or not disease or split.lower() not in {"training", "validation", "test"}:
                invalid_metadata.append(f"{row.get('Name', '<unknown>')}: plant={plant!r} disease={disease!r} split={split!r}")
                continue
            by_class[(plant, disease.lower())][split.lower()] += 1

    pair_totals: Counter = Counter(
        {"metadata_rows": len(metadata_rows), "pairs": 0, "missing_images": 0, "missing_masks": 0,
         "raw_dimension_mismatch": 0, "oriented_dimension_mismatch": 0, "unreadable_pair": 0,
         "invalid_metadata_labels": len(invalid_metadata)}
    )
    pair_bad: list[str] = []
    split_names = {"training": "train", "validation": "val", "test": "test"}
    referenced_images: set[Path] = set()
    referenced_masks: set[Path] = set()
    for row in metadata_rows:
        if not row.get("Plant", "").strip() or not row.get("Disease", "").strip():
            continue
        image_split = split_names.get(row.get("Split", "").strip().lower())
        if image_split is None:
            continue
        image_path = root / "images" / image_split / row["Name"]
        mask_path = root / "annotations" / image_split / row["Label file"]
        referenced_images.add(image_path)
        referenced_masks.add(mask_path)
        if not image_path.is_file():
            pair_totals["missing_images"] += 1
            if len(pair_bad) < 50:
                pair_bad.append(f"missing metadata image: {image_path.relative_to(ROOT)}")
            continue
        if not mask_path.is_file():
            pair_totals["missing_masks"] += 1
            if len(pair_bad) < 50:
                pair_bad.append(f"missing metadata mask: {mask_path.relative_to(ROOT)}")
            continue
        pair_totals["pairs"] += 1
        try:
            with Image.open(image_path) as image, Image.open(mask_path) as mask:
                raw_size = image.size
                orientation = image.getexif().get(274, 1)
                oriented_size = raw_size[::-1] if orientation in (5, 6, 7, 8) else raw_size
                if raw_size != mask.size:
                    pair_totals["raw_dimension_mismatch"] += 1
                if oriented_size != mask.size:
                    pair_totals["oriented_dimension_mismatch"] += 1
                    if len(pair_bad) < 50:
                        pair_bad.append(f"dimension mismatch after EXIF orientation: {image_path.name} {oriented_size} vs {mask.size} (stored {raw_size})")
        except Exception as error:
            pair_totals["unreadable_pair"] += 1
            if len(pair_bad) < 50:
                pair_bad.append(f"unreadable pair: {image_path.name}: {error}")

    disk_images = set(image_files(root / "images"))
    disk_masks = set(image_files(root / "annotations"))
    pair_totals["unreferenced_images"] = len(disk_images - referenced_images)
    pair_totals["unreferenced_masks"] = len(disk_masks - referenced_masks)

    json_totals = {}
    for split in ("train", "val", "test"):
        payload = json.loads((root / f"annotation_{split}.json").read_text(encoding="utf-8"))
        json_totals[split] = {
            "images": len(payload.get("images", [])),
            "annotations": len(payload.get("annotations", [])),
            "categories": [(item.get("id"), item.get("name")) for item in payload.get("categories", [])],
        }

    print("\nPlantSeg classes (Plant, disease, Train/Validation/Test/Total):")
    for (plant, disease), splits in sorted(by_class.items()):
        train, val, test = splits.get("training", 0), splits.get("validation", 0), splits.get("test", 0)
        print(f"  {plant} | {disease} | {train}/{val}/{test}/{train + val + test}")
    print(f"PlantSeg mask-pair check: {dict(pair_totals)}")
    print(f"PlantSeg JSON summaries: {json_totals}")
    print(f"PlantSeg invalid metadata label/split rows: {len(invalid_metadata)}")
    for issue in invalid_metadata[:50]:
        print(f"  INVALID LABEL {issue}")
    for issue in pair_bad:
        print(f"  ISSUE {issue}")
    return by_class, dict(pair_totals)


def main() -> None:
    pv_root = DATA / "PlantVillage"
    pv_classes = class_counts(pv_root)
    print("PlantVillage classes (nested extraction is listed separately):")
    for name, count in pv_classes.items():
        print(f"  {name}: {count}")

    pd_root = DATA / "PlantDoc-Selected"
    print("\nPlantDoc classes by supplied split:")
    pd_classes: dict[str, dict[str, int]] = {}
    for split in ("train", "test"):
        pd_classes[split] = class_counts(pd_root, split)
        for name, count in pd_classes[split].items():
            print(f"  {split}/{name}: {count}")

    report_dataset("PlantVillage", image_files(pv_root))
    report_dataset("PlantDoc-Selected", image_files(pd_root))
    report_dataset("PlantSeg images", image_files(DATA / "plantsegv3" / "images"))
    report_dataset("PlantSeg masks", image_files(DATA / "plantsegv3" / "annotations"))
    plantseg_report()


if __name__ == "__main__":
    main()
