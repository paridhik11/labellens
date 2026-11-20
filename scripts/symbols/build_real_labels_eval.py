"""Build the real-label evaluation set from the DailyMed images in ``data/real_labels/`` (not committed).

The boxes below were read by the assistant (Claude) from zoomed crops of each image with a coordinate grid, on
2026-11-15. They are **LLM-labelled, not human-labelled**, and a human should re-check them. Only symbols that are the
manufacturer pictogram (ISO 7000-3082) or the use-by hourglass (ISO 7000-2607) are marked; the factory-with-date icon
on the lancet carton is the date-of-manufacture symbol and is not marked as a manufacturer symbol.

    python scripts/symbols/build_real_labels_eval.py
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "real_labels"
OUT = ROOT / "data" / "real_labels_eval"
TIME = "2026-11-15"

# item name -> (source image, present symbols {name: (x, y, w, h)}, note)
ITEMS = {
    "lancet_format_block": ("d491f12b__label_pic.jpg", {"expiry": (406, 753, 10, 15)},
                            "hourglass in the printed-format block; the second hourglass (368,446,8,11) is not in this item"),
    "lancet_side_panel": ("d491f12b__label_pic.jpg", {"expiry": (368, 446, 8, 11)},
                          "hourglass in the carton side panel; the format-block hourglass is not in this item"),
    "pregnancy_test_back": ("69932e8d__Preg_Cont_back.jpg", {"manufacturer": (458, 1370, 36, 35)},
                            "manufacturer pictogram on the side flap, turned 90 degrees"),
    "glucose_strip_box_a": ("c7b67525__I_D_L1243_704113285_02_50_TDG_STS_Box_E_2P1.jpg", {}, "no pictograms"),
    "glucose_strip_box_b": ("6d1aee93__I_D_L1243_704113285_01_50_TDG_STS_Box_E_2P1.jpg", {}, "no pictograms"),
    "glucose_kit_box": ("0e2498a8__I_D_L1241_704113283_02_TDG_SKit_Box_E.jpg", {}, "no pictograms"),
    "glucose_voice_kit_box": ("82984eb0__I_D_L1242_704113284_02_TDG_Voice_SKit_Box_E.jpg", {}, "no pictograms"),
}


def main() -> int:
    """Copy the images and write truth files in the same format as the synthetic sets."""
    if OUT.exists():
        shutil.rmtree(OUT)
    folder = OUT / "real_label"
    folder.mkdir(parents=True)
    manifest = {"generator": "scripts/symbols/build_real_labels_eval.py", "format_version": 1, "split": "real",
                "straighten": False, "labelled_by": f"LLM (Claude), {TIME}; not human", "files": []}
    for name, (source, present, note) in ITEMS.items():
        shutil.copy(SRC / source, folder / f"{name}.jpg")
        entries = [{"name": key, "style": name, "scale": 1.0,
                    "quad_px": [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]} for key, (x, y, w, h) in present.items()]
        truth = {"label_id": name, "case": "real_label", "split": "real", "style": name, "condition": "real",
                 "expected_symbols": ["manufacturer", "expiry"], "present_symbols": entries, "distractor_symbols": [],
                 "labelled_by": f"LLM (Claude), {TIME}; not human", "note": note, "source_image": source}
        (folder / f"{name}.json").write_text(json.dumps(truth, indent=2) + "\n", encoding="utf-8")
        manifest["files"].append({"image": f"real_label/{name}.jpg", "ground_truth": f"real_label/{name}.json"})
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(ITEMS)} items to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
