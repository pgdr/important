#include <bits/stdc++.h>
#include <string>
using namespace std;

struct Edge {
  int v;    // to
  int flow; // current flow
  int C;    // capacity
  int rev;  // index of reverse edge in adj[v]
};

class Graph {
  int V;
  vector<int> level;
  vector<vector<Edge>> adj;

public:
  Graph(int V) : V(V), level(V, -1), adj(V) {}

  void addEdge(int u, int v, int C) {
    Edge a{v, 0, C, (int)adj[v].size()};
    Edge b{u, 0, 0, (int)adj[u].size()};
    adj[u].push_back(a);
    adj[v].push_back(b);
  }

  int numVertices() const { return V; }
  const vector<Edge> &neighborEdges(int u) const { return adj[u]; }

  bool BFS(int s, int t) {
    fill(level.begin(), level.end(), -1);
    level[s] = 0;
    deque<int> q;
    q.push_back(s);

    while (!q.empty()) {
      int u = q.front();
      q.pop_front();
      for (auto &e : adj[u]) {
        if (level[e.v] < 0 && e.flow < e.C) {
          level[e.v] = level[u] + 1;
          q.push_back(e.v);
        }
      }
    }
    return level[t] >= 0;
  }

  int sendFlow(int u, int flow, int t, vector<int> &start) {
    if (u == t)
      return flow;
    for (; start[u] < (int)adj[u].size(); start[u]++) {
      Edge &e = adj[u][start[u]];
      if (level[e.v] == level[u] + 1 && e.flow < e.C) {
        int curr_flow = min(flow, e.C - e.flow);
        int pushed = sendFlow(e.v, curr_flow, t, start);
        if (pushed > 0) {
          e.flow += pushed;
          adj[e.v][e.rev].flow -= pushed;
          return pushed;
        }
      }
    }
    return 0;
  }

  int DinicMaxflow(int s, int t) {
    if (s == t)
      return -1;
    int total = 0;
    while (BFS(s, t)) {
      vector<int> start(V, 0);
      while (int f = sendFlow(s, INT_MAX, t, start))
        total += f;
    }
    return total;
  }
};

struct UGraph {
  int n;
  vector<vector<int>> adj;
  UGraph(int n = 0) : n(n), adj(n) {}
  void addEdge(int u, int v) {
    adj[u].push_back(v);
    adj[v].push_back(u);
  }
};

using Set = vector<int>;

static inline void normalize(Set &s) {
  sort(s.begin(), s.end());
  s.erase(unique(s.begin(), s.end()), s.end());
}

static inline Set with_elem(Set s, int x) {
  auto it = lower_bound(s.begin(), s.end(), x);
  if (it == s.end() || *it != x)
    s.insert(it, x);
  return s;
}

static inline bool contains(const Set &s, int x) {
  return binary_search(s.begin(), s.end(), x);
}

static bool exists_path_avoiding(const UGraph &G, const Set &X, const Set &Y,
                                 const Set &D) {
  vector<char> forbidden(G.n, false), target(G.n, false), seen(G.n, false);

  for (int d : D)
    forbidden[d] = true;
  for (int y : Y)
    target[y] = true;
  for (int d : D)
    seen[d] = true;

  deque<int> q;
  for (int x : X) {
    if (forbidden[x])
      continue;
    if (!seen[x]) {
      seen[x] = true;
      q.push_back(x);
    }
  }

  while (!q.empty()) {
    int u = q.front();
    q.pop_front();
    if (target[u])
      return true;
    for (int w : G.adj[u]) {
      if (!seen[w] && !forbidden[w]) {
        seen[w] = true;
        q.push_back(w);
      }
    }
  }
  return false;
}

static pair<int, Set> furthest_min_vertex_cut(const UGraph &G, const Set &X,
                                              const Set &Y, const Set &D,
                                              int k) {
  vector<char> inX(G.n, false), inY(G.n, false), inD(G.n, false);
  for (int x : X)
    inX[x] = true;
  for (int y : Y)
    inY[y] = true;
  for (int d : D)
    inD[d] = true;

  int INF = max(k + 1, G.n + k + 5);

  auto inId = [&](int v) { return 2 * v; };
  auto outId = [&](int v) { return 2 * v + 1; };
  int SRC = 2 * G.n;
  int SNK = 2 * G.n + 1;

  Graph H(2 * G.n + 2);

  // vertex capacities
  for (int v = 0; v < G.n; v++) {
    if (inD[v])
      continue;
    int cap = (inX[v] || inY[v]) ? INF : 1;
    H.addEdge(inId(v), outId(v), cap);
  }

  // undirected edge gadget: add both arcs once per unordered pair
  for (int a = 0; a < G.n; a++) {
    if (inD[a])
      continue;
    for (int b : G.adj[a]) {
      if (a < b) {
        if (inD[b])
          continue;
        H.addEdge(outId(a), inId(b), INF);
        H.addEdge(outId(b), inId(a), INF);
      }
    }
  }

  // super source/sink wiring
  for (int x : X)
    if (!inD[x])
      H.addEdge(SRC, outId(x), INF);
  for (int y : Y)
    if (!inD[y])
      H.addEdge(inId(y), SNK, INF);

  int lam = H.DinicMaxflow(SRC, SNK);

  // residual reachability from SRC
  vector<char> reach(H.numVertices(), false);
  vector<int> st{SRC};
  while (!st.empty()) {
    int u = st.back();
    st.pop_back();
    if (reach[u])
      continue;
    reach[u] = true;
    for (const auto &e : H.neighborEdges(u)) {
      if (e.flow < e.C && !reach[e.v])
        st.push_back(e.v);
    }
  }

  Set Rmax;
  for (int v = 0; v < G.n; v++) {
    if (!inD[v] && reach[outId(v)])
      Rmax.push_back(v);
  }
  normalize(Rmax);
  return {lam, Rmax};
}

static int pick_boundary_vertex(const UGraph &G, const Set &Rmax, const Set &X,
                                const Set &Y, const Set &D) {
  vector<char> inR(G.n, false), inX(G.n, false), inY(G.n, false),
      inD(G.n, false);
  for (int u : Rmax)
    inR[u] = true;
  for (int u : X)
    inX[u] = true;
  for (int u : Y)
    inY[u] = true;
  for (int u : D)
    inD[u] = true;

  for (int u : Rmax) {
    for (int v : G.adj[u]) {
      if (!inR[v] && !inX[v] && !inY[v] && !inD[v])
        return v;
    }
  }
  return -1;
}

// ---------------- Important separators (Marx, 4^k) ----------------
struct Key {
  int k;
  Set X, Y, D;
  bool operator==(const Key &o) const {
    return k == o.k && X == o.X && Y == o.Y && D == o.D;
  }
};

struct VecHash {
  size_t operator()(const Set &v) const noexcept {
    size_t h = 0;
    for (int x : v) {
      h ^= std::hash<int>{}(x) + 0x9e3779b97f4a7c15ULL + (h << 6) + (h >> 2);
    }
    return h;
  }
};

struct KeyHash {
  size_t operator()(const Key &K) const noexcept {
    size_t h = std::hash<int>{}(K.k);
    VecHash vh;
    auto comb = [&](size_t x) {
      h ^= x + 0x9e3779b97f4a7c15ULL + (h << 6) + (h >> 2);
    };
    comb(vh(K.X));
    comb(vh(K.Y));
    comb(vh(K.D));
    return h;
  }
};

static vector<Set> important_separators(const UGraph &G, int s, int t, int k) {
  if (s == t)
    return {Set{}};
  if (s < 0 || s >= G.n || t < 0 || t >= G.n)
    throw runtime_error("s,t out of range");
  if (k < 0)
    return {};

  unordered_map<Key, vector<Set>, KeyHash> memo;

  function<vector<Set>(const Set &, const Set &, int, const Set &)> rec =
      [&](const Set &X, const Set &Y, int kk, const Set &D) -> vector<Set> {
    Key key{kk, X, Y, D};
    if (auto it = memo.find(key); it != memo.end())
      return it->second;

    vector<Set> ans;

    if (kk < 0) {
      memo[key] = {};
      return {};
    }

    if (!exists_path_avoiding(G, X, Y, D)) {
      memo[key] = {Set{}};
      return {Set{}};
    }

    auto [lam, Rmax] = furthest_min_vertex_cut(G, X, Y, D, kk);
    if (lam > kk) {
      memo[key] = {};
      return {};
    }

    int v = pick_boundary_vertex(G, Rmax, X, Y, D);
    if (v == -1) {
      memo[key] = {Set{}};
      return {Set{}};
    }

    set<Set> out;

    // Branch 1: put v into separator (delete v)
    {
      Set D2 = with_elem(D, v);
      auto fam = rec(X, Y, kk - 1, D2);
      for (auto S : fam) {
        S = with_elem(S, v);
        out.insert(std::move(S));
      }
    }

    // Branch 2: force v to X-side
    {
      Set X2 = with_elem(X, v);
      auto fam = rec(X2, Y, kk, D);
      for (auto &S : fam)
        out.insert(S);
    }

    ans.assign(out.begin(), out.end());
    memo[key] = ans;
    return ans;
  };

  Set X0{s}, Y0{t}, D0;
  return rec(X0, Y0, k, D0);
}

Set s_component(const UGraph &G, int s, const Set &S) {
  if (contains(S, s))
    return {};

  vector<char> blocked(G.n, false), seen(G.n, false);
  for (int v : S)
    blocked[v] = true;

  deque<int> q;
  seen[s] = true;
  q.push_back(s);

  while (!q.empty()) {
    int u = q.front();
    q.pop_front();

    for (int v : G.adj[u]) {
      if (blocked[v] || seen[v])
        continue;
      seen[v] = true;
      q.push_back(v);
    }
  }

  Set comp;
  comp.reserve(G.n);
  for (int v = 0; v < G.n; v++) {
    if (seen[v])
      comp.push_back(v);
  }
  return comp; // is sorted
}

void print_set(const Set &A) {
  cout << "{";
  for (int i = 0; i < (int)A.size(); i++) {
    if (i)
      cout << ", ";
    cout << A[i];
  }
  cout << "}";
}

void print_set_grid(const Set &A, int WIDTH) {
  cout << "{";
  for (int i = 0; i < (int)A.size(); i++) {
    if (i)
      cout << ", ";
    int v = A[i];
    int x = v % WIDTH;
    int y = v / WIDTH;
    cout << "(" << x << "," << y << ")";
  }
  cout << "}";
}

void print_grid_with_separator(const UGraph &G, int R, int C,
                               const vector<char> &blocked, int s,
                               const Set &S) {
  (void)
      G; // not needed for printing, but kept to match your requested signature

  cout << R << " " << C << "\n";

  vector<string> out(R, string(C, '.'));

  // blocked cells
  for (int r = 0; r < R; r++) {
    for (int c = 0; c < C; c++) {
      int v = r * C + c;
      if (blocked[v])
        out[r][c] = '#';
    }
  }

  // separator cells
  for (int v : S) {
    if (0 <= v && v < R * C && !blocked[v]) {
      out[v / C][v % C] = 'X';
    }
  }

  // source (wins over X)
  if (0 <= s && s < R * C && !blocked[s]) {
    out[s / C][s % C] = 's';
  }

  for (int r = 0; r < R; r++) {
    cout << out[r] << "\n";
  }
}

int main(int argc, char **argv) {
  ios::sync_with_stdio(false);
  cin.tie(nullptr);

  int R, C;
  cin >> R >> C;

  vector<string> grid(R);
  for (int i = 0; i < R; i++)
    cin >> grid[i];

  auto id = [&](int r, int c) { return r * C + c; };

  int s = -1;
  vector<char> blocked(R * C, 0);

  for (int r = 0; r < R; r++) {
    for (int c = 0; c < C; c++) {
      char ch = grid[r][c];
      if (ch == '#')
        blocked[id(r, c)] = 1;
      if (ch == 's')
        s = id(r, c);
    }
  }

  if (s == -1) {
    cerr << "Error: grid contains no 's'\n";
    return 1;
  }

  int t = R * C;       // extra terminal node (boundary sink)
  UGraph G(R * C + 1); // all cells + t

  for (int r = 0; r < R; r++) {
    for (int c = 0; c < C; c++) {
      int u = id(r, c);
      if (blocked[u])
        continue;

      if (c + 1 < C) {
        int v = id(r, c + 1);
        if (!blocked[v])
          G.addEdge(u, v);
      }
      if (r + 1 < R) {
        int v = id(r + 1, c);
        if (!blocked[v])
          G.addEdge(u, v);
      }
    }
  }

  set<int> boundary;
  for (int r = 0; r < R; r++) {
    boundary.insert(id(r, 0));
    boundary.insert(id(r, C - 1));
  }
  for (int c = 0; c < C; c++) {
    boundary.insert(id(0, c));
    boundary.insert(id(R - 1, c));
  }
  for (int v : boundary) {
    if (!blocked[v])
      G.addEdge(t, v);
  }

  int k = 3;
  if (argc >= 2)
    k = stoi(argv[1]);
  cout << "k = " << k << "\n";

  auto seps = important_separators(G, s, t, k);

  if (seps.empty()) {
    cout << "No important separators of size <= " << k << "\n";
    return 0;
  }

  Set bestS;
  size_t bestCompSize = 0;

  for (const auto &S : seps) {
    Set comp = s_component(G, s, S);
    if (comp.size() > bestCompSize) {
      bestCompSize = comp.size();
      bestS = S;
    }
  }

  cout << "important separators: " << seps.size() << "\n";
  cout << "optimal size: " << bestCompSize << "\n";
  cout << "Best separator S = ";
  print_set_grid(bestS, C);
  cout << "\n";
  print_grid_with_separator(G, R, C, blocked, s, bestS);
  return 0;
}
