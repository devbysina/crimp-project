from __future__ import annotations

from pathlib import Path
import networkx as nx

# Project root = parent of the src directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]

def load_edgelist_txt(path: str | Path, directed: bool = False) -> nx.Graph:
    """
    Load a whitespace-separated edge list (u v) from a .txt file.
    Accepts relative paths resolved against PROJECT_ROOT.
    """
    path = Path(path)
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()

    G = nx.DiGraph() if directed else nx.Graph()

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            a, b = line.split()[:2]
            try:
                a = int(a); b = int(b)
            except ValueError:
                pass
            G.add_edge(a, b)

    return G

DATASETS = {
    "Celegans": "data/raw/Celegans.txt",
    "Email": "data/raw/Email.txt",
    "Jazz": "data/raw/Jazz.txt",
    "NS_GC": "data/raw/NS_GC.txt",
    "USAir": "data/raw/USAir.txt",
    "Yeast": "data/raw/Yeast.txt",
}
