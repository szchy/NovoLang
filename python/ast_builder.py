class ASTBuilder:
    @staticmethod
    def number(value):
        return {"type": "NUMBER", "value": float(value)}

    @staticmethod
    def string(value):
        return {"type": "STRING", "value": value}

    @staticmethod
    def boolean(value):
        return {"type": "BOOL", "value": value}

    @staticmethod
    def null():
        return {"type": "NULL"}

    @staticmethod
    def identifier(name):
        return {"type": "IDENTIFIER", "name": name}

    @staticmethod
    def binary_op(left, op, right):
        return {
            "type": "BINARY_OP",
            "left": left,
            "op": op,
            "right": right
        }

    @staticmethod
    def assignment(target, value):
        return {
            "type": "ASSIGNMENT",
            "target": target,
            "value": value
        }

    @staticmethod
    def if_stmt(condition, body, else_body=None):
        return {
            "type": "IF",
            "condition": condition,
            "body": body,
            "else_body": else_body
        }

    @staticmethod
    def loop_stmt(condition, body):
        return {
            "type": "LOOP",
            "condition": condition,
            "body": body
        }

    @staticmethod
    def print_stmt(expr):
        return {
            "type": "PRINT",
            "expr": expr
        }
    
    @staticmethod
    def auto_call(name, args):
        return {
            "type": "AUTO_CALL",
            "function": name,
            "args": args
        }

    @staticmethod
    def block(statements):
        return {
            "type": "BLOCK",
            "statements": statements
        }
