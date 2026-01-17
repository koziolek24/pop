#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Building project in release mode...${NC}"
cargo build --release --quiet

mkdir -p out

seed=$1

for input_file in $(ls in/in*.txt | sort -V); do
    filename=$(basename -- "$input_file")
    number="${filename//[^0-9]/}"
    
    output_file="out/out${number}.txt"      # Expected score
    rust_time_file="out/timeR${number}.txt" # Where we save Rust time
    py_time_file="out/time${number}.txt"    # Python time file
    
    if [ "$#" -ge 1 ]; then
        full_output=$(./target/release/pop "$1" < "$input_file" 2> /dev/null)
    else
        full_output=$(./target/release/pop < "$input_file" 2> /dev/null)
    fi

    actual_score=$(echo "$full_output" | sed -n '1p')
    rust_time_raw=$(echo "$full_output" | sed -n '2p')

    echo "$rust_time_raw" > "$rust_time_file"

    if [ -f "$output_file" ]; then
        expected_score=$(< "$output_file")
    else
        expected_score="0" # Default if no out file exists
    fi

    if [[ -z "$actual_score" ]]; then
        diff_msg="${RED}FAIL (No output)${NC}"
    else
        diff=$((actual_score - expected_score))
        
        if [ "$diff" -eq 0 ]; then
            diff_msg="${GREEN}OK${NC}"
        else
            # Add '+' sign if positive
            if [ "$diff" -gt 0 ]; then sign="+"; else sign=""; fi
            
            diff_msg="${RED}ERR${NC} (Exp: ${expected_score}, Got: ${actual_score}, Diff: ${RED}${sign}${diff}${NC})"
        fi
    fi

    if [ -f "$py_time_file" ]; then
        py_time=$(< "$py_time_file")
        
        speedup=$(awk -v py="$py_time" -v ru="$rust_time_raw" 'BEGIN { if (ru > 0) printf "%.2f", py/ru; else print "0" }')
        
        is_faster=$(awk -v s="$speedup" 'BEGIN { print (s >= 1.0) }')
        if [ "$is_faster" -eq 1 ]; then
            color_speed="${GREEN}"
        else
            color_speed="${RED}"
        fi

        time_msg="[Time: Rust ${rust_time_raw}s vs Py ${py_time}s | Speedup: ${color_speed}${speedup}x${NC}]"
    else
        time_msg="[Time: Rust ${rust_time_raw}s ${YELLOW}(No Py file)${NC}]"
    fi

    echo -e "$input_file $diff_msg $time_msg"
done
