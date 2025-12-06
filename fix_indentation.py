#!/usr/bin/env python3
"""Fix indentation in flow_engine_service.py"""

with open('app/services/flow_engine_service.py', 'r') as f:
    lines = f.readlines()

# Fix the indentation issue - change 8 spaces to 4 spaces for exception blocks
for i, line in enumerate(lines):
    if i in [1065, 1073]:  # The except blocks
        if line.startswith('        except'):
            lines[i] = '    ' + line[8:]  # Replace 8 spaces with 4 spaces
        elif line.startswith('        #'):
            lines[i] = '    ' + line[8:]  # Replace 8 spaces with 4 spaces
        elif line.startswith('        logger'):
            lines[i] = '    ' + line[8:]  # Replace 8 spaces with 4 spaces
        elif line.startswith('        #'):
            lines[i] = '    ' + line[8:]  # Replace 8 spaces with 4 spaces
        elif line.startswith('        return'):
            lines[i] = '    ' + line[8:]  # Replace 8 spaces with 4 spaces
        elif line.startswith('        fallback'):
            lines[i] = '    ' + line[8:]  # Replace 8 spaces with 4 spaces

with open('app/services/flow_engine_service.py', 'w') as f:
    f.writelines(lines)

print("Indentation fixed!")