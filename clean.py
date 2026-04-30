import networkx as nx

from collections import deque


## TESTING
def random_graph(n, m):
    import random

    T = nx.random_labeled_tree(n)
    G = nx.Graph(T)

    possible = [
        (u, v)
        for u in range(n)
        for v in range(u + 1, n)
        if not G.has_edge(u, v)
    ]

    extra_edges = m - n + 1
    random.shuffle(possible)
    G.add_edges_from(possible[:extra_edges])
    return G


### END TESTING


def vertex_capacity_network(G, s, t):
    """Construct the vertex-flow network from a given graph (G, s, t).
    A minimum s-t-vertex separator in G will correspond to a minimum
    s-t-edgecut in H, with the same value.

    """
    H = nx.DiGraph()
    infinity = G.number_of_nodes() + 1

    for v in G:
        H.add_node((v, "in"))
        H.add_node((v, "out"))

        cap = infinity if v == s or v == t else 1
        H.add_edge((v, "in"), (v, "out"), capacity=cap)

    for v, u in G.edges():
        H.add_edge((v, "out"), (u, "in"), capacity=infinity)
        H.add_edge((u, "out"), (v, "in"), capacity=infinity)

    return H


def bfs(H, source, G, s, t):
    """
    Input: residual vertex-capacity network H, source node, and original graph G.

    Return the separator closest to s, and the reachability set of s.
    A vertex v is in the separator iff (v, "in") is reachable but
    (v, "out") is not reachable.
    """

    queue = deque([source])
    seen = {source}

    while queue:
        v = queue.popleft()

        for u in H[v]:
            edge = H[v][u]

            if u not in seen and edge["flow"] < edge["capacity"]:
                seen.add(u)
                queue.append(u)

    S = set()
    R = set()

    for v in G:
        if (v, "out") in seen:
            R.add(v)

        elif v != s and v != t and (v, "in") in seen:
            S.add(v)

    return S, R


def minimum_closest_separator(G, s, t):
    """Compute a minimum separator closest possible to s.  Return the
    separator and the reachability set of s."""
    H = vertex_capacity_network(G, s, t)
    source = (s, "out")
    target = (t, "in")

    H = nx.algorithms.flow.edmonds_karp(
        H, source, target, capacity="capacity"
    )

    S, R = bfs(H, source, G, s, t)
    return S, R


def G_minus_vertices(G, vertices):
    H = G.copy()
    H.remove_nodes_from(vertices)
    return H


def contract_vertices_into(G, vertices, s):
    H = G.copy()
    vertices = set(vertices)

    outside_neighbors = set()
    for v in vertices:
        for u in G[v]:
            if u not in vertices:
                outside_neighbors.add(u)

    H.remove_nodes_from(vertices - {s})

    for u in outside_neighbors:
        H.add_edge(s, u)

    H.remove_edges_from(nx.selfloop_edges(H))
    return H


def contract_edge(G, s, v):
    H = G.copy()

    for u in list(G[v]):
        if u != s:
            H.add_edge(s, u)

    H.remove_node(v)
    H.remove_edges_from(nx.selfloop_edges(H))
    return H


def impsep(G, s, t, Z, k):
    """Enumerate all important s-t-separators in G."""
    if s == t or G.has_edge(s, t):
        return

    if not nx.has_path(G, s, t):
        yield Z
        return

    S, R = minimum_closest_separator(G, s, t)

    if len(S) > k:
        return

    elif k == 0 or not S:
        yield Z

    else:
        G = contract_vertices_into(G, R, s)
        v = S.pop()

        # choose v
        Gv = G_minus_vertices(G, {v})
        yield from impsep(Gv, s, t, Z | {v}, k - 1)

        # contract edge sv
        Gsv = contract_edge(G, s, v)
        yield from impsep(Gsv, s, t, Z, k)


def important_separator(G, s, t, k):
    yield from impsep(G, s, t, set(), k)


if __name__ == "__main__":
    G = random_graph(10, 20)
    V = list(G.nodes())
    s = V[0]
    t = V[-1]
    print(G, s, t)
    for S in important_separator(G, s, t, 4):
        print(S)
