from pathlib import Path
from typing import Dict, List


def list_scen_files(scen_dir: Path) -> List[Path]:
    return sorted(scen_dir.rglob("*.scen"))


def load_scen_file(path: Path) -> List[Dict[str, object]]:
    """
    Parse MovingAI .scen format.

    Typical line (tab-separated):
    bucket  map_name  width  height  sx  sy  gx  gy  optimal_length

    Notes:
    - sx/gx are x (column), sy/gy are y (row) in MovingAI definition.
    - We convert to grid indexing as (row, col) => (y, x).
    """
    rows: List[Dict[str, object]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.lower().startswith("version"):
            continue
        parts = line.split("\t")
        if len(parts) < 9:
            parts = line.split()
        if len(parts) < 9:
            continue
        bucket, map_name, width, height, sx, sy, gx, gy, opt_len = parts[:9]
        rows.append(
            {
                "bucket": int(bucket),
                "map_name_raw": map_name,
                "map_name": Path(map_name).name,
                "width": int(width),
                "height": int(height),
                "start": (int(sy), int(sx)),
                "goal": (int(gy), int(gx)),
                "optimal_length": float(opt_len),
                "scen_file": path.name,
            }
        )
    return rows


def build_scen_index(scen_dir: Path) -> Dict[str, List[Dict[str, object]]]:
    index: Dict[str, List[Dict[str, object]]] = {}
    for scen_path in list_scen_files(scen_dir):
        for row in load_scen_file(scen_path):
            key = row["map_name"]
            index.setdefault(key, []).append(row)
    return index
