#!/bin/bash

mkdir -p out

if [ ! -f "solver.py" ]; then
    echo "Brak pliku solver.py"
    exit 1
fi


for input_file in $(ls in/in*.txt | sort -V); do
    filename=$(basename -- "$input_file")
    number="${filename//[^0-9]/}"
    file_out="out/out${number}.txt"
    file_time="out/time${number}.txt"
    file_solve="out/solve${number}.txt"
    temp_output="out/temp${number}.tmp"
    python3 solver.py < "$input_file" > "$temp_output"
    sed -n '1p' "$temp_output" > "$file_time"
    exec_time=$(cat "$file_time")
    sed -n '2p' "$temp_output" > "$file_out"
    tail -n +3 "$temp_output" > "$file_solve"
    rm "$temp_output"
done

