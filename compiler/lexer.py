from enum import Enum, auto



class TokenType(Enum):

    INT = auto()
    IF = auto()
    WHILE = auto()
    RETURN = auto()
    ELSE = auto()
    
    # Identifiers and numbers
    IDENT = auto()
    NUMBER = auto()
    STRUCT = auto()
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    MUL = auto()
    DIV = auto()
    ASSIGN = auto()
    EQEQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()
    
    # Punctuation
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    SEMI = auto()
    
    EOF = auto()
    ERROR = auto()

    VOID = auto()
    COMMA = auto()

KEYWORDS = {
        "if": TokenType.IF,
        "while": TokenType.WHILE,
        "return": TokenType.RETURN,
        "else": TokenType.ELSE,
        "int": TokenType.INT,
        "struct": TokenType.STRUCT,
        "void": TokenType.VOID,
        "return": TokenType.RETURN
    }

class Token:

    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value
    
    def __repr__(self):
        if self.value is not None:
            return f"{self.type.name}:{self.value}"
        return f"{self.type.name}"
    
class Lexer:

    def __init__(self, text_):
        
        self.text = text_
        self.currentChar = 0
        self.start = 0
    
    #Returns the current character and advances it by one
    def advance(self):

        if self.currentChar >= len(self.text):
            return "\0"   # EOF marker
        ch = self.text[self.currentChar]
        self.currentChar += 1
        return ch
    
    #Returns the current character
    def peek(self):

        if self.currentChar >= len(self.text):
            return "\0"
        return self.text[self.currentChar]
    
    def number(self):

        while self.peek().isdigit():
            self.advance()
    
        value_str = self.text[self.start:self.currentChar]
        value = int(value_str)
        return Token(TokenType.NUMBER, value)
    
    def identifier(self):
        # Need to check for `.` in case it is a struct declaration
        while self.peek().isalnum() or self.peek() == "." or self.peek() == "_":
            self.advance()
        value_str = self.text[self.start:self.currentChar]
        type_ = KEYWORDS.get(value_str, TokenType.IDENT)
        return Token(type_, value_str)
        
    def nextToken(self):

        self.start = self.currentChar

        c = self.advance()

        if (c == "\0"):
            return Token(TokenType.EOF)
        elif (c.isdigit()):
            return self.number()
        elif (c.isalpha()):
            return self.identifier()
        elif (c == '+'):
            return Token(TokenType.PLUS)
        elif (c == '-'):
            return Token(TokenType.MINUS)
        elif (c == '*'):
            return Token(TokenType.MUL)
        elif (c == '/'):
            return Token(TokenType.DIV)
        elif (c == '('):
            return Token(TokenType.LPAREN)
        elif (c == ')'):
            return Token(TokenType.RPAREN)
        elif (c == '<'):
            if self.peek() == '=':
                self.advance()
                return Token(TokenType.LTE)
            return Token(TokenType.LT)
        elif (c == '>'):
            if self.peek() == '=':
                self.advance()
                return Token(TokenType.GTE)
            return Token(TokenType.GT)
        elif (c == '{'):
            return Token(TokenType.LBRACE)
        elif (c == '}'):
            return Token(TokenType.RBRACE)
        elif (c == ';'):
            return Token(TokenType.SEMI)
        elif (c == '='):
            if self.peek() == '=':
                self.advance()
                return Token(TokenType.EQEQ)
            return Token(TokenType.ASSIGN)
        elif (c == '!'):
            if self.peek() == '=':
                self.advance()
                return Token(TokenType.NEQ)
        if c.isspace():
            self.start = self.currentChar
            return self.nextToken()
        elif (c == ','):
            return Token(TokenType.COMMA)
        return Token(TokenType.ERROR)
    
    # Tokenize the current text contained in the Lexer. Returns a list of Tokens.
    def tokenize(self):

        tokens = []
        while self.currentChar < len(self.text):
            tokens.append(self.nextToken())
        return tokens
        




