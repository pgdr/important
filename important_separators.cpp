#include <bits/stdc++.h>
#include <string>

#include "libimportant.hpp"

using namespace std;

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
  (void)G; // not needed for printing

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

  for (int r = 0; r < R; r++)
    cout << out[r] << "\n";
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
