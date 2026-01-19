#pragma once
#include <bits/stdc++.h>

using Set = std::vector<int>;

struct UGraph {
  int n;
  std::vector<std::vector<int>> adj;
  explicit UGraph(int n = 0);
  void addEdge(int u, int v);
};

std::vector<Set> important_separators(const UGraph &G, int s, int t, int k);
Set s_component(const UGraph &G, int s, const Set &S);
