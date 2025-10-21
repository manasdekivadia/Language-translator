import ply.yacc as yacc
from cpp2py.lexer import tokens, build as build_lexer
from cpp2py.ast_nodes import *

# -------------------- Lexer --------------------
lexer = build_lexer()

# -------------------- Operator Precedence --------------------
# Ternary (?:) added above assignment/comma
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQ', 'NEQ'),
    ('left', 'LT', 'LE', 'GT', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MOD'),
    ('right', 'UMINUS', 'NOT'),
)

# -------------------- Program --------------------
def p_program(p):
    "program : global_items"
    stmts = []
    for item in p[1]:
        # Extract main function body
        if isinstance(item, FuncDef) and item.name == 'main':
            stmts.extend(item.body.stmts)
        elif item is not None:
            stmts.append(item)
    p[0] = Program(stmts)

def p_global_items(p):
    """global_items : global_items global_item
                    | global_item"""
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

# -------------------- Global items --------------------
def p_global_item(p):
    """global_item : function_def
                   | stmt
                   | class_def"""
    p[0] = p[1]

# -------------------- Classes (skipped for now) --------------------
def p_class_def(p):
    "class_def : CLASS ID LBRACE class_members RBRACE SEMICOLON"
    p[0] = None

def p_class_members(p):
    """class_members : class_members class_member
                     | empty"""
    p[0] = None

def p_class_member(p):
    """class_member : type_specifier ID SEMICOLON
                    | function_def"""
    p[0] = None

# -------------------- Functions --------------------
def p_function_def(p):
    "function_def : type_specifier ID LPAREN param_list RPAREN block"
    p[0] = FuncDef(p[2], p[1], p[4], p[6])


def p_param_list(p):
    """param_list : param_list COMMA param
                  | param
                  | empty"""
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    elif len(p) == 2 and p[1] is not None:
        p[0] = [p[1]]
    else:
        p[0] = []

def p_param(p):
    "param : type_specifier ID"
    p[0] = p[2]

# -------------------- Types --------------------
def p_type_specifier(p):
    """type_specifier : INT
                      | FLOAT
                      | DOUBLE
                      | CHAR
                      | BOOL
                      | STRING
                      | VOID"""
    p[0] = p[1]

# -------------------- Blocks --------------------
def p_block(p):
    "block : LBRACE stmt_list RBRACE"
    p[0] = Block(p[2])

def p_stmt_list(p):
    """stmt_list : stmt_list stmt
                 | empty"""
    if len(p) == 3:
        if p[1] is None:
            p[0] = [p[2]]
        else:
            p[0] = p[1] + [p[2]]
    else:
        p[0] = []

# -------------------- Statements --------------------
def p_stmt(p):
    """stmt : decl_stmt
            | array_decl_stmt
            | assignment
            | expr_stmt
            | if_stmt
            | while_stmt
            | for_stmt
            | io_stmt
            | return_stmt
            | break_stmt
            | continue_stmt
            | block"""
    if isinstance(p[1], Expr):
        p[0] = ExprStmt(p[1])
    else:
        p[0] = p[1]

# -------------------- Variable Declarations --------------------
def p_for_decl(p):
    """for_decl : type_specifier init_decl
                | type_specifier ID"""
    if len(p) == 3 and isinstance(p[2], tuple):
        _, name, expr = p[2]
        p[0] = VarDecl(p[1], name, expr)
    else:
        p[0] = VarDecl(p[1], p[2], None)

def p_decl_stmt(p):
    """decl_stmt : for_decl SEMICOLON"""
    p[0] = p[1]

def p_init_decl(p):
    "init_decl : ID ASSIGN expression"
    p[0] = ('init', p[1], p[3])

# -------------------- Array Declarations --------------------
def p_array_decl_stmt(p):
    "array_decl_stmt : type_specifier ID LBRACKET INT_CONST RBRACKET SEMICOLON"
    p[0] = ArrayDecl(p[2], p[4], p[1])

# -------------------- Assignments --------------------
def p_assignment(p):
    """assignment : ID ASSIGN expression SEMICOLON
                  | ID LBRACKET expression RBRACKET ASSIGN expression SEMICOLON"""
    if len(p) == 5:
        p[0] = Assign(Var(p[1]), p[3])
    else:
        p[0] = Assign(ArrayRef(p[1], p[3]), p[6])

# -------------------- Expressions --------------------
def p_expr_stmt(p):
    "expr_stmt : expression SEMICOLON"
    p[0] = p[1]

def p_func_call(p):
    "func_call : ID LPAREN arg_list RPAREN"
    p[0] = FuncCall(p[1], p[3])

def p_arg_list(p):
    """arg_list : arg_list COMMA expression
                | expression
                | empty"""
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    elif len(p) == 2 and p[1] is not None:
        p[0] = [p[1]]
    else:
        p[0] = []

def p_unary_inc_dec(p):
    """unary_inc_dec : ID INC
                     | ID DEC"""
    p[0] = UnaryOp(p[2], Var(p[1]))

def p_compound_assignment(p):
    """compound_assignment : ID PLUS_ASSIGN expression
                           | ID MINUS_ASSIGN expression
                           | ID TIMES_ASSIGN expression
                           | ID DIVIDE_ASSIGN expression"""
    op_map = {'+=': '+', '-=': '-', '*=': '*', '/=': '/'}
    p[0] = Assign(Var(p[1]), BinaryOp(Var(p[1]), op_map[p[2]], p[3]))

# Ternary expression
def p_expression_ternary(p):
    "expression : expression QMARK expression COLON expression"
    p[0] = TernaryOp(p[1], p[3], p[5])

# Function call
def p_expression_func_call(p):
    "expression : func_call"
    p[0] = p[1]

# Unary inc/dec
def p_expression_unary_inc_dec(p):
    "expression : unary_inc_dec"
    p[0] = p[1]

# Compound assignment
def p_expression_compound_assignment(p):
    "expression : compound_assignment"
    p[0] = p[1]

# Binary ops
def p_expression_binop(p):
    """expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression MOD expression
                  | expression EQ expression
                  | expression NEQ expression
                  | expression LT expression
                  | expression GT expression
                  | expression LE expression
                  | expression GE expression
                  | expression AND expression
                  | expression OR expression"""
    p[0] = BinaryOp(p[1], p[2], p[3])

# Unary ops
def p_expression_unary(p):
    """expression : MINUS expression %prec UMINUS
                  | NOT expression %prec NOT"""
    p[0] = UnaryOp(p[1], p[2])

def p_expression_group(p):
    "expression : LPAREN expression RPAREN"
    p[0] = p[2]

def p_expression_literal(p):
    """expression : INT_CONST
                  | FLOAT_CONST
                  | STRING_LITERAL
                  | CHAR_CONST"""
    p[0] = Literal(p[1])

def p_expression_id(p):
    "expression : ID"
    p[0] = Var(p[1])

def p_expression_array(p):
    "expression : ID LBRACKET expression RBRACKET"
    p[0] = ArrayRef(p[1], p[3])

# -------------------- Loops --------------------
def p_while_stmt(p):
    "while_stmt : WHILE LPAREN expression RPAREN stmt"
    p[0] = WhileStmt(p[3], p[5] if isinstance(p[5], Block) else Block([p[5]]))

def p_for_stmt(p):
    "for_stmt : FOR LPAREN for_init SEMICOLON for_cond SEMICOLON for_iter RPAREN stmt"
    p[0] = ForStmt(p[3], p[5], p[7], p[9] if isinstance(p[9], Block) else Block([p[9]]))

def p_for_init(p):
    """for_init : for_decl
                | assignment
                | unary_inc_dec
                | compound_assignment
                | empty"""
    p[0] = p[1]

def p_for_cond(p):
    """for_cond : expression
                | empty"""
    p[0] = p[1]

def p_for_iter(p):
    """for_iter : expr_iter
                | empty"""
    p[0] = p[1]

def p_expr_iter(p):
    """expr_iter : ID INC
                 | ID DEC
                 | assignment
                 | compound_assignment"""
    if len(p) == 3:
        p[0] = UnaryOp(p[2], Var(p[1]))
    else:
        p[0] = p[1]

# -------------------- I/O --------------------
def p_io_stmt(p):
    """io_stmt : cout_stmt
               | cin_stmt"""
    p[0] = p[1]

def p_cout_stmt(p):
    "cout_stmt : COUT insertion_list SEMICOLON"
    p[0] = CoutStmt(p[2])

def p_insertion_list(p):
    "insertion_list : LSHIFT insertion_items"
    p[0] = p[2]

def p_insertion_items(p):
    """insertion_items : insertion_items LSHIFT insertion_item
                       | insertion_item"""
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_insertion_item(p):
    """insertion_item : expression
                      | ENDL"""
    p[0] = Endl() if p[1] == 'endl' else p[1]

def p_cin_stmt(p):
    "cin_stmt : CIN extraction_list SEMICOLON"
    p[0] = CinStmt(p[2])

def p_extraction_list(p):
    "extraction_list : RSHIFT extraction_items"
    p[0] = p[2]

def p_extraction_items(p):
    """extraction_items : extraction_items RSHIFT extraction_target
                        | extraction_target"""
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_extraction_target(p):
    "extraction_target : ID"
    p[0] = Var(p[1])

# -------------------- Control Flow --------------------
def p_if_stmt(p):
    """if_stmt : IF LPAREN expression RPAREN stmt ELSE stmt
               | IF LPAREN expression RPAREN stmt"""
    if_body = p[5] if isinstance(p[5], Block) else Block([p[5]])
    if len(p) == 8:
        else_body = p[7] if isinstance(p[7], Block) else Block([p[7]])
        p[0] = IfStmt(p[3], if_body, else_body)
    else:
        p[0] = IfStmt(p[3], if_body)

def p_return_stmt(p):
    """return_stmt : RETURN expression SEMICOLON
                   | RETURN SEMICOLON"""
    if len(p) == 4:
        p[0] = ReturnStmt(p[2])
    else:
        p[0] = ReturnStmt()

def p_break_stmt(p):
    "break_stmt : BREAK SEMICOLON"
    p[0] = BreakStmt()

def p_continue_stmt(p):
    "continue_stmt : CONTINUE SEMICOLON"
    p[0] = ContinueStmt()

# -------------------- Empty --------------------
def p_empty(p):
    "empty :"
    p[0] = None

# -------------------- Error Handling --------------------
def p_error(p):
    if p:
        print(f"[Parser Error] Unexpected token {p.type!r} ('{p.value}') at line {getattr(p, 'lineno', '?')}")
    else:
        print("[Parser Error] Unexpected end of input")

# -------------------- Build Parser --------------------
def build_parser(**kwargs):
    return yacc.yacc(debug=False, **kwargs)

parser = build_parser()

def parse(source_code: str):
    global lexer, parser
    lexer = build_lexer()
    try:
        result = parser.parse(source_code, lexer=lexer)
        if result is None:
            print("[Parser Warning] No valid AST generated; returning empty Program.")
            return Program([])
        return result
    except Exception as e:
        print(f"[Parser Exception] {e}")
        return Program([])
