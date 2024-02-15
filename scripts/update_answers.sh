#!/bin/bash
cd scripts
# Check if exactly one argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <argument>"
    exit 1
fi

# Pass the first argument to the Python script
python3 get_single-hop_updated_answers.py "$1"
python3 get_multi-hop_updated_answers.py "$1"