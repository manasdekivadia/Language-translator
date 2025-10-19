# cpp2py/ast_nodes.py
from typing import List, Optional

def indent_text(s: str, indent: int = 0) -> str:
    prefix = ' ' * (4 * indent)
    return '\n'.join(prefix + line if line.strip() != '' else line for line in s.split('\n'))

class Node:
    def to_python(self, env: dict = None, indent: int = 0) -> str:
        raise NotImplementedError

class Program(Node):
    def __init__(self, stmts: List[Node]):
        self.stmts = stmts

    def to_python(self, env=None, indent=0):
        env = env or {}
        lines = []
        for s in self.stmts:
            lines.append(s.to_python(env, indent))
        return '\n'.join(l for l in lines if l is not None and l != '')

class Block(Node):
    def __init__(self, stmts):
        self.stmts = stmts

    def to_python(self, env=None, indent=0):
        env = env or {}
        lines = []
        for s in self.stmts:
            code = s.to_python(env, indent)
            if code:
                lines.append(code)
        return '\n'.join(lines)

class VarDecl(Node):
    def __init__(self, vtype, name, initializer=None):
        self.vtype = vtype  # 'int', 'float', ...
        self.name = name
        self.initializer = initializer

    def to_python(self, env=None, indent=0):
        if env is None: env = {}
        env[self.name] = self.vtype
        indent_str = ' ' * (4 * indent)
        if self.initializer:
            value = self.initializer.to_python(env, 0)
            return f"{indent_str}{self.name} = {value}"
        else:
            # default initialization
            if self.vtype in ('int',):
                val = '0'
            elif self.vtype in ('float', 'double'):
                val = '0.0'
            elif self.vtype in ('char', 'string'):
                val = "''"
            elif self.vtype == 'bool':
                val = 'False'
            else:
                val = 'None'
            return f"{indent_str}{self.name} = {val}"

class Assign(Node):
    def __init__(self, target, expr):
        self.target = target  # string name
        self.expr = expr

    def to_python(self, env=None, indent=0):
        indent_str = ' ' * (4 * indent)
        return f"{indent_str}{self.target} = {self.expr.to_python(env, 0)}"

class ReturnStmt(Node):
    def __init__(self, expr=None):
        self.expr = expr

    def to_python(self, env=None, indent=0):
        # we will ignore return since top-level in python doesn't need return in main
        return ''  # empty string

class IfStmt(Node):
    def __init__(self, cond, then_block: Block, else_block: Optional[Block]=None):
        self.cond = cond
        self.then_block = then_block
        self.else_block = else_block

    def to_python(self, env=None, indent=0):
        env = env or {}
        indent_str = ' ' * (4 * indent)
        cond_py = self.cond.to_python(env, 0)
        then_py = self.then_block.to_python(env, indent+1)
        lines = [f"{indent_str}if {cond_py}:"]
        if then_py.strip() == '':
            lines.append(' ' * (4 * (indent+1)) + 'pass')
        else:
            lines.append(then_py)
        if self.else_block:
            else_py = self.else_block.to_python(env, indent+1)
            lines.append(f"{indent_str}else:")
            if else_py.strip() == '':
                lines.append(' ' * (4 * (indent+1)) + 'pass')
            else:
                lines.append(else_py)
        return '\n'.join(lines)

class WhileStmt(Node):
    def __init__(self, cond, body: Block):
        self.cond = cond
        self.body = body

    def to_python(self, env=None, indent=0):
        indent_str = ' ' * (4 * indent)
        cond_py = self.cond.to_python(env, 0)
        body_py = self.body.to_python(env, indent+1)
        lines = [f"{indent_str}while {cond_py}:"]
        if body_py.strip() == '':
            lines.append(' ' * (4 * (indent+1)) + 'pass')
        else:
            lines.append(body_py)
        return '\n'.join(lines)

class ForStmt(Node):
    def __init__(self, init_stmt, cond_expr, iter_stmt, body: Block):
        self.init_stmt = init_stmt  # VarDecl or Assign
        self.cond_expr = cond_expr
        self.iter_stmt = iter_stmt
        self.body = body

    def to_python(self, env=None, indent=0):
        # Try to transform common C-style for loops to Python range
        env = env or {}
        indent_str = ' ' * (4 * indent)
        # Basic pattern: init: var = start ; cond: var < end ; iter: var++ or var += step
        try:
            if isinstance(self.init_stmt, VarDecl) or isinstance(self.init_stmt, Assign):
                # get var and start
                if isinstance(self.init_stmt, VarDecl):
                    var = self.init_stmt.name
                    start = self.init_stmt.initializer.to_python(env, 0) if self.init_stmt.initializer else '0'
                    env[var] = self.init_stmt.vtype
                else:
                    var = self.init_stmt.target
                    start = self.init_stmt.expr.to_python(env, 0)

                # cond: expect var < end  OR var <= end
                cond = self.cond_expr
                if isinstance(cond, BinaryOp) and isinstance(cond.left, Var) and cond.left.name == var and cond.op in ('<', '<='):
                    end_expr = cond.right.to_python(env, 0)
                    # determine range end adjustment for <=
                    if cond.op == '<=':
                        end = f"({end_expr}) + 1"
                    else:
                        end = end_expr

                    # iter: var++ or var += N or var = var + N
                    step = '1'
                    if isinstance(self.iter_stmt, UnaryOp) and self.iter_stmt.op == '++' and isinstance(self.iter_stmt.operand, Var) and self.iter_stmt.operand.name == var:
                        step = '1'
                    elif isinstance(self.iter_stmt, Assign) and self.iter_stmt.target == var:
                        # try to detect var = var + k or var += k
                        rhs = self.iter_stmt.expr
                        # rhs expected as BinaryOp var + k
                        if isinstance(rhs, BinaryOp) and rhs.left.name == var and rhs.op == '+':
                            step = rhs.right.to_python(env, 0)
                        else:
                            step = '1'
                    elif isinstance(self.iter_stmt, BinaryOp):  # maybe var += N encoded differently
                        step = '1'
                    # Build Python for
                    header = f"for {var} in range({start}, {end}"
                    if step != '1':
                        header += f", {step}"
                    header += "):"
                    body_py = self.body.to_python(env, indent+1)
                    if body_py.strip() == '':
                        body_py = ' ' * (4 * (indent+1)) + 'pass'
                    return '\n'.join([indent_str + header, body_py])
        except Exception:
            pass
        # Fallback: convert to while loop (emit init before)
        parts = []
        init_code = self.init_stmt.to_python(env, indent) if self.init_stmt else ''
        if init_code:
            parts.append(init_code)
        cond_py = self.cond_expr.to_python(env, 0) if self.cond_expr else 'True'
        body_py = self.body.to_python(env, indent+1)
        if self.iter_stmt:
            # add iter at end of body
            if body_py.strip() == '':
                body_py = ' ' * (4 * (indent+1)) + 'pass'
            body_py = body_py + '\n' + ' ' * (4 * (indent+1)) + self.iter_stmt.to_python(env, 0)
        parts.append(f"{indent_str}while {cond_py}:")
        parts.append(body_py)
        return '\n'.join(parts)

class CoutStmt(Node):
    def __init__(self, outputs: List[Node]):  # outputs are expressions or ENDL
        self.outputs = outputs

    def to_python(self, env=None, indent=0):
        env = env or {}
        indent_str = ' ' * (4 * indent)
        items = []
        newline = True
        for o in self.outputs:
            if isinstance(o, Endl):
                newline = True
            else:
                items.append(o.to_python(env, 0))
        if not items:
            return indent_str + "print()"
        joined = ', '.join(items)
        return indent_str + f"print({joined})"

class CinStmt(Node):
    def __init__(self, targets: List[str]):
        self.targets = targets

    def to_python(self, env=None, indent=0):
        env = env or {}
        indent_str = ' ' * (4 * indent)
        lines = []
        for t in self.targets:
            typ = env.get(t, None)
            if typ in ('int',):
                lines.append(f"{indent_str}{t} = int(input())")
            elif typ in ('float', 'double'):
                lines.append(f"{indent_str}{t} = float(input())")
            elif typ in ('char', 'string'):
                lines.append(f"{indent_str}{t} = input()")
            elif typ == 'bool':
                # naive conversion
                lines.append(f"{indent_str}{t} = input().lower() in ('1','true','yes') ")
            else:
                lines.append(f"{indent_str}{t} = input()")
        return '\n'.join(lines)

class Endl(Node):
    def to_python(self, env=None, indent=0):
        return ''

# Expression nodes
class Expr(Node):
    pass

class Var(Expr):
    def __init__(self, name):
        self.name = name

    def to_python(self, env=None, indent=0):
        return self.name

class Literal(Expr):
    def __init__(self, value):
        self.value = value

    def to_python(self, env=None, indent=0):
        if isinstance(self.value, str):
            return self.value
        elif isinstance(self.value, bool):
            return 'True' if self.value else 'False'
        else:
            return repr(self.value)

class BinaryOp(Expr):
    def __init__(self, left: Expr, op: str, right: Expr):
        self.left = left
        self.op = op
        self.right = right

    def to_python(self, env=None, indent=0):
        left = self.left.to_python(env, 0)
        right = self.right.to_python(env, 0)
        # map C operators to Python
        op = self.op
        if op == '&&':
            op = 'and'
        elif op == '||':
            op = 'or'
        return f"({left} {op} {right})"

# aliases to match usages
BinaryOpAlias = BinaryOp

class UnaryOp(Expr):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

    def to_python(self, env=None, indent=0):
        if self.op == '++':
            # not a direct python op; caller should handle as part of for-loop or translate to var = var + 1
            return f"{self.operand.to_python(env,0)} + 1"
        elif self.op == '--':
            return f"{self.operand.to_python(env,0)} - 1"
        elif self.op == '-':
            return f"-{self.operand.to_python(env,0)}"
        else:
            return f"{self.op}{self.operand.to_python(env,0)}"

# For simpler parser usage, expose names used in parser:
BinaryOp = BinaryOp
UnaryOp = UnaryOp
