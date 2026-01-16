from collections import deque

import networkx as nx

#import random

from important import important_separators

WIDTH = HEIGHT = 12
T_NODE = (-2, HEIGHT // 2)
#random.seed(str(T_NODE))

FS = frozenset


def s_component(G, s, t, S):
    S = set(S)
    if s in S:
        return 0

    seen = {s}
    q = deque([s])

    while q:
        u = q.popleft()
        for v in G.neighbors(u):
            if v in S or v in seen:
                continue
            seen.add(v)
            q.append(v)

    return FS(seen)




REMOVE_IN_ROW = []
_ = REMOVE_IN_ROW
_.append([0, 1, 3, 4, 8, 9, 10, 11])
_.append([3, 6])
_.append([0, 5, 6, 8, 9, 10])
_.append([4, 10, 11])
_.append([0, 1, 3, 6, 7, 8, 11])
_.append([0, 5, 9])
_.append([0, 2, 3, 5, 7, 9, 11])
_.append([0, 3, 7, 9, 11])
_.append([4, 5, 6, 9])
_.append([0, 2, 9, 11])
_.append([0, 3, 5, 7, 11])
_.append([0, 1, 5, 7, 8, 9, 11])


if __name__ == "__main__":
    G = nx.grid_2d_graph(WIDTH, HEIGHT)  # undirected
    for r, row in enumerate(REMOVE_IN_ROW):
        for c in row:
            v = (c, r)
            G.remove_node(v)
            G.add_node(v)
    s = (6, 5)
    t = T_NODE
    for i in range(HEIGHT):
        G.add_edge(t, (0, i))
        G.add_edge(t, (WIDTH - 1, i))
    for i in range(WIDTH):
        G.add_edge(t, (i, 0))
        G.add_edge(t, (i, HEIGHT - 1))

    from datetime import datetime as dt

    import sys

    K = int(sys.argv[1])
    for k in [K]:
        start = dt.now()
        print(f"{k = }")
        seps = important_separators(G, s, t, k)
        all_seps = set()
        size_s = 0
        best_S = []
        R = set()  # reachability
        for S in seps:
            all_seps.add(S)
            cR = s_component(G, s, t, S)
            if len(cR) > size_s:
                R = cR
                size_s = len(R)
                best_S = S
                print(size_s, end=".. ")
        print()
        end = dt.now()
        delta_time = round((end - start).total_seconds(), 2)
        print(f"important separators: {len(all_seps)}")
        print("optimal size:", size_s)
        print("S:", best_S)
        print("time:", delta_time, "seconds")
        print("\n" * 2)
        # from plot import plot
        # plot(G, s, t, best_S, R)
