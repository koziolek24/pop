#!/bin/bash

for input_file in $(ls in/in*.txt | sort -V); do
    filename=$(basename -- "$input_file")
    number="${filename//[^0-9]/}"
    output_file="out/out${number}.txt"
    
    cargo run < "$input_file" > r.out 2> /dev/null
    
    actual=$(< r.out)
    expected=$(< "$output_file")
    diff=$((actual - expected))

    if [ "$diff" -eq 0 ]; then
        echo "$input_file OK"
    else
        echo "$input_file ERR: $actual - $expected = $diff"
    fi

    rm r.out
done
