# cpp2py/lexer.py
import re
import ply.lex as lex

# List of token names
tokens = [
    'ID', 'INT_CONST', 'FLOAT_CONST', 'CHAR_CONST', 'STRING_LITERAL',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
    'ASSIGN',
    'EQ', 'NEQ', 'LT', 'GT', 'LE', 'GE',
    'AND', 'OR',
    'LSHIFT', 'RSHIFT',
    'INC', 'DEC',
    'SEMICOLON', 'COMMA',
    'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE'
]

# Reserved words
reserved = {
    'int': 'INT',
    'float': 'FLOAT',
    'double': 'DOUBLE',
    'char': 'CHAR',
    'bool': 'BOOL',
    'if': 'IF',
    'else': 'ELSE',
    'for': 'FOR',
    'while': 'WHILE',
    'return': 'RETURN',
    'cin': 'CIN',
    'cout': 'COUT',
    'endl': 'ENDL',
    'main': 'MAIN'
}

tokens += list(reserved.values())

# Regular expression rules for simple tokens
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_ASSIGN = r'='
t_EQ = r'=='
t_NEQ = r'!='
t_LE = r'<='
t_GE = r'>='
t_LT = r'<'
t_GT = r'>'
t_AND = r'&&'
t_OR = r'\|\|'
t_LSHIFT = r'<<'
t_RSHIFT = r'>>'
t_INC = r'\+\+'
t_DEC = r'--'
t_SEMICOLON = r';'
t_COMMA = r','
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'

# String literal
def t_STRING_LITERAL(t):
    r'\"([^\\\n]|(\\.))*?\"'
    t.value = t.value
    return t

# Char constant 'a'
def t_CHAR_CONST(t):
    r'\'([^\\\n]|(\\.))\''
    t.value = t.value
    return t

# Float constant (must be before int)
def t_FLOAT_CONST(t):
    r'(\d+\.\d*|\d*\.\d+)([eE][-+]?\d+)?'
    t.value = float(t.value)
    return t

# Integer constant
def t_INT_CONST(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Identifiers and reserved words
def t_ID(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

# Comments: single-line //...
def t_COMMENT_SINGLE(t):
    r'//.*'
    pass

# Multi-line comments /* ... */
def t_COMMENT_MULTI(t):
    r'/\*[\s\S]*?\*/'
    pass

# Ignore spaces and tabs
t_ignore = ' \t\r'

# Track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Illegal character {t.value[0]!r} at line {t.lexer.lineno}")
    t.lexer.skip(1)

def build(**kwargs):
    """Build and return the lexer."""
    return lex.lex(**kwargs)

if __name__ == "__main__":
    # Test tokenizer
    data = '''
    int main() {
        int a = 5;
        cout << "Hello" << a << endl;
    }
    '''
    l = build()
    l.input(data)
    for tok in l:
        print(tok)
