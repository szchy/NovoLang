import sys
try:
    from .auto_api import AutoAPI
except ImportError:
    from auto_api import AutoAPI

class Scope:
    def __init__(self, parent=None):
        self.variables = {}
        self.parent = parent

    def define(self, name, value):
        self.variables[name] = value

    def assign(self, name, value):
        if name in self.variables:
            self.variables[name] = value
        elif self.parent:
            self.parent.assign(name, value)
        else:
            raise RuntimeError(f"Error: Variable '{name}' not defined")

    def get(self, name):
        if name in self.variables:
            return self.variables[name]
        elif self.parent:
            return self.parent.get(name)
        else:
            raise RuntimeError(f"Error: Variable '{name}' not defined")

    def exists_local(self, name):
        return name in self.variables

class PyExecutor:
    def __init__(self):
        self.global_scope = Scope()
        self.current_scope = self.global_scope
        self.auto_api = AutoAPI()

    def execute(self, ast):
        if ast['type'] == 'BLOCK':
            self.exec_block(ast['statements'])

    def exec_block(self, stmts):
        for stmt in stmts:
            self.exec_stmt(stmt)

    def exec_stmt(self, stmt):
        type_ = stmt['type']
        if type_ == 'IF':
            self.exec_if(stmt)
        elif type_ == 'LOOP':
            self.exec_loop(stmt)
        elif type_ == 'PRINT':
            self.exec_print(stmt)
        elif type_ == 'ASSIGNMENT':
            self.exec_assign(stmt)
        elif type_ == 'AUTO_CALL':
            self.exec_auto(stmt)
        elif type_ == 'BLOCK':
            # Create new scope
            old_scope = self.current_scope
            self.current_scope = Scope(old_scope)
            self.exec_block(stmt['statements'])
            self.current_scope = old_scope

    def exec_if(self, stmt):
        cond = self.eval_expr(stmt['condition'])
        if cond:
            old_scope = self.current_scope
            self.current_scope = Scope(old_scope)
            
            body = stmt['body']
            if isinstance(body, list): # It's a list of stmts from parser block
                self.exec_block(body)
            elif body['type'] == 'BLOCK':
                 self.exec_block(body['statements'])
            else:
                 self.exec_stmt(body)
            
            self.current_scope = old_scope
        elif stmt.get('else_body'):
            old_scope = self.current_scope
            self.current_scope = Scope(old_scope)
            
            else_body = stmt['else_body']
            if isinstance(else_body, list):
                self.exec_block(else_body)
            elif else_body['type'] == 'BLOCK':
                 self.exec_block(else_body['statements'])
            else:
                 self.exec_stmt(else_body)
                 
            self.current_scope = old_scope

    def exec_loop(self, stmt):
        while True:
            cond = self.eval_expr(stmt['condition'])
            if not cond:
                break
            
            old_scope = self.current_scope
            self.current_scope = Scope(old_scope)
            
            body = stmt['body']
            if isinstance(body, list):
                self.exec_block(body)
            elif body['type'] == 'BLOCK':
                 self.exec_block(body['statements'])
            else:
                 self.exec_stmt(body)
            
            self.current_scope = old_scope

    def exec_print(self, stmt):
        val = self.eval_expr(stmt['expr'])
        # Handle boolean/null print formatting to match C++ spec
        if val is True:
            print("真")
        elif val is False:
            print("假")
        elif val is None:
            print("空")
        else:
            print(val)

    def exec_assign(self, stmt):
        name = stmt['target']
        val = self.eval_expr(stmt['value'])
        
        # Check if exists in any scope (assign), otherwise define in current
        try:
            self.current_scope.assign(name, val)
        except RuntimeError:
            self.current_scope.define(name, val)

    def exec_auto(self, stmt):
        func_name = stmt['function']
        args = [self.eval_expr(arg) for arg in stmt['args']]
        self.auto_api.execute(func_name, args)

    def eval_expr(self, expr):
        type_ = expr['type']
        if type_ == 'NUMBER':
            return expr['value']
        elif type_ == 'STRING':
            return expr['value']
        elif type_ == 'BOOL':
            return expr['value']
        elif type_ == 'NULL':
            return None
        elif type_ == 'IDENTIFIER':
            return self.current_scope.get(expr['name'])
        elif type_ == 'BINARY_OP':
            return self.eval_bin_op(expr)
        return None

    def eval_bin_op(self, expr):
        left = self.eval_expr(expr['left'])
        right = self.eval_expr(expr['right'])
        op = expr['op']
        
        if op == '+': 
            # String concatenation if either is string
            if isinstance(left, str) or isinstance(right, str):
                # Handle None/True/False string conversion if needed, 
                # but str() handles them (None->'None', True->'True')
                # For numbers, 10.0 -> '10.0'. 
                # If we want integer-like display:
                if isinstance(left, float) and left.is_integer():
                    left = int(left)
                if isinstance(right, float) and right.is_integer():
                    right = int(right)
                return str(left) + str(right)
            return left + right
        if op == '-': return left - right
        if op == '*': return left * right
        if op == '/': return left / right if right != 0 else 0
        if op == '>': return left > right
        if op == '<': return left < right
        if op == '>=': return left >= right
        if op == '<=': return left <= right
        if op == '==': return left == right
        if op == '!=': return left != right
        if op == '<>': return left != right
        
        return None
