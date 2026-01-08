#!/usr/bin/env python3
import sys
import re

# --- Konfiguracja Batchy ---
# (Start, Koniec włącznie, Opis)
BATCHES = [
    (0, 29, "1. Małe taski (20), Małe grupy (5)"),
    (30, 59, "2. Średnie taski (50), Małe grupy (3)"),
    (60, 89, "3. Małe taski (20), Średnie grupy (10)"),
    (90, 119, "4. Średnie taski (50), Średnie grupy (10)"),
    (120, 149, "5. Duże (100 tasków, 20 grup)"),
    (150, 200, "6. Ogromne (1000 tasków, 200 grup)")
]

TOLERANCE_THRESHOLD = 2  # 0.1%

# --- Kolory ANSI ---
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def parse_line(line):
    # Wyciągnij numer testu
    match_num = re.search(r'in/in(\d+)\.txt', line)
    if not match_num:
        return None
    num = int(match_num.group(1))

    is_ok = "OK" in line
    is_bonus = False

    # Sprawdź czy Expected to BRAK_ROZWIAZANIA
    if "Exp: BRAK_ROZWIAZANIA" in line:
        is_bonus = True
        # Jeśli Rust znalazł rozwiązanie, to jest bonus/świetny wynik
    
    # Wyciągnij błędy (Expected vs Got) dla % błędu
    match_exp = re.search(r'Exp: (\d+)', line)
    match_got = re.search(r'Got: (\d+)', line)

    expected = int(match_exp.group(1)) if match_exp else 0
    got = int(match_got.group(1)) if match_got else 0

    # Oblicz % błędu
    error_pct = 0.0
    if not is_ok and expected > 0 and not is_bonus:
        error_pct = (abs(got - expected) / expected) * 100

    # Wyciągnij czasy
    match_rust = re.search(r'Rust ([\d\.]+)s', line)
    match_py = re.search(r'Py ([\d\.]+)s', line)

    rust_time = float(match_rust.group(1)) if match_rust else 0.0
    py_time = float(match_py.group(1)) if match_py else 0.0

    # Speedup
    speedup = 0.0
    if rust_time > 0 and py_time > 0:
        speedup = py_time / rust_time

    return {
        'id': num,
        'ok': is_ok,
        'bonus': is_bonus,
        'error_pct': error_pct,
        'rust_time': rust_time,
        'py_time': py_time,
        'speedup': speedup
    }


def print_separator():
    print("-" * 125)


def main():
    # Czytamy dane ze standardowego wejścia (pipe)
    raw_input = sys.stdin.read()

    results = {}
    lines = raw_input.strip().split('\n')

    # Najpierw wypisz surowe logi (żebyś widział postęp/błędy)
    print("\n" + "="*50 + " ANALIZA WYNIKÓW " + "="*50 + "\n")

    # Parsowanie
    for line in lines:
        parsed = parse_line(line)
        if parsed:
            results[parsed['id']] = parsed

    # --- Tabela Batchy ---
    # Dodajemy kolumnę Tol %
    header = f"{'Batch':<40} | {'Count':<5} | {'Acc %':<6} | {'Tol %':<6} | {'Bonus':<5} | {'Speedup':<9} | {'Avg Err %':<10} | {'Max Err %':<10}"
    print(BOLD + header + RESET)
    print_separator()

    total_files = 0
    total_ok = 0
    total_tol_ok = 0
    total_bonus = 0
    total_err_pct_sum = 0
    global_rust_time = 0.0
    global_py_time = 0.0
    global_speedups = []
    max_err_global = 0.0

    for start, end, name in BATCHES:
        batch_files = 0
        batch_ok = 0
        batch_tol_ok = 0
        batch_bonus = 0
        batch_speedups = []
        batch_err_pct_sum = 0
        batch_max_err = 0.0

        # Iterujemy po zakresie ID dla danego batcha
        for i in range(start, end + 1):
            if i in results:
                r = results[i]
                batch_files += 1
                
                if r['ok']:
                    batch_ok += 1
                elif r['bonus']:
                    batch_ok += 1  # Liczymy bonus jako sukces do accuracy
                    batch_bonus += 1
                
                # Sprawdź tolerancję (Ok i Bonus mają error_pct = 0.0, więc łapią się z automatu)
                if r['error_pct'] <= TOLERANCE_THRESHOLD:
                    batch_tol_ok += 1

                batch_err_pct_sum += r['error_pct']
                if r['error_pct'] > batch_max_err:
                    batch_max_err = r['error_pct']

                if r['speedup'] > 0:
                    batch_speedups.append(r['speedup'])

                global_rust_time += r['rust_time']
                global_py_time += r['py_time']

        # Statystyki batcha
        if batch_files > 0:
            accuracy = (batch_ok / batch_files * 100)
            tol_accuracy = (batch_tol_ok / batch_files * 100)
            avg_speedup = sum(batch_speedups) / \
                len(batch_speedups) if batch_speedups else 0
            avg_err_pct = batch_err_pct_sum / batch_files

            # Kolorowanie Accuracy
            acc_color = GREEN if accuracy == 100 else (
                YELLOW if accuracy > 80 else RED)
            
            tol_color = GREEN if tol_accuracy == 100 else (
                YELLOW if tol_accuracy > 80 else RED)

            print(f"{name:<40} | {batch_files:<5} | {acc_color}{accuracy:6.1f}{RESET} | {tol_color}{tol_accuracy:6.1f}{RESET} | {batch_bonus:<5} | {avg_speedup:8.2f}x | {avg_err_pct:9.2f}% | {batch_max_err:9.2f}%")

            # Aktualizacja globalnych
            total_files += batch_files
            total_ok += batch_ok
            total_tol_ok += batch_tol_ok
            total_bonus += batch_bonus
            total_err_pct_sum += batch_err_pct_sum
            global_speedups.extend(batch_speedups)
            if batch_max_err > max_err_global:
                max_err_global = batch_max_err

    print_separator()

    # --- Podsumowanie Całości ---
    if total_files > 0:
        global_acc = (total_ok / total_files * 100)
        global_tol_acc = (total_tol_ok / total_files * 100)
        global_avg_spd = sum(global_speedups) / \
            len(global_speedups) if global_speedups else 0
        global_avg_err = total_err_pct_sum / total_files

        acc_color = GREEN if global_acc == 100 else (
            YELLOW if global_acc > 80 else RED)
        
        tol_color = GREEN if global_tol_acc == 100 else (
            YELLOW if global_tol_acc > 80 else RED)

        print(f"{BOLD}{'TOTAL / AVERAGE':<40} | {total_files:<5} | {acc_color}{global_acc:6.1f}{RESET} | {tol_color}{global_tol_acc:6.1f}{RESET} | {total_bonus:<5} | {global_avg_spd:8.2f}x | {global_avg_err:9.2f}% | {max_err_global:9.2f}%{RESET}")

        print("\n" + "="*40 + " PORÓWNANIE CZASÓW " + "="*39)
        print(f"Całkowity czas Rust:    {BOLD}{global_rust_time:.4f}s{RESET}")
        print(f"Całkowity czas Python:  {global_py_time:.4f}s")
        
        if total_bonus > 0:
             print(f"Znaleziono {BOLD}{total_bonus}{RESET} rozwiązań, których Python/Solver nie znalazł!")

        if global_rust_time > 0:
            total_speedup = global_py_time / global_rust_time
            print(f"Globalny Speedup (Sum): {BOLD}{GREEN}{total_speedup:.2f}x{RESET}")

        avg_rust = global_rust_time / total_files
        avg_py = global_py_time / total_files
        print(f"\nŚredni czas/plik Rust:  {avg_rust:.4f}s")
        print(f"Średni czas/plik Py:    {avg_py:.4f}s")


if __name__ == "__main__":
    main()
