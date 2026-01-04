from __future__ import annotations

import networkx as nx


class CycleRatioEngine:
    """
    Baseline Cycle Ratio implementation (as provided by mentor),
    fixed for Python (__init__) and returns a score dict.
    """

    def __init__(self, graph: nx.Graph):
        self.graph = graph
        self.CycleRatio: dict = {}
        self.cycles: set = set()

    def run(self) -> dict:
        for node in self.graph.nodes():
            neighbors = list(self.graph.neighbors(node))
            if len(neighbors) < 2:
                continue

            G_temp = self.graph.copy()
            G_temp.remove_node(node)

            for i in range(len(neighbors)):
                for j in range(i + 1, len(neighbors)):
                    u, v = neighbors[i], neighbors[j]

                    if self.graph.has_edge(u, v):
                        self.cycles.add(tuple(sorted((node, u, v))))
                    else:
                        try:
                            paths = list(nx.all_shortest_paths(G_temp, source=u, target=v))
                            for p in paths:
                                self.cycles.add(tuple(sorted([node] + list(p))))
                        except nx.NetworkXNoPath:
                            continue

        cycle_map = {n: [] for n in self.graph.nodes()}
        for cyc in self.cycles:
            for n in cyc:
                cycle_map[n].append(cyc)

        for i in self.graph.nodes():
            c_ii = len(cycle_map[i])
            if c_ii == 0:
                self.CycleRatio[i] = 0.0
                continue

            shared_counts = {}
            for cyc in cycle_map[i]:
                for n in cyc:
                    shared_counts[n] = shared_counts.get(n, 0) + 1

            score = 0.0
            for j, c_ij in shared_counts.items():
                if j == i:
                    continue
                c_jj = len(cycle_map[j])
                if c_jj > 0:
                    score += (c_ij / c_jj)

            self.CycleRatio[i] = float(score)

        return self.CycleRatio


def rank_cycle_ratio_base(G: nx.Graph) -> dict:
    return CycleRatioEngine(G).run()


def rank_degree(G: nx.Graph) -> dict:
    return {n: float(G.degree(n)) for n in G.nodes()}


def rank_betweenness(G: nx.Graph) -> dict:
    bc = nx.betweenness_centrality(G, normalized=True)
    return {n: float(bc[n]) for n in G.nodes()}


def rank_pagerank(G: nx.Graph) -> dict:
    pr = nx.pagerank(G)
    return {n: float(pr[n]) for n in G.nodes()}
