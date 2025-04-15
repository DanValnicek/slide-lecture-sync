import re


def parse_file(file_path):
    result = []
    current_time = None

    with open(file_path, 'r') as file:
        # Match time
        pattern = r'\["time"\]=(\d+)[^\[]*\["label"\]="([^\"]*)\",'
        for match in re.finditer(pattern, file.read()):
            current_time = int(match.group(1))
            label = int(match.group(2))
            result.append({"time": current_time, "label": label})

    return result


# Usage example
file_path = "data/testing/IDM_2023-11-15_1080p.txt"  # Replace with your file path
parsed_data = parse_file(file_path)

# Print the parsed test_data
print(parsed_data)
