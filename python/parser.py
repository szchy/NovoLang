try:
    from .lexer import Lexer
    from .ast_builder import ASTBuilder
except ImportError:
    from lexer import Lexer
    from ast_builder import ASTBuilder
import sys

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[0] if self.tokens else None

    def eat(self, type):
        if self.current_token and self.current_token.type == type:
            self.advance()
        else:
            self.error(f"Expected token {type}, got {self.current_token.type if self.current_token else 'EOF'}")

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None

    def error(self, msg):
        line = self.current_token.line if self.current_token else "EOF"
        print(f"Syntax Error at line {line}: {msg}")
        sys.exit(1)

    def parse(self):
        statements = []
        while self.current_token:
            statements.append(self.statement())
        return ASTBuilder.block(statements)

    def statement(self):
        if self.current_token.type == 'IF':
            return self.if_statement()
        elif self.current_token.type == 'LOOP':
            return self.loop_statement()
        elif self.current_token.type == 'PRINT':
            return self.print_statement()
        elif self.current_token.type == 'DEF':
            return self.def_statement()
        elif self.current_token.type == 'AUTO':
            return self.auto_statement()
        elif self.current_token.type == 'ID':
            # Could be assignment or function call (if we had them as stmt)
            # Check lookahead
            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].value == '=':
                return self.assign_statement()
            else:
                 self.error(f"Unexpected identifier {self.current_token.value}")
        else:
            self.error(f"Unexpected token {self.current_token.type}")

    def if_statement(self):
        self.eat('IF')
        condition = self.expr()
        
        # Expect block
        body = self.block()
        else_body = None
        
        if self.current_token and self.current_token.type == 'ELSE':
            self.eat('ELSE')
            else_body = self.block()
            
        return ASTBuilder.if_stmt(condition, body, else_body)

    def loop_statement(self):
        self.eat('LOOP')
        self.eat('PUNCT') # (
        
        # Check if it's a for-loop (init; cond; step) or while-loop (cond)
        is_for_loop = False
        if self.current_token.type == 'ID':
            # Lookahead for assignment '='
            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].value == '=':
                is_for_loop = True
        
        if is_for_loop:
            # Parse init: i = 0
            init_stmt = self.assign_statement()
            self.eat('PUNCT') # ; (Expect semicolon)
            
            # Parse condition: i < 3
            condition = self.expr()
            self.eat('PUNCT') # ;
            
            # Parse step: i = i + 1
            step_stmt = self.assign_statement()
            self.eat('PUNCT') # )
            
            # Parse body
            body = self.block()
            
            # Construct equivalent while loop:
            # {
            #   init;
            #   while(cond) {
            #     body...
            #     step;
            #   }
            # }
            
            # Ensure body is a list
            body_stmts = body if isinstance(body, list) else [body]
            # Append step to body
            body_stmts.append(step_stmt)
            
            loop_node = ASTBuilder.loop_stmt(condition, body_stmts)
            
            # Wrap init and loop in a block to scope the loop var (if we had block scope)
            # or just to execute sequentially
            return ASTBuilder.block([init_stmt, loop_node])
            
        else:
            # Standard while loop: while (condition)
            condition = self.expr()
            self.eat('PUNCT') # ) (Close paren for condition)
            body = self.block()
            return ASTBuilder.loop_stmt(condition, body)

    def print_statement(self):
        self.eat('PRINT')
        val = self.expr()
        return ASTBuilder.print_stmt(val)

    def def_statement(self):
        self.eat('DEF')
        var_name = self.current_token.value
        self.eat('ID')
        self.eat('OP') # Expect '='
        val = self.expr()
        return ASTBuilder.assignment(var_name, val)

    def assign_statement(self):
        var_name = self.current_token.value
        self.eat('ID')
        self.eat('OP') # Expect '='
        val = self.expr()
        return ASTBuilder.assignment(var_name, val)

    def auto_statement(self):
        self.eat('AUTO')
        func_name = self.current_token.value
        self.eat('ID')
        self.eat('PUNCT') # (
        args = []
        if self.current_token.type != 'PUNCT' or self.current_token.value != ')':
            args.append(self.expr())
            while self.current_token.type == 'PUNCT' and self.current_token.value == ',':
                self.eat('PUNCT')
                args.append(self.expr())
        self.eat('PUNCT') # )
        return ASTBuilder.auto_call(func_name, args)

    def block(self):
        if self.current_token.value == '{':
            self.eat('PUNCT')
            stmts = []
            while self.current_token.value != '}':
                stmts.append(self.statement())
            self.eat('PUNCT')
            return stmts
        else:
            # Allow single statement without braces
            return [self.statement()]

    def expr(self):
        # Simple expression parser handling + -
        node = self.term()
        
        while self.current_token and self.current_token.type == 'OP' and self.current_token.value in ('+', '-'):
            op = self.current_token.value
            self.eat('OP')
            node = ASTBuilder.binary_op(node, op, self.term())
            
        # Handle comparisons
        if self.current_token and self.current_token.type == 'OP' and self.current_token.value in ('<', '>', '<=', '>=', '==', '!=', '<>'):
            op = self.current_token.value
            self.eat('OP')
            node = ASTBuilder.binary_op(node, op, self.expr()) # Recursive for chain? Or just next term
            
        return node

    def term(self):
        # * /
        node = self.factor()
        while self.current_token and self.current_token.type == 'OP' and self.current_token.value in ('*', '/'):
            op = self.current_token.value
            self.eat('OP')
            node = ASTBuilder.binary_op(node, op, self.factor())
        return node

    def factor(self):
        token = self.current_token
        if token.type == 'NUMBER':
            self.eat('NUMBER')
            return ASTBuilder.number(token.value)
        elif token.type == 'STRING':
            self.eat('STRING')
            return ASTBuilder.string(token.value)
        elif token.type == 'ID':
            self.eat('ID')
            return ASTBuilder.identifier(token.value)
        elif token.type == 'TRUE':
            self.eat('TRUE')
            return ASTBuilder.boolean(True)
        elif token.type == 'FALSE':
            self.eat('FALSE')
            return ASTBuilder.boolean(False)
        elif token.type == 'NULL':
            self.eat('NULL')
            return ASTBuilder.null()
        elif token.type == 'PUNCT' and token.value == '(':
            self.eat('PUNCT')
            node = self.expr()
            self.eat('PUNCT') # )
            return node
        else:
            self.error(f"Unexpected token in expression: {token}")

