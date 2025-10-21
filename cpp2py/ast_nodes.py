from typing import List, Optional

def indent_text(s: str, indent: int = 0) -> str:
    """Indent text by 4 * indent spaces."""
    prefix = ' ' * (4 * indent)
    return '\n'.join(prefix + line if line.strip() != '' else line for line in s.split('\n'))

# ------------------ Base Node ------------------
class Node:
    def to_python(self, env: dict = None, indent: int = 0) -> str:
        raise NotImplementedError


# ------------------ Program / Block ------------------
class Program(Node):
    def __init__(self, stmts: List[Node]):
        self.stmts = stmts

    def to_python(self, env=None, indent=0):
        env = env or {}
        lines = []
        for s in self.stmts:
            # Skip 'return' statements that appear at global level (like from main)
            if isinstance(s, ReturnStmt):
                continue
            if s:
                lines.append(s.to_python(env, indent))
        return '\n'.join(lines) if lines else ''



class Block(Node):
    def __init__(self, stmts: List[Node]):
        self.stmts = stmts

    def to_python(self, env=None, indent=0):
        env = env or {}
        lines = [s.to_python(env, indent) for s in self.stmts if s]
        return '\n'.join(lines) if lines else ''


# ------------------ Statements ------------------
class ExprStmt(Node):
    def __init__(self, expr: 'Expr'):
        self.expr = expr

    def to_python(self, env=None, indent=0):
        indent_str = ' ' * (4 * indent)

        # Special handling for C++'s i++ and i-- when used as a statement (side effect)
        if isinstance(self.expr, UnaryOp) and self.expr.op in ('++', '--'):
            op = '+' if self.expr.op == '++' else '-'
            target_py = self.expr.operand.to_python(env, 0)
            return f"{indent_str}{target_py} = {target_py} {op} 1"

        # Handle all other expressions (function calls, etc.)
        return f"{indent_str}{self.expr.to_python(env, 0)}"


# ------------------ Variables ------------------
class VarDecl(Node):
    def __init__(self, vtype: str, name: str, initializer: Optional['Expr'] = None):
        self.vtype = vtype
        self.name = name
        self.initializer = initializer

    def to_python(self, env=None, indent=0):
        env = env or {}
        env[self.name] = self.vtype.lower()  # store type in lowercase
        indent_str = ' ' * (4 * indent)

        if self.initializer:
            value = self.initializer.to_python(env, 0)
            return f"{indent_str}{self.name} = {value}"

        default_map = {
            'int': '0', 'float': '0.0', 'double': '0.0',
            'char': "''", 'string': "''", 'bool': 'False', 'void': 'None'
        }
        val = default_map.get(self.vtype.lower(), 'None')
        return f"{indent_str}{self.name} = {val}"



class ArrayDecl(Node):
    def __init__(self, name: str, size: int, vtype: str = 'int', initializer: Optional['Expr'] = None):
        self.name = name
        self.size = size
        self.vtype = vtype
        self.initializer = initializer

    def to_python(self, env=None, indent=0):
        env = env or {}
        env[self.name] = f"list[{self.vtype}]"
        indent_str = ' ' * (4 * indent)

        if self.initializer:
            init = self.initializer.to_python(env, 0)
            return f"{indent_str}{self.name} = {init}"

        default_map = {
            'int': '0', 'float': '0.0', 'double': '0.0',
            'char': "''", 'string': "''", 'bool': 'False'
        }
        val = default_map.get(self.vtype, 'None')
        return f"{indent_str}{self.name} = [{val}] * {self.size}"


class Assign(Node):
    # Keeping op='=' for parser compatibility, though the parser expands compound assignments
    def __init__(self, target: 'Expr', expr: 'Expr', op: str = '='):
        self.target = target  # Var or ArrayRef (both Expr)
        self.expr = expr
        self.op = op

    def to_python(self, env=None, indent=0):
        indent_str = ' ' * (4 * indent)
        target_py = self.target.to_python(env, 0)
        rhs = self.expr.to_python(env, 0)
        return f"{indent_str}{target_py} {self.op} {rhs}"


# ------------------ Control Flow ------------------
class IfStmt(Node):
    def __init__(self, cond: 'Expr', then_block: Block, else_block: Optional[Block] = None):
        self.cond = cond
        self.then_block = then_block
        self.else_block = else_block

    def to_python(self, env=None, indent=0):
        env = env or {}
        indent_str = ' ' * (4 * indent)
        cond_py = self.cond.to_python(env, 0)
        then_py = self.then_block.to_python(env, indent + 1)
        lines = [f"{indent_str}if {cond_py}:"]
        lines.append(then_py if then_py.strip() else ' ' * (4 * (indent + 1)) + 'pass')

        if self.else_block:
            else_py = self.else_block.to_python(env, indent + 1)
            lines.append(f"{indent_str}else:")
            lines.append(else_py if else_py.strip() else ' ' * (4 * (indent + 1)) + 'pass')
        return '\n'.join(lines)


class WhileStmt(Node):
    def __init__(self, cond: 'Expr', body: Block):
        self.cond = cond
        self.body = body

    def to_python(self, env=None, indent=0):
        indent_str = ' ' * (4 * indent)
        cond_py = self.cond.to_python(env, 0)
        body_py = self.body.to_python(env, indent + 1)
        lines = [f"{indent_str}while {cond_py}:"]
        lines.append(body_py if body_py.strip() else ' ' * (4 * (indent + 1)) + 'pass')
        return '\n'.join(lines)


class ForStmt(Node):
    def __init__(self, init_stmt: Optional[Node], cond_expr: Optional['Expr'], iter_stmt: Optional[Node], body: Block):
        self.init_stmt = init_stmt
        self.cond_expr = cond_expr
        self.iter_stmt = iter_stmt
        self.body = body

    def to_python(self, env=None, indent=0):
        env = env or {}
        indent_str = ' ' * (4 * indent)

        # Try to convert to range-based for if possible
        try:
            var = None
            start = None
            end = None

            # 1. Init statement
            if isinstance(self.init_stmt, VarDecl):
                var = self.init_stmt.name
                start = self.init_stmt.initializer.to_python(env, 0) if self.init_stmt.initializer else '0'
            elif isinstance(self.init_stmt, Assign):
                # init assigned to a Var target
                tgt = self.init_stmt.target
                if isinstance(tgt, Var):
                    var = tgt.name
                    start = self.init_stmt.expr.to_python(env, 0)

            # 2. Condition must be binary op comparing the same var
            if var and isinstance(self.cond_expr, BinaryOp) and isinstance(self.cond_expr.left, Var) and self.cond_expr.left.name == var:
                end = self.cond_expr.right.to_python(env, 0)
                op = self.cond_expr.op
                step = '1'

                if op in ('<', '<='):
                    if op == '<=':
                        end = f"({end}) + 1"

                    # iteration: i++ or i = i + k
                    if isinstance(self.iter_stmt, ExprStmt) and isinstance(self.iter_stmt.expr, UnaryOp) and self.iter_stmt.expr.op == '++':
                        pass
                    elif isinstance(self.iter_stmt, Assign) and isinstance(self.iter_stmt.expr, BinaryOp) and self.iter_stmt.expr.op == '+' and isinstance(self.iter_stmt.expr.right, Literal):
                        step = self.iter_stmt.expr.right.to_python(env, 0)

                    header = f"for {var} in range({start}, {end}"
                    if step != '1':
                        header += f", {step}"
                    header += "):"

                    body_py = self.body.to_python(env, indent + 1)
                    if not body_py.strip():
                        body_py = ' ' * (4 * (indent + 1)) + 'pass'

                    return '\n'.join([indent_str + header, body_py])
        except Exception:
            # fallback below
            pass

        # Fallback: translate to while loop
        init_code = self.init_stmt.to_python(env, indent) if self.init_stmt else ''
        cond_py = self.cond_expr.to_python(env, 0) if self.cond_expr else 'True'
        body_py = self.body.to_python(env, indent + 1)

        # handle iteration appended at end of body
        if self.iter_stmt:
            if isinstance(self.iter_stmt, ExprStmt) and isinstance(self.iter_stmt.expr, UnaryOp) and self.iter_stmt.expr.op in ('++', '--'):
                op = '+' if self.iter_stmt.expr.op == '++' else '-'
                target_py = self.iter_stmt.expr.operand.to_python(env, 0)
                iter_py = f"{target_py} = {target_py} {op} 1"
            else:
                # ensure indent consistent for appended iteration code
                raw_iter = self.iter_stmt.to_python(env, 0)
                iter_py = raw_iter if raw_iter.strip() else ''

            if body_py.strip():
                body_py += '\n' + ' ' * (4 * (indent + 1)) + iter_py
            else:
                body_py = ' ' * (4 * (indent + 1)) + iter_py

        if not body_py.strip():
            body_py = ' ' * (4 * (indent + 1)) + 'pass'

        parts = []
        if init_code:
            parts.append(init_code)
        parts.append(f"{indent_str}while {cond_py}:")
        parts.append(body_py)
        return '\n'.join(parts)


# ------------------ I/O ------------------
class CoutStmt(Node):
    def __init__(self, outputs: List[Node]):
        self.outputs = outputs

    def to_python(self, env=None, indent=0):
        env = env or {}
        indent_str = ' ' * (4 * indent)
        py_items = []

        for o in self.outputs:
            if isinstance(o, Endl):
                # Skip endl for now; Python print adds newline automatically
                continue
            # If it's a Node (Var, Literal, FuncCall, etc.), get its Python code
            if isinstance(o, Node):
                py_items.append(o.to_python(env, 0))
            else:
                # Fallback: convert raw value to repr
                py_items.append(repr(o))

        joined = ", ".join(py_items)
        return f"{indent_str}print({joined})" if py_items else f"{indent_str}print()"



class CinStmt(Node):
    def __init__(self, targets: List['Var']):
        self.targets = targets

    def to_python(self, env=None, indent=0):
        if env is None:
            env = {}  # only initialize if None
        indent_str = ' ' * (4 * indent)
        lines = []

        for t in self.targets:
            typ = env.get(t.name, 'string').lower()

            if typ == 'int':
                lines.append(f"{indent_str}{t.name} = int(input())")
            elif typ in ('float', 'double'):
                lines.append(f"{indent_str}{t.name} = float(input())")
            elif typ == 'char':
                lines.append(f"{indent_str}{t.name} = input()[0]")
            elif typ == 'string':
                lines.append(f"{indent_str}{t.name} = input()")
            elif typ == 'bool':
                lines.append(f"{indent_str}{t.name} = input().lower() in ('1','true','yes')")
            else:
                lines.append(f"{indent_str}{t.name} = input()")

        return '\n'.join(lines)





class Endl(Node):
    def to_python(self, env=None, indent=0):
        return ''


# ------------------ Expressions ------------------
class Expr(Node):
    pass


class Var(Expr):
    def __init__(self, name: str):
        self.name = name

    def to_python(self, env=None, indent=0):
        return self.name


class ArrayRef(Expr):
    def __init__(self, name: str, index: Expr):
        self.name = name
        self.index = index

    def to_python(self, env=None, indent=0):
        index_py = self.index.to_python(env, 0)
        return f"{self.name}[{index_py}]"


class Literal(Expr):
    def __init__(self, value):
        self.value = value

    def to_python(self, env=None, indent=0):
        # If string literal already has surrounding quotes, return as-is
        if isinstance(self.value, str):
            if len(self.value) >= 2 and self.value[0] == '"' and self.value[-1] == '"':
                return self.value
            return repr(self.value)
        elif isinstance(self.value, bool):
            return 'True' if self.value else 'False'
        return repr(self.value)


class BinaryOp(Expr):
    def __init__(self, left: Expr, op: str, right: Expr):
        self.left, self.op, self.right = left, op, right

    def to_python(self, env=None, indent=0):
        left = self.left.to_python(env, 0)
        right = self.right.to_python(env, 0)
        op = self.op
        if op == '&&':
            op = 'and'
        elif op == '||':
            op = 'or'
        # keep other operators as-is (==, !=, <, >, +, -, *, /, etc.)
        return f"({left} {op} {right})"


class UnaryOp(Expr):
    def __init__(self, op: str, operand: Expr):
        self.op, self.operand = op, operand

    def to_python(self, env=None, indent=0):
        op = self.op

        if op == '-':
            return f"-({self.operand.to_python(env, 0)})"
        if op == '!':
            return f"(not {self.operand.to_python(env, 0)})"

        # ++/-- used within expression should be handled by statement-level translation.
        if op in ('++', '--'):
            return self.operand.to_python(env, 0)

        return f"{op}{self.operand.to_python(env, 0)}"


# ------------------ Additional Statements ------------------
class ReturnStmt(Node):
    def __init__(self, expr: Optional[Expr] = None):
        self.expr = expr

    def to_python(self, env=None, indent=0):
        indent_str = ' ' * (4 * indent)
        if self.expr:
            return f"{indent_str}return {self.expr.to_python(env, 0)}"
        return f"{indent_str}return None"


class BreakStmt(Node):
    def to_python(self, env=None, indent=0):
        return ' ' * (4 * indent) + 'break'


class ContinueStmt(Node):
    def to_python(self, env=None, indent=0):
        return ' ' * (4 * indent) + 'continue'


class TernaryOp(Expr):
    def __init__(self, cond: Expr, true_expr: Expr, false_expr: Expr):
        self.cond, self.true_expr, self.false_expr = cond, true_expr, false_expr

    def to_python(self, env=None, indent=0):
        return f"({self.true_expr.to_python(env, 0)} if {self.cond.to_python(env, 0)} else {self.false_expr.to_python(env, 0)})"


class FuncDef(Node):
    def __init__(self, name: str, vtype: str, params: List[str], body: Block):
        self.name = name
        self.vtype = vtype
        self.params = params
        self.body = body

    def to_python(self, env=None, indent=0):
        indent_str = ' ' * (4 * indent)
        params_str = ", ".join(self.params) if self.params else ""
        body_code = "\n".join(stmt.to_python(env, indent + 1) for stmt in self.body.stmts)
        if not body_code.strip():
            body_code = ' ' * (4 * (indent + 1)) + "pass"
        return f"{indent_str}def {self.name}({params_str}):\n{body_code}"



class FuncCall(Expr):
    def __init__(self, func_name: str, args: List[Expr]):
        self.func_name = func_name
        self.args = args

    def to_python(self, env=None, indent=0):
        env = env or {}
        args_py = ', '.join(arg.to_python(env, 0) for arg in self.args)
        return f"{self.func_name}({args_py})"


class ClassDef(Node):
    def __init__(self, name: str, members: List[Node]):
        self.name = name
        self.members = members  

    def to_python(self, env=None, indent=0):
        env = env or {}
        indent_str = ' ' * (4 * indent)
        lines = [f"{indent_str}class {self.name}:"]

      
        init_assigns: List[str] = []
        methods_py: List[str] = []

        # collect var/array declarations and methods separately
        for m in self.members:
            if isinstance(m, (VarDecl, ArrayDecl)):
              
                decl_code = m.to_python(env, 0).strip()
                if '=' in decl_code:
                    lhs, rhs = map(str.strip, decl_code.split('=', 1))
                    init_assigns.append(' ' * (4 * (indent + 2)) + f"self.{lhs} = {rhs}")
                else:
                   
                    init_assigns.append(' ' * (4 * (indent + 2)) + f"self.{decl_code}")
            elif isinstance(m, FuncDef):
              
                params = list(m.params)
                if not params or params[0] != 'self':
                    params = ['self'] + params
                param_str = ', '.join(params)
                method_header = ' ' * (4 * (indent + 1)) + f"def {m.name}({param_str}):"
                body_py = m.body.to_python(env, indent + 2)
                if not body_py.strip():
                    body_py = ' ' * (4 * (indent + 2)) + 'pass'
                methods_py.append(method_header)
                methods_py.append(body_py)
            else:
               
                other_py = m.to_python(env, indent + 1)
                if other_py.strip():
                    methods_py.append(other_py)

        # create __init__ if we have any instance vars
        if init_assigns:
            lines.append(' ' * (4 * (indent + 1)) + "def __init__(self):")
            lines.extend(init_assigns)
            # ensure at least one line in __init__
            if not init_assigns:
                lines.append(' ' * (4 * (indent + 2)) + 'pass')

        # append methods / other members
        if methods_py:
            lines.extend(methods_py)

        if not init_assigns and not methods_py:
            lines.append(' ' * (4 * (indent + 1)) + 'pass')

        return '\n'.join(lines)
