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
        lines = [s.to_python(env, indent) for s in self.stmts if s]
        return '\n'.join(lines)

class Block(Node):
    def __init__(self, stmts):
        self.stmts = stmts

    def to_python(self, env=None, indent=0):
        env = env or {}
        lines = [s.to_python(env, indent) for s in self.stmts if s]
        return '\n'.join(lines)

# ------------------ Variables ------------------
class VarDecl(Node):
    def __init__(self, vtype, name, initializer=None):
        self.vtype = vtype
        self.name = name
        self.initializer = initializer

    def to_python(self, env=None, indent=0):
        env = env or {}
        env[self.name] = self.vtype
        indent_str = ' ' * (4 * indent)
        if self.initializer:
            value = self.initializer.to_python(env, 0)
            return f"{indent_str}{self.name} = {value}"
        default_map = {'int': '0', 'float': '0.0', 'double': '0.0',
                       'char': "''", 'string': "''", 'bool': 'False'}
        val = default_map.get(self.vtype, 'None')
        return f"{indent_str}{self.name} = {val}"

class ArrayDecl(Node):
    def __init__(self, name, size, vtype='int', initializer=None):
        self.name = name
        self.size = size
        self.vtype = vtype
        self.initializer = initializer

    def to_python(self, env=None, indent=0):
        env = env or {}
        env[self.name] = f"list[{self.vtype}]"
        indent_str = ' ' * (4*indent)
        if self.initializer:
            init = self.initializer.to_python(env,0)
            return f"{indent_str}{self.name} = {init}"
        default_map = {'int': '0', 'float': '0.0', 'double': '0.0',
                       'char': "''", 'string': "''", 'bool': 'False'}
        val = default_map.get(self.vtype,'None')
        return f"{indent_str}{self.name} = [{val}]*{self.size}"

class Assign(Node):
    def __init__(self, target, expr, op='='):
        self.target = target
        self.expr = expr
        self.op = op  # supports +=, -=, etc.

    def to_python(self, env=None, indent=0):
        indent_str = ' ' * (4 * indent)
        rhs = self.expr.to_python(env,0)
        return f"{indent_str}{self.target} {self.op} {rhs}"

# ------------------ Control Flow ------------------
class IfStmt(Node):
    def __init__(self, cond, then_block: Block, else_block: Optional[Block]=None):
        self.cond = cond
        self.then_block = then_block
        self.else_block = else_block

    def to_python(self, env=None, indent=0):
        env = env or {}
        indent_str = ' ' * (4*indent)
        cond_py = self.cond.to_python(env,0)
        then_py = self.then_block.to_python(env, indent+1)
        lines = [f"{indent_str}if {cond_py}:"]
        lines.append(then_py if then_py.strip() else ' '*(4*(indent+1))+'pass')
        if self.else_block:
            else_py = self.else_block.to_python(env, indent+1)
            lines.append(f"{indent_str}else:")
            lines.append(else_py if else_py.strip() else ' '*(4*(indent+1))+'pass')
        return '\n'.join(lines)

class WhileStmt(Node):
    def __init__(self, cond, body: Block):
        self.cond = cond
        self.body = body

    def to_python(self, env=None, indent=0):
        indent_str = ' '*(4*indent)
        cond_py = self.cond.to_python(env,0)
        body_py = self.body.to_python(env, indent+1)
        lines = [f"{indent_str}while {cond_py}:"]
        lines.append(body_py if body_py.strip() else ' '*(4*(indent+1))+'pass')
        return '\n'.join(lines)

class ForStmt(Node):
    def __init__(self, init_stmt, cond_expr, iter_stmt, body: Block):
        self.init_stmt = init_stmt
        self.cond_expr = cond_expr
        self.iter_stmt = iter_stmt
        self.body = body

    def to_python(self, env=None, indent=0):
        env = env or {}
        indent_str = ' '*(4*indent)
        # Handle simple C-style loops
        try:
            if isinstance(self.init_stmt, (VarDecl, Assign)):
                var = self.init_stmt.name if isinstance(self.init_stmt, VarDecl) else self.init_stmt.target
                start = self.init_stmt.initializer.to_python(env,0) if isinstance(self.init_stmt, VarDecl) else self.init_stmt.expr.to_python(env,0)
                env[var] = 'int'

                if isinstance(self.cond_expr, BinaryOp) and isinstance(self.cond_expr.left, Var) and self.cond_expr.left.name==var:
                    end = self.cond_expr.right.to_python(env,0)
                    step = '1'
                    if self.cond_expr.op == '<=': end = f"({end})+1"
                    # detect decrement
                    if isinstance(self.iter_stmt, UnaryOp) and self.iter_stmt.op=='--': step='-1'
                    # detect var += k
                    if isinstance(self.iter_stmt, Assign) and self.iter_stmt.op=='+=': step=self.iter_stmt.expr.to_python(env,0)
                    header = f"for {var} in range({start},{end}"
                    if step!='1': header += f", {step}"
                    header += "):"
                    body_py = self.body.to_python(env, indent+1)
                    if not body_py.strip(): body_py=' '*(4*(indent+1))+'pass'
                    return '\n'.join([indent_str+header, body_py])
        except Exception: pass
        # fallback: while loop
        init_code = self.init_stmt.to_python(env, indent) if self.init_stmt else ''
        cond_py = self.cond_expr.to_python(env,0) if self.cond_expr else 'True'
        body_py = self.body.to_python(env, indent+1)
        if self.iter_stmt:
            body_py += '\n' + ' '*(4*(indent+1)) + self.iter_stmt.to_python(env,0)
        return '\n'.join([init_code, f"{indent_str}while {cond_py}:", body_py])

# ------------------ I/O ------------------
class CoutStmt(Node):
    def __init__(self, outputs: List[Node]):
        self.outputs = outputs

    def to_python(self, env=None, indent=0):
        env=env or {}
        indent_str=' '*(4*indent)
        items=[o.to_python(env,0) for o in self.outputs if not isinstance(o,Endl)]
        return indent_str+'print('+', '.join(items)+')' if items else indent_str+'print()'

class CinStmt(Node):
    def __init__(self, targets: List[str]):
        self.targets = targets

    def to_python(self, env=None, indent=0):
        env=env or {}
        indent_str=' '*(4*indent)
        lines=[]
        for t in self.targets:
            typ=env.get(t,'')
            if typ=='int': lines.append(f"{indent_str}{t} = int(input())")
            elif typ in ('float','double'): lines.append(f"{indent_str}{t} = float(input())")
            elif typ in ('char','string'): lines.append(f"{indent_str}{t} = input()")
            elif typ=='bool': lines.append(f"{indent_str}{t} = input().lower() in ('1','true','yes')")
            else: lines.append(f"{indent_str}{t} = input()")
        return '\n'.join(lines)

class Endl(Node):
    def to_python(self, env=None, indent=0):
        return ''

# ------------------ Expressions ------------------
class Expr(Node): pass

class Var(Expr):
    def __init__(self,name): self.name=name
    def to_python(self, env=None, indent=0): return self.name

class Literal(Expr):
    def __init__(self,value): self.value=value
    def to_python(self, env=None, indent=0):
        if isinstance(self.value,str): return self.value
        elif isinstance(self.value,bool): return 'True' if self.value else 'False'
        return repr(self.value)

class BinaryOp(Expr):
    def __init__(self,left:Expr, op:str, right:Expr): self.left,self.op,self.right=left,op,right
    def to_python(self, env=None, indent=0):
        left=self.left.to_python(env,0)
        right=self.right.to_python(env,0)
        op=self.op
        if op=='&&': op='and'
        elif op=='||': op='or'
        return f"({left} {op} {right})"

class UnaryOp(Expr):
    def __init__(self, op, operand): self.op,self.operand=op,operand
    def to_python(self, env=None, indent=0):
        if self.op=='++': return f"{self.operand.to_python(env,0)} + 1"
        if self.op=='--': return f"{self.operand.to_python(env,0)} - 1"
        if self.op=='-': return f"-{self.operand.to_python(env,0)}"
        if self.op=='!': return f"not {self.operand.to_python(env,0)}"
        return f"{self.op}{self.operand.to_python(env,0)}"

# ------------------ Additional Statements ------------------
class ReturnStmt(Node):
    def __init__(self, expr=None): self.expr=expr
    def to_python(self, env=None, indent=0): return ''

class BreakStmt(Node):
    def to_python(self, env=None, indent=0): return ' '*(4*indent)+'break'

class ContinueStmt(Node):
    def to_python(self, env=None, indent=0): return ' '*(4*indent)+'continue'

class TernaryOp(Expr):
    def __init__(self, cond, true_expr, false_expr):
        self.cond,self.true_expr,self.false_expr=cond,true_expr,false_expr
    def to_python(self, env=None, indent=0):
        return f"({self.true_expr.to_python(env,0)} if {self.cond.to_python(env,0)} else {self.false_expr.to_python(env,0)})"

class FuncDef(Node):
    def __init__(self, name, params: List[str], body: Block):
        self.name=name
        self.params=params
        self.body=body
    def to_python(self, env=None, indent=0):
        indent_str=' '*(4*indent)
        param_str=', '.join(self.params)
        body_py=self.body.to_python(env, indent+1)
        if not body_py.strip(): body_py=' '*(4*(indent+1))+'pass'
        return f"{indent_str}def {self.name}({param_str}):\n{body_py}"
