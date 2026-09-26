"""AC-9 : aucun code de `data/` ne peut passer, modifier ou annuler un ordre.

Le test parcourt les noms de fonction, les URL et les chemins d'API du module `data/`
et échoue s'il y trouve un mot interdit.
"""

import ast
import re
from pathlib import Path

import hellofedge.data

DATA_DIR = Path(hellofedge.data.__file__).parent
FORBIDDEN = re.compile(r"order|trade|position|close_trade|opentrade|entry", re.I)
# Une URL ou un chemin d'API : pas d'espace et au moins une barre oblique.
LOOKS_LIKE_PATH = re.compile(r"^\S*/\S*$")


def forbidden_names(root: Path) -> list[str]:
    found = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                text = node.name
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                if not LOOKS_LIKE_PATH.match(node.value):
                    continue
                text = node.value
            else:
                continue
            if FORBIDDEN.search(text):
                found.append(f"{path.name}:{node.lineno} {text}")
    return found


def test_data_module_has_no_trading_call():
    assert forbidden_names(DATA_DIR) == []


def test_guard_catches_an_order_function(tmp_path):
    (tmp_path / "adapter.py").write_text("async def place_order(units):\n    ...\n")

    assert forbidden_names(tmp_path) == ["adapter.py:1 place_order"]


def test_guard_catches_a_trading_url(tmp_path):
    (tmp_path / "adapter.py").write_text(
        'URL = "https://api-demo.fxcm.com/trading/open_trade"\n'
        'OK = "https://api-demo.fxcm.com/candles/1/m1"\n'
        'DOC = "Le trader lit les prix / rien d\'autre"\n'
    )

    assert forbidden_names(tmp_path) == [
        "adapter.py:1 https://api-demo.fxcm.com/trading/open_trade"
    ]
