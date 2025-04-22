#!/bin/bash
# Set the directory containing your input files.
# You can modify this variable to the path of your input directory.
input_dir=$1

# Create the output directory if it doesn't exist.
output_dir=$2
mkdir -p "$output_dir"

# Loop over each file in the input directory.
for infile in "$input_dir"/*; do
    # Check if it is a file.
    if [ -f "$infile" ]; then
        # Extract the base name from the file path.
        filename=$(basename "$infile")
       	filename="${filename%.*}"
        # Run the command with -i set to the full file path and -o set to the corresponding output file.
        python3 -m clipy.main -i "$infile" -o "$output_dir/$filename" --preset verygood --use-profiler  > ./.cache/${filename}.txt
	rm "${filename}_preprocessed.mp4"
    fi
done
