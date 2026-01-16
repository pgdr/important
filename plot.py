import matplotlib.pyplot as plt
import networkx as nx

# TODO these should be provided by enclose
WIDTH = HEIGHT = 12
T_NODE = (-2, HEIGHT // 2)


def plot(G, s, t, S, R):
    G = G.copy()
    G.remove_node(T_NODE)

    pos = {n: n for n in G.nodes()}  # use (x,y) coordinates as layout
    degree_0 = [v for v in G.nodes() if not G.degree(v)]

    THE_WIDTH = 0
    SIZE = 500

    plt.figure(figsize=(6, 6))
    nx.draw(
        G,
        pos,
        node_size=SIZE,
        width=THE_WIDTH,
        with_labels=False,
        node_color="#1b6b3a",
        node_shape="s",  # square
    )

    nx.draw(
        G,
        pos,
        node_size=SIZE,
        nodelist=degree_0,
        width=THE_WIDTH,
        with_labels=False,
        node_color="#062f48",
        node_shape="s",  # square
    )

    nx.draw(
        G,
        pos,
        node_size=SIZE,
        nodelist=list(R),
        width=THE_WIDTH,
        with_labels=False,
        node_color="#bd974a",
        node_shape="s",  # square
    )

    # color nodes in S black
    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=list(S),
        node_color="#bcbcbc",
        node_size=SIZE,
        node_shape="s",
    )

    # draw the rest of the horse
    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=[s],
        node_color="#f0e070",
        node_size=SIZE,
        node_shape="s",
    )

    plt.axis("equal")
    plt.show()
