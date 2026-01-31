import re
import sys

class Token:
    def __init__(self, type, value, line):
        self.type = type
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {self.value}, {self.line})"

class Lexer:
    def __init__(self, code):
        self.code = code
        self.tokens = []
        self.pos = 0
        self.line = 1
        self.keywords = {
            # Chinese (Simplified)
            '如果': 'IF',
            '否则': 'ELSE',
            '循环': 'LOOP',
            '打印': 'PRINT',
            '定义': 'DEF',
            '返回': 'RETURN',
            '当': 'WHILE',
            '自动': 'AUTO',
            '真': 'TRUE',
            '假': 'FALSE',
            '空': 'NULL',
            
            # English
            'if': 'IF',
            'else': 'ELSE',
            'loop': 'LOOP',
            'for': 'LOOP',
            'print': 'PRINT',
            'def': 'DEF',
            'var': 'DEF',
            'return': 'RETURN',
            'while': 'WHILE',
            'auto': 'AUTO',
            'true': 'TRUE',
            'false': 'FALSE',
            'null': 'NULL',

            # Japanese
            'もし': 'IF',
            'その他': 'ELSE',
            '繰り返し': 'LOOP',
            '表示': 'PRINT',
            '定義': 'DEF',
            '戻る': 'RETURN',
            '間': 'WHILE',
            '自動': 'AUTO',
            '真': 'TRUE', # Same as Chinese often, but distinct in context
            '偽': 'FALSE',
            '無': 'NULL',

            # Korean
            '만약': 'IF',
            '아니면': 'ELSE',
            '반복': 'LOOP',
            '출력': 'PRINT',
            '정의': 'DEF',
            '반환': 'RETURN',
            '동안': 'WHILE',
            '자동': 'AUTO',
            '참': 'TRUE',
            '거짓': 'FALSE',
            '비어': 'NULL',

            # Russian
            'если': 'IF',
            'иначе': 'ELSE',
            'цикл': 'LOOP',
            'печать': 'PRINT',
            'определить': 'DEF',
            'вернуть': 'RETURN',
            'пока': 'WHILE',
            'авто': 'AUTO',
            'истина': 'TRUE',
            'ложь': 'FALSE',
            'ноль': 'NULL'
        }

    def tokenize(self):
        # Regex patterns
        token_spec = [
            ('COMMENT', r'//.*'),
            ('NUMBER',  r'\d+(\.\d+)?'),
            ('STRING',  r'"[^"]*"'),
            ('ID',      r'[a-zA-Z_\u4e00-\u9fa5][a-zA-Z0-9_\u4e00-\u9fa5]*'),
            ('OP',      r'==|!=|<>|>=|<=|>|<|=|\+|\-|\*|/'),
            ('PUNCT',   r'\(|\)|,|\{|\}|;'),
            ('NEWLINE', r'\n'),
            ('SKIP',    r'[ \t\r]+'),
            ('MISMATCH',r'.'),
        ]
        
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_spec)
        
        for mo in re.finditer(tok_regex, self.code):
            kind = mo.lastgroup
            value = mo.group()
            
            if kind == 'NEWLINE':
                self.line += 1
            elif kind == 'SKIP':
                pass
            elif kind == 'COMMENT':
                pass
            elif kind == 'ID':
                if value in self.keywords:
                    kind = self.keywords[value]
                self.tokens.append(Token(kind, value, self.line))
            elif kind == 'MISMATCH':
                # Simplified error handling as per requirements
                # In a real compiler, we might throw an error here or accumulate it
                print(f"Error: Unexpected character '{value}' at line {self.line}")
                sys.exit(1)
            else:
                if kind == 'STRING':
                    value = value[1:-1] # Remove quotes
                self.tokens.append(Token(kind, value, self.line))
                
        return self.tokens
