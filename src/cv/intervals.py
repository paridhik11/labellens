"""Add Wilson 95% intervals to the headline rates of the CV reports, from the counts already in them.

Nothing is re-run: each table cell of the form ``k/n`` or ``k/n (p%)`` in the
chosen columns becomes ``k/n (p%; 95% CI lo to hi%)``. Run from the repo root:

    python -m src.cv.intervals

The Wilson score interval is used instead of p plus or minus 1.96 standard
errors because that simple interval collapses to zero width at 0/n and n/n,
which would wrongly suggest certainty from 51 images. Wilson gives, for
example, 93.0% to 100% for 51/51.
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

Z_95 = 1.959963984540054
_CELL = re.compile(r"^(\d+)/(\d+)(?: \((\d+(?:\.\d+)?)%\))?$")

# (file, start of the table's header row, zero-based column indices to annotate,
#  optional text that the first cell of a row must contain).
TABLES: tuple[tuple[str, str, tuple[int, ...], str], ...] = (
    ("results/cv_final_eval.md", "| Condition | Images | Exact GS1 | Symbols IoU>=0.5 |", (2, 3), ""),
    ("results/cv_final_eval.md", "| Condition | Images | Exact GS1, blind |", (2, 3, 4, 6), ""),
    ("results/cv_final_eval.md", "| Decoder | Original hard (blur to 1.8, noise 8) |", (1, 2), ""),
    ("results/cv_final_eval.md", "| Case | Condition | Mode | Images | Present symbols matched |", (4, 5), ""),
    ("results/cv_final_eval.md", "| Case | Condition | Images | Present symbols matched |", (3, 4), ""),
    ("results/cv_fixes.md", "| Condition | Exact GS1: before |", (1, 2, 3, 7, 8), ""),
    ("results/cv_fixes.md", "| Decoder | Original hard | Reduced hard |", (1, 2), ""),
    ("results/cv_fixes.md", "| Case | Measure | Before |", (2, 3, 4), "symbol"),
)


def wilson_interval(successes: int, trials: int, z: float = Z_95) -> tuple[float, float]:
    """Return the Wilson score interval for a binomial proportion, as fractions from 0 to 1."""
    if trials <= 0 or not 0 <= successes <= trials:
        raise ValueError("Need 0 <= successes <= trials and trials > 0")
    p = successes / trials
    denominator = 1 + z**2 / trials
    centre = (p + z**2 / (2 * trials)) / denominator
    half = z * math.sqrt(p * (1 - p) / trials + z**2 / (4 * trials**2)) / denominator
    return max(0.0, centre - half), min(1.0, centre + half)


def annotate_cell(cell: str) -> str:
    """Add a Wilson interval to one ``k/n`` cell; leave any other text (or n of 0) unchanged."""
    text = cell.strip()
    match = _CELL.match(text)
    if match is None or "CI" in text:
        return cell
    successes, trials = int(match.group(1)), int(match.group(2))
    if trials == 0 or successes > trials:
        return cell
    low, high = wilson_interval(successes, trials)
    return f" {successes}/{trials} ({100 * successes / trials:.1f}%; 95% CI {100 * low:.1f} to {100 * high:.1f}%) "


def annotate_table(lines: list[str], header_prefix: str, columns: tuple[int, ...], row_filter: str = "") -> int:
    """Annotate the given columns of the first table whose header starts with ``header_prefix``.

    Returns the number of header rows found (0 or 1); the lines are changed in place.
    """
    start = next((position for position, line in enumerate(lines) if line.startswith(header_prefix)), None)
    if start is None:
        return 0
    index = start + 2
    while index < len(lines) and lines[index].startswith("|"):
        cells = lines[index].split("|")[1:-1]
        if row_filter in cells[0] or row_filter in "|".join(cells[:2]):
            for column in columns:
                if column < len(cells):
                    cells[column] = annotate_cell(cells[column])
            lines[index] = "|" + "|".join(cells) + "|"
        index += 1
    return 1


def main(argv: list[str] | None = None) -> int:
    """Annotate the report tables listed in ``TABLES``."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args(argv)
    for name in dict.fromkeys(table[0] for table in TABLES):
        path = Path(name)
        lines = path.read_text(encoding="utf-8").splitlines()
        found = sum(annotate_table(lines, prefix, columns, row_filter) for file, prefix, columns, row_filter in TABLES
                    if file == name)
        expected = sum(1 for table in TABLES if table[0] == name)
        if found != expected:
            raise SystemExit(f"{name}: found {found} of {expected} tables; nothing written")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        print(f"{name}: annotated {found} tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
