input_file = "roads.txt"
output_file = "output_1.txt"

filtered_lines = []

with open(input_file, "r") as file:
    for line in file:
        columns = line.split()
        first_column = int(columns[0])
        second_column = int(columns[1])
        
        if first_column <= 9999 and second_column <= 9999:
            filtered_lines.append(line)

with open(output_file, "w") as file:
    file.writelines(filtered_lines)
