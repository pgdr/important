import collections
from functools import cache
import networkx as nx

FS = frozenset
Ø=FS()

def exists_path_avoiding(G, X, Y, D):
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


def build_split_network(G, X, Y, D, k):
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


def furthest_min_vertex_cut(G, X, Y, D, k):
    """
    Return (λ, Rmax) where λ is the min (X,Y)-vertex cut size in G - D
    (unit vertex capacities outside X∪Y), and Rmax is the *furthest*
    min-cut reachable region from X in (G - D) after deleting that cut.

    We compute Rmax from residual reachability after a maxflow in the split network,
    projecting reachable v_out nodes back to original vertices.
    """
    H, SRC, SNK = build_split_network(G, X, Y, D, k)
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


def pick_boundary_vertex(G, Rmax, X, Y, D):
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


def rec_important(G, X, Y, k, D):
    """
    Recursive enumeration of important (X,Y)-vertex separators in G - D
    of size ≤ k. (X,Y,D disjoint; terminals in X∪Y cannot be deleted.)
    """

    # Memoization: key is (X,Y,k,D)
    @cache
    def rec(X, Y, k, D):
        if k < 0:
            return Ø  # empty family

        # If already disconnected, empty separator is the unique important separator here
        if not exists_path_avoiding(G, X, Y, D):
            return FS([Ø])

        lam, Rmax = furthest_min_vertex_cut(G, X, Y, D, k)
        if lam > k:
            return Ø

        v = pick_boundary_vertex(G, Rmax, X, Y, D)
        if v is None:
            # Should not happen when connected, but safe fallback
            return FS([Ø])

        out = set()

        # Branch 1: take v into separator
        for S in rec(X, Y, k - 1, FS(set(D) | {v})):
            out.add(FS(set(S) | {v}))

        # Branch 2: force v to the X-side (so v cannot be in the separator)
        for S in rec(FS(set(X) | {v}), Y, k, D):
            out.add(S)

        return FS(out)

    return FS(rec(X, Y, k, D))


def important_separators(G, s, t, k):
    if s == t:
        return {Ø}
    if s not in G or t not in G:
        raise ValueError("s and t must be vertices of G")
    if k < 0:
        return set()

    if G.is_directed():
        raise ValueError("G must be undirected")

    X0 = FS([s])
    Y0 = FS([t])
    D0 = Ø

    return rec_important(G, X0, Y0, k, D0)
