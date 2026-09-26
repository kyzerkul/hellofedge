from collections import Counter
from pathlib import Path

import pytest

from hellofedge.data.reference import (
    COLUMNS,
    PointType,
    ReferenceFileError,
    load_reference,
)

EXEMPLES = Path(__file__).resolve().parents[2] / "exemples"
REFERENCE = EXEMPLES / "reference_oanda.csv"


def test_reference_file_covers_every_capture_with_enough_m3_and_m5_points():
    """AC-1 : au moins un point par capture, dont 5 en M3 et 5 en M5."""
    points = load_reference(REFERENCE)

    captures = {
        p.relative_to(EXEMPLES).as_posix() for p in EXEMPLES.glob("lot-*/*.png")
    }
    assert len(captures) == 19
    assert {p.capture for p in points} == captures
    by_unit = Counter(p.ut for p in points)
    assert by_unit[3] >= 5
    assert by_unit[5] >= 5


def test_reference_file_has_no_duplicate_point():
    points = load_reference(REFERENCE)

    keys = Counter((p.ut, p.ts_open, p.champ, p.type) for p in points)
    assert [k for k, n in keys.items() if n > 1] == []


def test_every_current_candle_open_is_an_exact_point():
    points = load_reference(REFERENCE)

    assert all(p.type is PointType.EXACT for p in points if p.champ == "open")


def write(tmp_path: Path, *rows: str) -> Path:
    path = tmp_path / "ref.csv"
    path.write_text("\n".join([",".join(COLUMNS), *rows]) + "\n", encoding="utf-8")
    return path


def test_reads_a_valid_line(tmp_path):
    path = write(tmp_path, "lot-1/ex3.png,3,exact,2026-08-25T12:15:00Z,159.246,open,O")

    (point,) = load_reference(path)

    assert point.ut == 3
    assert str(point.prix) == "159.246"
    assert point.ts_open.isoformat() == "2026-08-25T12:15:00+00:00"


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ("x.png,3,exact,2026-08-25T12:16:00Z,159.246,open,", "bougie M3"),
        ("x.png,5,exact,2026-08-25T12:16:00Z,159.246,open,", "bougie M5"),
        ("x.png,2,exact,2026-08-25T12:16:00Z,159.246,open,", "1, 3 ou 5"),
        ("x.png,1,exact,2026-08-25T12:16:00+01:00,159.246,open,", "non UTC"),
        ("x.png,1,exact,2026-08-25T12:16:00Z,159.25,open,", "3 décimales"),
        ("x.png,1,borne,2026-08-25T12:16:00Z,159.246,open,", "high ou low"),
        ("x.png,1,environ,2026-08-25T12:16:00Z,159.246,open,", "environ"),
        ("x.png,1,exact,2026-08-25T12:16:00Z,159.246,mid,", "champ inconnu"),
    ],
)
def test_refuses_an_invalid_line_and_names_it(tmp_path, row, message):
    path = write(tmp_path, row)

    with pytest.raises(ReferenceFileError, match=rf"ligne 2 : .*{message}"):
        load_reference(path)


def test_refuses_unexpected_columns(tmp_path):
    path = tmp_path / "ref.csv"
    path.write_text("capture,prix\nx.png,159.246\n", encoding="utf-8")

    with pytest.raises(ReferenceFileError, match="colonnes"):
        load_reference(path)
