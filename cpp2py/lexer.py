import ply.lex as lex

# -------------------- Token definitions --------------------
tokens = [
    'ID', 'INT_CONST', 'FLOAT_CONST', 'CHAR_CONST', 'STRING_LITERAL',
    # Operators
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
    'ASSIGN', 'PLUS_ASSIGN', 'MINUS_ASSIGN', 'TIMES_ASSIGN', 'DIVIDE_ASSIGN',
    'EQ', 'NEQ', 'LT', 'GT', 'LE', 'GE',
    'AND', 'OR', 'NOT',
    'LSHIFT', 'RSHIFT',
    'INC', 'DEC',
    # Punctuation
    'SEMICOLON', 'COMMA',
    'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET',
   
    'QMARK', 'COLON',
]


# -------------------- Reserved keywords --------------------
reserved = {
    'int': 'INT',
    'float': 'FLOAT',
    'double': 'DOUBLE',
    'char': 'CHAR',
    'bool': 'BOOL',
    'string': 'STRING',
    'if': 'IF',
    'else': 'ELSE',
    'for': 'FOR',
    'while': 'WHILE',
    'return': 'RETURN',
    'cin': 'CIN',
    'cout': 'COUT',
    'endl': 'ENDL',
    'break': 'BREAK',
    'continue': 'CONTINUE',
    'class': 'CLASS',
    'void': 'VOID',
}

tokens += list(reserved.values())

# -------------------- Operators & punctuation --------------------
t_LSHIFT        = r'<<'
t_RSHIFT        = r'>>'
t_PLUS_ASSIGN   = r'\+='
t_MINUS_ASSIGN  = r'-='
t_TIMES_ASSIGN  = r'\*='
t_DIVIDE_ASSIGN = r'/='
t_EQ            = r'=='
t_NEQ           = r'!='
t_LE            = r'<='
t_GE            = r'>='
t_AND           = r'&&'
t_OR            = r'\|\|'
t_INC           = r'\+\+'
t_DEC           = r'--'

t_QMARK = r'\?'
t_COLON = r':'

t_PLUS          = r'\+'
t_MINUS         = r'-'
t_TIMES         = r'\*'
t_DIVIDE        = r'/'
t_MOD           = r'%'
t_ASSIGN        = r'='
t_LT            = r'<'
t_GT            = r'>'
t_NOT           = r'!'

t_SEMICOLON     = r';'
t_COMMA         = r','
t_LPAREN        = r'\('
t_RPAREN        = r'\)'
t_LBRACE        = r'\{'
t_RBRACE        = r'\}'
t_LBRACKET      = r'\['
t_RBRACKET      = r'\]'

# -------------------- Literals --------------------
def t_STRING_LITERAL(t):
    r'\"([^\\\n]|(\\.))*?\"'
    t.value = t.value
    return t

def t_CHAR_CONST(t):
    r'\'([^\\\n]|(\\.))\''
    return t

def t_FLOAT_CONST(t):
    r'(\d+\.\d*|\d*\.\d+)([eE][-+]?\d+)?'
    try:
        t.value = float(t.value)
    except ValueError:
        print(f"[Lexer Error] Invalid float constant: {t.value}")
        t.value = 0.0
    return t

def t_INT_CONST(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print(f"[Lexer Error] Invalid integer constant: {t.value}")
        t.value = 0
    return t

# -------------------- Preprocessor & namespace --------------------
def t_PREPROCESSOR(t):
    r'\#\s*(include|define|ifdef|ifndef|endif|pragma|error).*'
    # Entire preprocessor line ignored
    t.lexer.lineno += 1
    pass

def t_NAMESPACE_USING(t):
    r'using\s+namespace\s+[A-Za-z_][A-Za-z0-9_]*\s*;'
    # Ignore using namespace declarations
    pass

# -------------------- Identifiers --------------------
def t_ID(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

# -------------------- Comments --------------------
def t_COMMENT_SINGLE(t):
    r'//[^\n]*'
    # ignore single-line comments
    pass

def t_COMMENT_MULTI(t):
    r'/\*[\s\S]*?\*/'
    t.lexer.lineno += t.value.count('\n')
    pass

# -------------------- Whitespace --------------------
t_ignore = ' \t\r'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# -------------------- Error handling --------------------
def t_error(t):
    print(f"[Lexer Error] Illegal character '{t.value[0]}' at line {t.lexer.lineno}")
    t.lexer.skip(1)

# -------------------- Build lexer --------------------
def build(**kwargs):
    """Builds and returns the lexer."""
    return lex.lex(debug=False, **kwargs)

# -------------------- Test --------------------
if __name__ == "__main__":
    data = r'''
    #include <iostream>
    #define PI 3.14
    using namespace std;

    class Point {
        int x;
        int y;
        void move(int dx, int dy) {
            x += dx;
            y += dy;
        }
    };

    int main() {
        int a = 5;
        float b = 3.2;
        string s = "hello\nworld";
        char c = 'A';
        cout << s << " " << c << endl;
        for (int i = 0; i < 3; i++) {
            if (a < 10) break;
            a += 1;
        }
        /* multi
           line
           comment */
        // single-line comment
        return 0;
    }
    '''
    lexer = build()
    lexer.input(data)
    print("---- TOKENS ----")
    for tok in lexer:
        print(f"{tok.lineno:3} {tok.type:15} {tok.value!r}")
