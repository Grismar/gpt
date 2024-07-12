import fileinput
import sys

content = ''
if not sys.stdin.isatty():
    for line in fileinput.input(['-']):
        content += line

print(content)