import collections
from functools import lru_cache
import networkx as nx
import matplotlib.pyplot as plt
import random


def enumerate_important_vertex_separators(G: nx.Graph, s, t, k):
    if s == t:
        return {frozenset()}
    if s not in G or t not in G:
        raise ValueError("s and t must be vertices of G")
    if k < 0:
        return set()

    if G.is_directed():
        raise ValueError("G must be undirected")

    X0 = frozenset([s])
    Y0 = frozenset([t])
    D0 = frozenset()

    return _rec_important(G, X0, Y0, k, D0)


def _rec_important(
    G: nx.Graph, X: frozenset, Y: frozenset, k, D: frozenset
):
    """
    Recursive enumeration of important (X,Y)-vertex separators in G - D
    of size ≤ k. (X,Y,D disjoint; terminals in X∪Y cannot be deleted.)
    """

    # Memoization: key is (X,Y,k,D)
    @lru_cache(maxsize=None)
    def rec(
        X: frozenset,
        Y: frozenset,
        k,
        D: frozenset,
    ):
        if k < 0:
            return frozenset()  # empty family

        # If already disconnected, empty separator is the unique important separator here
        if not _exists_path_avoiding(G, X, Y, D):
            return frozenset([frozenset()])

        lam, Rmax = _furthest_min_vertex_cut(G, X, Y, D, k)
        if lam > k:
            return frozenset()

        v = _pick_boundary_vertex(G, Rmax, X, Y, D)
        if v is None:
            # Should not happen when connected, but safe fallback
            return frozenset([frozenset()])

        out = set()

        # Branch 1: take v into separator
        for S in rec(X, Y, k - 1, frozenset(set(D) | {v})):
            out.add(frozenset(set(S) | {v}))

        # Branch 2: force v to the X-side (so v cannot be in the separator)
        for S in rec(frozenset(set(X) | {v}), Y, k, D):
            out.add(S)

        return frozenset(out)

    return set(rec(X, Y, k, D))


def _exists_path_avoiding(
    G: nx.Graph,
    X: frozenset,
    Y: frozenset,
    D: frozenset,
) -> bool:
    """Is there an X-to-Y path in G after deleting vertices in D?"""
    forbidden = set(D)
    targets = set(Y)
    seen = set(forbidden)
    q = collections.deque()

    for x in X:
        if x in forbidden:
            continue
        q.append(x)
        seen.add(x)

    while q:
        u = q.popleft()
        if u in targets:
            return True
        for w in G.neighbors(u):
            if w not in seen and w not in forbidden:
                seen.add(w)
                q.append(w)
    return False


def _pick_boundary_vertex(
    G: nx.Graph,
    Rmax: frozenset,
    X: frozenset,
    Y: frozenset,
    D: frozenset,
):
    """
    Pick any vertex v outside Rmax that has a neighbor in Rmax,
    and is eligible (not in X,Y,D).
    """
    Xset, Yset, Dset = set(X), set(Y), set(D)
    for u in Rmax:
        for v in G.neighbors(u):
            if (
                v not in Rmax
                and v not in Xset
                and v not in Yset
                and v not in Dset
            ):
                return v
    return None


def _furthest_min_vertex_cut(
    G: nx.Graph,
    X: frozenset,
    Y: frozenset,
    D: frozenset,
    k,
) -> tuple[int, frozenset]:
    """
    Return (λ, Rmax) where λ is the min (X,Y)-vertex cut size in G - D
    (unit vertex capacities outside X∪Y), and Rmax is the *furthest*
    min-cut reachable region from X in (G - D) after deleting that cut.

    We compute Rmax from residual reachability after a maxflow in the split network,
    projecting reachable v_out nodes back to original vertices.
    """
    H, SRC, SNK = _build_split_network(G, X, Y, D, k)
    R = nx.algorithms.flow.preflow_push(
        H, SRC, SNK, capacity="capacity"
    )
    flow_value = int(R.graph["flow_value"])

    # Residual BFS from SRC: follow edges with positive residual capacity.
    reachable = set()
    stack = [SRC]
    while stack:
        u = stack.pop()
        if u in reachable:
            continue
        reachable.add(u)
        for v, attr in R[u].items():
            cap = attr.get("capacity", 0)
            flw = attr.get("flow", 0)
            if cap - flw > 0 and v not in reachable:
                stack.append(v)

    # Project: v ∈ Rmax iff v_out is reachable.
    # (This excludes cut vertices whose (v_in->v_out) edge is saturated.)
    Rmax = set()
    for v in G.nodes:
        if v in D:
            continue
        if (v, "out") in reachable:
            Rmax.add(v)

    return flow_value, Rmax


def _build_split_network(
    G: nx.Graph,
    X: frozenset,
    Y: frozenset,
    D: frozenset,
    k,
):
    """
    Build the standard vertex-splitting flow network for unit vertex capacities.
      - each v becomes v_in -> v_out with capacity 1 (unless v in X∪Y, then INF)
      - each undirected edge {a,b} becomes a_out -> b_in and b_out -> a_in with INF
      - super source connects to x_out for x in X (INF)
      - y_in connects to super sink for y in Y (INF)
    """
    H = nx.DiGraph()

    SRC = (
        "__SRC__",
        id(G),
        id(X),
        id(Y),
        id(D),
    )  # unique-ish but hashable
    SNK = ("__SNK__", id(G), id(X), id(Y), id(D))

    # Any INF > k is sufficient since we prune if λ > k
    INF = max(k + 1, len(G) + k + 5)

    Xset, Yset, Dset = set(X), set(Y), set(D)

    # Vertex capacity edges
    for v in G.nodes:
        if v in Dset:
            continue
        vin = (v, "in")
        vout = (v, "out")
        H.add_node(vin)
        H.add_node(vout)

        if v in Xset or v in Yset:
            H.add_edge(vin, vout, capacity=INF)
        else:
            H.add_edge(vin, vout, capacity=1)

    # Edge gadgets (undirected -> two directed arcs)
    for a, b in G.edges:
        if a in Dset or b in Dset:
            continue
        H.add_edge((a, "out"), (b, "in"), capacity=INF)
        H.add_edge((b, "out"), (a, "in"), capacity=INF)

    # Super source / super sink wiring
    H.add_node(SRC)
    H.add_node(SNK)

    for x in Xset:
        if x in Dset:
            continue
        H.add_edge(SRC, (x, "out"), capacity=INF)

    for y in Yset:
        if y in Dset:
            continue
        H.add_edge((y, "in"), SNK, capacity=INF)

    return H, SRC, SNK


from collections import deque


def size_of_s(G, s, t, S):
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

    return len(seen)


def plot(G, s, t, S):
    pos = {n: n for n in G.nodes()}  # use (x,y) coordinates as layout

    plt.figure(figsize=(6, 6))
    nx.draw(G, pos, node_size=80, width=1, with_labels=False)

    # color nodes in S black
    nx.draw_networkx_nodes(
        G, pos, nodelist=list(S), node_color="black", node_size=150
    )

    # highlight s and t
    nx.draw_networkx_nodes(
        G, pos, nodelist=[s], node_color="green", node_size=200
    )
    nx.draw_networkx_nodes(
        G, pos, nodelist=[t], node_color="red", node_size=200
    )

    plt.axis("equal")
    plt.show()


if __name__ == "__main__":
    random.seed(1)
    WIDTH = HEIGHT = 12
    G = nx.grid_2d_graph(WIDTH, HEIGHT)  # undirected
    for i in range(20):
        v = random.choice(list(G.nodes()))
        if 0 in v:
            continue
        G.remove_node(v)
    s = random.choice(list(G.nodes()))
    t = (-2, HEIGHT // 2)
    for i in range(HEIGHT):
        G.add_edge(t, (0, i))

    from datetime import datetime as dt

    for k in range(1, WIDTH):
        start = dt.now()
        print(f"{k = }")
        seps = enumerate_important_vertex_separators(G, s, t, k)
        print(f"important separators: {len(seps)}")
        size_s = 0
        best_S = []
        for S in sorted(seps, key=len):
            csize = size_of_s(G, s, t, S)
            if csize > size_s:
                size_s = csize
                best_S = S
        end = dt.now()
        delta_time = round((end - start).total_seconds(), 2)
        print("optimal size:", size_s)
        print("S:", best_S)
        print("time:", delta_time, "seconds")
        print("\n" * 2)
    # plot(G, s, t, best_S)
