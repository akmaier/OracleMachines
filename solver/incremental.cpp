// Persistent untrusted SAT proposal engine. Final decisions are checked by Lean.
// Protocol: ADD <literals ending in 0>; SOLVE <root> <model vars ending in 0>.
#include "cadical.hpp"
#include <chrono>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <sys/resource.h>

struct Learned : CaDiCaL::Learner {
  unsigned long long clauses = 0;
  unsigned long long omitted = 0;
  std::vector<std::vector<int>> exported;
  std::vector<int> current;
  bool learning(int size) override {
    ++clauses;
    if (size < 1 || size > 64 || exported.size() >= 4096) { ++omitted; return false; }
    current.clear();
    return true;
  }
  void learn(int literal) override {
    if (literal) current.push_back(literal);
    else exported.push_back(current);
  }
};

int main() {
  CaDiCaL::Solver solver;
  solver.set("quiet", 1);
  Learned learned;
  solver.connect_learner(&learned);
  unsigned long long queries = 0;
  int maximum = 0;
  std::string line;
  while (std::getline(std::cin, line)) {
    std::istringstream input(line);
    std::string command;
    input >> command;
    if (command == "ADD") {
      int literal;
      bool ended = false;
      while (input >> literal) {
        if (literal == 0) { solver.add(0); ended = true; }
        else {
          if (literal == INT32_MIN) return 2;
          int variable = std::abs(literal);
          if (variable > maximum) {
            solver.reserve(variable);
            // CaDiCaL restores eliminated clauses on incremental reuse; leaving
            // variables unfrozen permits its normal inprocessing techniques.
            maximum = variable;
          }
          solver.add(literal);
          ended = false;
        }
      }
      if (!ended) return 2;
    } else if (command == "SOLVE") {
      learned.exported.clear();
      int root;
      if (!(input >> root) || !root || root == INT32_MIN || std::abs(root) > maximum) return 2;
      std::vector<int> model;
      int variable;
      while (input >> variable && variable) {
        if (variable < 1 || variable > maximum) return 2;
        model.push_back(variable);
      }
      solver.assume(root);
      const auto retained_before = solver.redundant();
      const auto start = std::chrono::steady_clock::now();
      const int answer = solver.solve();
      const auto nanos = std::chrono::duration_cast<std::chrono::nanoseconds>(
          std::chrono::steady_clock::now() - start).count();
      struct rusage usage;
      getrusage(RUSAGE_SELF, &usage);
      std::cout << "{\"verdict\":" << answer << ",\"queries\":" << ++queries
                << ",\"learned_clauses_total\":" << learned.clauses
                << ",\"retained_clauses\":" << solver.redundant()
                << ",\"retained_before\":" << retained_before
                << ",\"solve_ns\":" << nanos << ",\"peak_rss_bytes\":"
#ifdef __APPLE__
                << usage.ru_maxrss
#else
                << usage.ru_maxrss * 1024
#endif
                << ",\"values\":[";
      if (answer == 10) {
        for (size_t i = 0; i < model.size(); ++i) {
          if (i) std::cout << ',';
          std::cout << solver.val(model[i]);
        }
      }
      std::cout << "],\"export_omitted_total\":" << learned.omitted << ",\"learned_export\":[";
      for (size_t i = 0; i < learned.exported.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << '[';
        for (size_t j = 0; j < learned.exported[i].size(); ++j) {
          if (j) std::cout << ',';
          std::cout << learned.exported[i][j];
        }
        std::cout << ']';
      }
      std::cout << "]}" << std::endl;
    } else return 2;
  }
  solver.disconnect_learner();
}
