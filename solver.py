import sys
import time
from ortools.sat.python import cp_model

def solve_schedule():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    try:
        n = int(next(iterator))
        m = int(next(iterator))
        durations = [int(next(iterator)) for _ in range(n)]
        adjacency = [[int(next(iterator)) for _ in range(n)] for _ in range(n)]
    except StopIteration:
        return

    model = cp_model.CpModel()
    horizon = sum(durations)
    starts = []
    ends = []
    intervals = []

    for i in range(n):
        s = model.NewIntVar(0, horizon, f'start_{i}')
        e = model.NewIntVar(0, horizon, f'end_{i}')
        interval = model.NewIntervalVar(s, durations[i], e, f'interval_{i}')
        starts.append(s)
        ends.append(e)
        intervals.append(interval)

    for r in range(n):
        for c in range(n):
            val = adjacency[r][c]
            if val == 1:
                model.Add(ends[r] <= starts[c])
            elif val == -1:
                model.Add(ends[c] <= starts[r])

    demands = [1] * n
    model.AddCumulative(intervals, demands, m)

    makespan = model.NewIntVar(0, horizon, 'makespan')
    model.AddMaxEquality(makespan, ends)
    model.Minimize(makespan)

    solver = cp_model.CpSolver()
    
    start_time = time.perf_counter()
    status = solver.Solve(model)
    end_time = time.perf_counter()
    
    calculation_time = end_time - start_time

    print(f"{calculation_time:.6f}")

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(int(solver.ObjectiveValue()))
        
        tasks_ordered = sorted(range(n), key=lambda k: solver.Value(starts[k]))
        for i in tasks_ordered:
            st = solver.Value(starts[i])
            en = solver.Value(ends[i])
            print(f"Zadanie {i+1} (czas: {durations[i]}): [{st}, {en}]")
    else:
        print("BRAK_ROZWIAZANIA")

if __name__ == '__main__':
    solve_schedule()
