# C++ to Python Language Translator

## Overview

**Language Translator: C++ → Python** is a mini compiler project implemented in Python. It translates a simplified subset of C++ code into equivalent Python code by simulating **compiler front-end phases**:

* **Lexical Analysis** → Tokenizes C++ source code
* **Syntax Analysis (Parsing)** → Validates code against grammar rules
* **AST Construction** → Builds Abstract Syntax Tree as intermediate representation
* **Code Generation / Translation** → Converts AST to Python syntax

This project demonstrates **lexical analysis, parsing, AST design, and syntax-directed translation** concepts.

---

## Supported C++ Features

| Feature                        | Example                                                                              |   |   |
| ------------------------------ | ------------------------------------------------------------------------------------ | - | - |
| Variable Declarations          | `int a = 5;`, `float x = 2.5;`                                                       |   |   |
| Assignments                    | `a = 10;`                                                                            |   |   |
| Arithmetic & Logical Operators | `+`, `-`, `*`, `/`, `<`, `>`, `==`, `!=`, `&&`, `                                    |   | ` |
| Conditional Statements         | `if (a < b) { ... } else { ... }`                                                    |   |   |
| Loops                          | `while(condition) { ... }`, `for(i=0; i<n; i++) { ... }`                             |   |   |
| Input/Output                   | `cin >> a;` → `a = input()` <br> `cout << "text" << a << endl;` → `print("text", a)` |   |   |
| Simple `main()` function       | Flattened to top-level Python code                                                   |   |   |
| Comments                       | `//` and `/* ... */` are ignored                                                     |   |   |

**Not supported:** Classes, templates, pointers, references, STL, macros.

---

## Folder Structure

```text
Language-translator/
├─ cpp2py/
│  ├─ __init__.py          # marks cpp2py as a package
│  ├─ lexer.py             # lexical analyzer using PLY
│  ├─ parser.py            # grammar rules and parser
│  ├─ ast_nodes.py         # AST node classes with Python translation
│  ├─ translator.py        # main driver file
│  └─ utils.py             # indentation & helper functions
│
├─ input_examples/
│  └─ sample.cpp           # example input C++ program
│
├─ output/
│  └─ (generated Python files appear here)
│
├─ tests/
│  └─ test_samples.py      # optional unit tests
├─ requirements.txt        # pip dependencies
└─ README.md
```

---

## Installation

1. Clone the repository:

```bash
git clone <your-repo-url>
cd Language-translator
```

2. Create a virtual environment (optional but recommended):

```bash
python -m venv myvenv
myvenv\Scripts\activate       # Windows
# source myvenv/bin/activate  # Linux/Mac
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

`requirements.txt`:

```
ply
```

---

## Usage

### Step 1: Prepare Input

Place your C++ file inside `input_examples/`, e.g., `sample.cpp`.

Example:

```cpp
int main() {
    int a = 5;
    int b = 10;
    a = a + 1;
    if (a < b) {
        cout << "a is less" << endl;
    } else {
        cout << "a >= b" << endl;
    }
}
```

> ⚠️ Remove preprocessor directives like `#include <iostream>` for now.

---

### Step 2: Run the Translator

```bash
python -m cpp2py.translator input_examples/sample.cpp output/output.py
```

Expected output:

```
Translation complete! Output written to output/output.py
```

---

### Step 3: Run Generated Python Code

```bash
python output/output.py
```

Expected output:

```
a is less
```

---

## How It Works

1. **Lexical Analysis (`lexer.py`)**

   * Tokenizes keywords, identifiers, literals, operators, and symbols.
   * Skips whitespace and comments.

2. **Parsing (`parser.py`)**

   * Grammar rules for declarations, assignments, loops, conditionals, and I/O.
   * Builds AST nodes corresponding to each construct.

3. **AST (`ast_nodes.py`)**

   * Classes: `Program`, `Block`, `VarDecl`, `Assign`, `If`, `While`, `For`, `CoutStmt`, `CinStmt`, `Expr`
   * Each node has a `to_python(indent=0)` method to generate Python code.

4. **Translation (`translator.py`)**

   * Reads input C++ file → parses → builds AST → generates Python code → writes to output.

---
