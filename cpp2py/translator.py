# cpp2py/translator.py
import sys
from cpp2py import parser

def translate_file(input_path: str, output_path: str):
    with open(input_path, 'r', encoding='utf-8') as f:
        src = f.read()
    ast = parser.parse(src)
    py_code = ast.to_python(env={}, indent=0)
    # Add a small header
    header = "# Translated from C++ (subset) to Python\n"
    final = header + py_code + "\n"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final)
    print(f"Translation complete. Wrote {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python cpp2py/translator.py input.cpp output.py")
        sys.exit(1)
    translate_file(sys.argv[1], sys.argv[2])
