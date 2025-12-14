from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Dict, FrozenSet, Iterable, List, Tuple

import networkx as nx


Pair = Tuple[int, int]  # (min(u,v), max(u,v))


def _pair(u, v) -> Pair:
    return (u, v) if u < v else (v, u)


@dataclass
class CRimpResult:
    c_ii: Dict[int, int]
    c_ij: Dict[Pair, int]
    k_t: Dict[int, int]
    r_imp: Dict[int, float]
    cycles3: List[FrozenSet[int]]
    cycles4: List[FrozenSet[int]]


def find_chordless_triangles(G: nx.Graph) -> List[FrozenSet[int]]:
    """
    All 3-cycles are chordless by definition.
    Returns unique triangles as frozensets.
    """
    triangles: set[FrozenSet[int]] = set()
    # Efficient-ish triangle enumeration using neighbor intersections
    for u in G.nodes():
        Nu = set(G.neighbors(u))
        for v in Nu:
            if v <= u:
                continue
            Nv = set(G.neighbors(v))
            common = Nu & Nv
            for w in common:
                if w <= v:
                    continue
                triangles.add(frozenset((u, v, w)))
    return sorted(triangles, key=lambda s: tuple(sorted(s)))


def find_chordless_4cycles(G: nx.Graph) -> List[FrozenSet[int]]:
    """
    Enumerate chordless 4-cycles (squares) using the 'two common neighbors' trick.

    A chordless 4-cycle u-a-v-b-u can be found when:
      - u and v have two distinct common neighbors a and b
      - u-v is NOT an edge (otherwise u-v would be a chord/diagonal)
      - a-b is NOT an edge (otherwise a-b would be a chord/diagonal)

    Returns unique 4-cycles as frozensets of 4 nodes.
    """
    nodes = list(G.nodes())
    squares: set[FrozenSet[int]] = set()

    # Iterate over unordered pairs (u, v)
    for i in range(len(nodes)):
        u = nodes[i]
        Nu = set(G.neighbors(u))
        for j in range(i + 1, len(nodes)):
            v = nodes[j]
            if G.has_edge(u, v):
                # u-v would be a diagonal chord in any u-a-v-b-u square
                continue

            common = Nu & set(G.neighbors(v))
            if len(common) < 2:
                continue

            # Each pair of common neighbors defines a candidate square
            for a, b in combinations(sorted(common), 2):
                if a == b:
                    continue
                if G.has_edge(a, b):
                    # a-b would be the other diagonal chord
                    continue
                squares.add(frozenset((u, v, a, b)))

    return sorted(squares, key=lambda s: tuple(sorted(s)))


def build_cycle_counts(
    cycles: Iterable[FrozenSet[int]],
) -> Tuple[Dict[int, int], Dict[Pair, int]]:
    """
    Given cycles as node-sets, compute:
      c_ii: how many cycles contain node i
      c_ij: how many cycles contain both i and j (unordered pair)
    """
    c_ii: Dict[int, int] = {}
    c_ij: Dict[Pair, int] = {}

    for cyc in cycles:
        nodes = sorted(cyc)
        for i in nodes:
            c_ii[i] = c_ii.get(i, 0) + 1
        for u, v in combinations(nodes, 2):
            key = _pair(u, v)
            c_ij[key] = c_ij.get(key, 0) + 1

    return c_ii, c_ij


def compute_k_t(G: nx.Graph, c_ij: Dict[Pair, int]) -> Dict[int, int]:
    """
    k_{i,t}: number of neighbors of i that share NO cycle with i.
    i.e. neighbors j where c_ij == 0.
    """
    k_t: Dict[int, int] = {}
    for i in G.nodes():
        cycle_neighbors = 0
        for j in G.neighbors(i):
            if c_ij.get(_pair(i, j), 0) > 0:
                cycle_neighbors += 1
        k_t[i] = G.degree(i) - cycle_neighbors
    return k_t


def compute_crimp_scores(
    G: nx.Graph,
    c_ii: Dict[int, int],
    c_ij: Dict[Pair, int],
    k_t: Dict[int, int],
    include_self: bool = True,
) -> Dict[int, float]:
    """
    Implements Eq.(4) in a practical way:
      If c_ii == 0: r_imp = k_t
      Else: r_imp = sum_{j in {i} U N(i), c_ij>0} c_ij/c_jj + k_t

    include_self=True adds the j=i term (which contributes c_ii/c_ii = 1).
    """
    r: Dict[int, float] = {}

    for i in G.nodes():
        if c_ii.get(i, 0) == 0:
            r[i] = float(k_t.get(i, 0))
            continue

        s = 0.0

        # Optionally include self-term
        if include_self:
            s += 1.0  # c_ii/c_ii

        for j in G.neighbors(i):
            cij = c_ij.get(_pair(i, j), 0)
            if cij <= 0:
                continue
            cjj = c_ii.get(j, 0)
            if cjj and cjj > 0:
                s += cij / cjj

        r[i] = s + float(k_t.get(i, 0))

    return r


def crimp(G: nx.Graph) -> CRimpResult:
    """
    End-to-end: find chordless 3- & 4-cycles, compute counts and CRimp score.
    """
    if G.is_directed():
        raise ValueError("This implementation expects an undirected graph.")

    cycles3 = find_chordless_triangles(G)
    cycles4 = find_chordless_4cycles(G)

    all_cycles = list(cycles3) + list(cycles4)

    c_ii, c_ij = build_cycle_counts(all_cycles)
    k_t = compute_k_t(G, c_ij)
    r_imp = compute_crimp_scores(G, c_ii, c_ij, k_t, include_self=True)

    return CRimpResult(
        c_ii=c_ii,
        c_ij=c_ij,
        k_t=k_t,
        r_imp=r_imp,
        cycles3=cycles3,
        cycles4=cycles4,
    )
