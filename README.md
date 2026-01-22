# Project Guide

## 1. Setup

Install dependencies using `uv`:

```bash
uv sync
```

## 2. Generate Tests

Compile generator and create test batches in `in/`:

```bash
g++ -O3 gen.cc -o gen
./generate.sh
```

## 3. Reference Solver (Python)

Run Python solver to generate expected scores in `out/`:

```bash
uv run bash run_solver.sh
```

## 4. Run Rust Solution

Build and run the solution against generated tests:

```bash
./test.sh [SEED]
```

## 5. Analyze Results

Compare Rust solution against reference:

```bash
./test.sh | ./analyze.py
```

**Metrics:**
- **Acc %**: Percentage of tests matching/beating reference score.
- **Tol %**: Percentage within error tolerance.
- **Bonus**: Solutions found where reference failed.
- **Speedup**: Average performance gain vs Python.