#include <algorithm>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <numeric>
#include <random>
#include <vector>

const double DENSITY = 0.4;

int main(int argc, char *argv[]) {
  int maxTaskCount = 10;
  int maxGroupCount = 3;
  int maxTime = 10;
  uint64_t seed = std::chrono::high_resolution_clock::now().time_since_epoch().count();
  if (argc > 1) {
    maxTaskCount = std::stoi(argv[1]);
    if (argc >= 3)
      maxGroupCount = std::stoi(argv[2]);
    if (argc >= 4)
      maxTime = std::stoi(argv[3]);
    if (argc >= 5)
      seed = std::stoi(argv[4]);
  }
  std::mt19937 gen(seed);
  std::uniform_real_distribution<> prob_dist(0.0, 1.0);
  std::uniform_int_distribution<> taskDist(maxTaskCount / 2, maxTaskCount);
  std::uniform_int_distribution<> groupDist(maxGroupCount / 2, maxGroupCount);
  std::uniform_int_distribution<> timeDist(maxTime / 2, maxTime);

  int taskCount = taskDist(gen);
  int groupCount = groupDist(gen);

  std::cout << taskCount << " " << groupCount << "\n";
  for (int i = 0; i < taskCount; i++) {
    std::cout << timeDist(gen) << "\n";
  }
  std::vector<int> p(taskCount);
  std::iota(p.begin(), p.end(), 0);
  std::shuffle(p.begin(), p.end(), gen);

  std::vector<std::vector<int>> matrix(taskCount,
                                       std::vector<int>(taskCount, 0));

  for (int i = 0; i < taskCount; ++i) {
    for (int j = i + 1; j < taskCount; ++j) {
      if (prob_dist(gen) < DENSITY) {
        int u = p[i];
        int v = p[j];
        matrix[u][v] = 1;
        matrix[v][u] = -1;
      }
    }
  }

  for (int i = 0; i < taskCount; ++i) {
    for (int j = 0; j < taskCount; ++j) {
      std::cout << matrix[i][j] << " ";
    }
    std::cout << "\n";
  }

  return 0;
}
