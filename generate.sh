#!/bin/bash

mkdir -p in

counter=1

generate_batch() {
    count=$1
    tasks=$2
    groups=$3
    time=$4
    seed=$5
    
    for ((i=1; i<=count; i++)); do
        ./gen $tasks $groups $time $seed > "in/in${counter}.txt"
        ((counter++))
        ((seed++))
    done
}

# 1. Małe taski (10-20), Małe grupy (2-5)
generate_batch 30 20 5 10 123456789

# 2. Średnie taski (50), Małe grupy (3)
generate_batch 30 50 3 20 123456789

# 3. Małe taski (20), Średnie grupy (10)
generate_batch 30 20 10 20 123456789

# 4. Średnie taski (50), Średnie grupy (10)
generate_batch 30 50 10 50 123456789

# 5. Wszystko duże (Taski 100, Grupy 20)
generate_batch 30 100 20 100 123456789

generate_batch 25 1000 200 1000 123456789
