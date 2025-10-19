# cpp2py/parser.py
import ply.yacc as yacc
from cpp2py.lexer import tokens, build as build_lexer
from cpp2py.ast_nodes import (
    Program, Block, VarDecl, Assign, IfStmt, WhileStmt,
    ForStmt, CoutStmt, CinStmt, ReturnStmt, BinaryOp,
    UnaryOp, Literal, Var, Endl
)

# Build lexer
lexer = build_lexer()

# Precedence rules (lowest to highest)
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQ', 'NEQ'),
    ('left', 'LT', 'LE', 'GT', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'UMINUS'),
)

def p_program(p):
    """program : global_items"""
    # Flatten main function if present
    stmts = []
    for it in p[1]:
        # if Block returned from main, flatten its stmts
        if isinstance(it, tuple) and it[0] == 'main':
            # it[1] is Block
            stmts.extend(it[1].stmts)
        else:
            stmts.append(it)
    p[0] = Program(stmts)

def p_global_items(p):
    """global_items : global_items global_item
                    | global_item"""
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_global_item(p):
    """global_item : function_def
                   | stmt"""
    p[0] = p[1]

def p_function_def(p):
    """function_def : type_specifier MAIN LPAREN RPAREN block"""
    # only support main
    p[0] = ('main', p[5])

def p_type_specifier(p):
    """type_specifier : INT
                      | FLOAT
                      | DOUBLE
                      | CHAR
                      | BOOL"""
    p[0] = p[1]

def p_block(p):
    """block : LBRACE stmt_list RBRACE"""
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

def p_stmt(p):
    """stmt : decl_stmt
            | expr_stmt
            | if_stmt
            | while_stmt
            | for_stmt
            | io_stmt
            | return_stmt
            | block"""
    p[0] = p[1]

def p_decl_stmt(p):
    """decl_stmt : type_specifier init_decl SEMICOLON
                 | type_specifier ID SEMICOLON"""
    if len(p) == 4 and isinstance(p[2], tuple):
        # type ID = expr
        _, name, expr = p[2]
        p[0] = VarDecl(p[1], name, expr)
    else:
        # no initializer
        name = p[2] if isinstance(p[2], str) else p[2]
        p[0] = VarDecl(p[1], name, None)

def p_init_decl(p):
    """init_decl : ID ASSIGN expression"""
    p[0] = ('init', p[1], p[3])

def p_expr_stmt(p):
    """expr_stmt : assignment SEMICOLON"""
    p[0] = p[1]

def p_assignment(p):
    """assignment : ID ASSIGN expression"""
    p[0] = Assign(p[1], p[3])

def p_if_stmt(p):
    """if_stmt : IF LPAREN expression RPAREN stmt ELSE stmt
               | IF LPAREN expression RPAREN stmt"""
    if len(p) == 8:
        p[0] = IfStmt(p[3], p[5] if hasattr(p[5],'stmts') else Block([p[5]]), p[7] if hasattr(p[7],'stmts') else Block([p[7]]))
    else:
        p[0] = IfStmt(p[3], p[5] if hasattr(p[5],'stmts') else Block([p[5]]), None)

def p_while_stmt(p):
    """while_stmt : WHILE LPAREN expression RPAREN stmt"""
    p[0] = WhileStmt(p[3], p[6] if hasattr(p[6],'stmts') else Block([p[6]]))

def p_for_stmt(p):
    """for_stmt : FOR LPAREN for_init SEMICOLON for_cond SEMICOLON for_iter RPAREN stmt"""
    init = p[3]
    cond = p[5]
    it = p[7]
    body = p[9] if hasattr(p[9],'stmts') else Block([p[9]])
    p[0] = ForStmt(init, cond, it, body)

def p_for_init(p):
    """for_init : decl_stmt
                | assignment
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
                 | assignment"""
    if len(p) == 3 and isinstance(p[2], str) and p[2] in ('++','--'):
        p[0] = UnaryOp(p[2], Var(p[1]))
    else:
        p[0] = p[1]

def p_io_stmt(p):
    """io_stmt : cout_stmt SEMICOLON
               | cin_stmt SEMICOLON"""
    p[0] = p[1]

def p_cout_stmt(p):
    """cout_stmt : COUT insertion_list"""
    # insertion_list is list of exprs
    p[0] = CoutStmt(p[2])

def p_insertion_list(p):
    """insertion_list : LSHIFT insertion_items"""
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
    if p[1] == 'endl':
        p[0] = Endl()
    else:
        p[0] = p[1]

def p_cin_stmt(p):
    """cin_stmt : CIN extraction_list"""
    p[0] = CinStmt(p[2])

def p_extraction_list(p):
    """extraction_list : RSHIFT extraction_items"""
    p[0] = p[2]

def p_extraction_items(p):
    """extraction_items : extraction_items RSHIFT extraction_target
                        | extraction_target"""
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_extraction_target(p):
    """extraction_target : ID"""
    p[0] = p[1]

def p_return_stmt(p):
    """return_stmt : RETURN expression SEMICOLON
                   | RETURN SEMICOLON"""
    if len(p) == 4:
        p[0] = ReturnStmt(p[2])
    else:
        p[0] = ReturnStmt()

def p_expression_binop(p):
    """expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression EQ expression
                  | expression NEQ expression
                  | expression LT expression
                  | expression GT expression
                  | expression LE expression
                  | expression GE expression
                  | expression AND expression
                  | expression OR expression"""
    p[0] = BinaryOp(p[1], p[2], p[3])

def p_expression_unary(p):
    """expression : MINUS expression %prec UMINUS"""
    p[0] = UnaryOp('-', p[2])

def p_expression_group(p):
    "expression : LPAREN expression RPAREN"
    p[0] = p[2]

def p_expression_literal(p):
    """expression : INT_CONST
                  | FLOAT_CONST
                  | STRING_LITERAL
                  | CHAR_CONST"""
    val = p[1]
    if isinstance(val, str):
        p[0] = Literal(val)
    else:
        p[0] = Literal(val)

def p_expression_id(p):
    "expression : ID"
    p[0] = Var(p[1])

def p_empty(p):
    "empty :"
    p[0] = None

def p_error(p):
    if p:
        print(f"Syntax error at token {p.type!r}, value {p.value!r}, line {p.lineno}")
    else:
        print("Syntax error at EOF")

def build_parser(**kwargs):
    return yacc.yacc(**kwargs)

parser = build_parser()

def parse(source_code: str):
    global lexer, parser
    lexer = build_lexer()
    result = parser.parse(source_code, lexer=lexer)
    return result

if __name__ == "__main__":
    sample = '''
    #include <iostream>
    using namespace std;
    int main() {
        int a = 5;
        int b = 10;
        for (int i = 0; i < 3; i++) {
            if (a < b) {
                cout << "a is less" << endl;
            } else {
                cout << "a >= b" << endl;
            }
            a = a + 1;
        }
        return 0;
    }
    '''
    prog = parse(sample)
    print(prog.to_python())
