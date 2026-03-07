#A simple recursive descent parser for a subset of C (C-).

from lexer import TokenType

class Parser:

    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def previous(self):

        return self.tokens[self.current - 1]

    def peek(self):

        return self.tokens[self.current]

    def consume(self):
        
        self.current += 1
        return self.tokens[self.current - 1]
    
    def is_at_end(self):

        return self.tokens[self.current].type == TokenType.EOF
    

    def consume_and_check(self, token_type, message):

        if self.is_at_end() or self.peek().type != token_type:
            raise Exception("Exception: " + message)

        return self.consume()

    def if_stmt(self):

        self.consume_and_check(TokenType.LPAREN, "Expected LPAREN")
        condition = self.expression()
        self.consume_and_check(TokenType.RPAREN, "Expected RPARAN")
        then_branch = self.statement()
        else_branch = None
        if self.peek().type == TokenType.ELSE:
            self.consume()
            else_branch = self.statement()
        
        return If(condition, then_branch, else_branch)
    
    def var_decl(self):

        name_token = self.consume_and_check(TokenType.IDENT, "Expected variable name")
        var_name = name_token.value

        initializer = None

        if self.peek().type == TokenType.ASSIGN:
            self.consume()
            initializer = self.expression()

        self.consume_and_check(TokenType.SEMI, "Expected semicolon")

        return VarDecl(var_name, initializer)

    def while_stmt(self):

        self.consume_and_check(TokenType.LPAREN, "Expected LPAREN")
        condition = self.expression()
        self.consume_and_check(TokenType.RPAREN, "Expected RPARAN")
        body = self.statement()
        return While(condition, body)

    def expression(self):

        return self.assignment()

    def expr_stmt(self):
        expr = self.expression()
        self.consume_and_check(TokenType.SEMI, "Expected semicolon")
        return ExprStmt(expr)

    def statement(self):

        if self.peek().type == TokenType.IF:
            self.consume()
            return self.if_stmt()
        elif self.peek().type == TokenType.WHILE:
            self.consume()
            return self.while_stmt()
        elif self.peek().type == TokenType.LBRACE:
            self.consume()
            return self.block()
        elif self.peek().type == TokenType.INT:
            self.consume()
            return self.var_decl()
        return self.expr_stmt()
    
    def block(self):

        statements = []
        while not self.peek().type == TokenType.RBRACE and not self.is_at_end():
            statements.append(self.statement())
        self.consume_and_check(TokenType.RBRACE, "Expected right brace.")
        return Block(statements)
    
    
    def assignment(self):
        expr = self.equality()

        if self.peek().type == TokenType.ASSIGN:
            equals = self.consume()
            value = self.assignment()

            if isinstance(expr, Variable):
                return Assign(expr.name, value)

            raise Exception("Invalid assignment target.")

        return expr
    
    def equality(self):
        expr = self.comparison()

        while self.peek().type == TokenType.EQEQ:
            operator = self.consume()
            right = self.comparison()
            expr = Binary(expr, operator, right)

        return expr
    
    def comparison(self):
        expr = self.term()

        while self.peek().type in (
            TokenType.GT,
            TokenType.LT,
            TokenType.LTE,
            TokenType.GTE,
        ):
            operator = self.consume()
            right = self.term()
            expr = Binary(expr, operator, right)

        return expr
    
    def term(self):
        expr = self.factor()

        while self.peek().type == TokenType.PLUS or self.peek().type == TokenType.MINUS:
            operator = self.consume()
            right = self.factor()
            expr = Binary(expr, operator, right)

        return expr
    
    def factor(self):
        expr = self.unary()

        while self.peek().type == TokenType.MUL or self.peek().type == TokenType.DIV:
            operator = self.consume()
            right = self.unary()
            expr = Binary(expr, operator, right)

        return expr
    
    def unary(self):
        if self.peek().type == TokenType.MINUS:
            operator = self.consume()
            right = self.unary()
            return Unary(operator, right)

        return self.primary()
    
    def primary(self):
        if self.peek().type == TokenType.NUMBER:
            token = self.consume()
            return Literal(token.value)

        if self.peek().type == TokenType.IDENT:
            token = self.consume()
            return Variable(token.value)

        if self.peek().type == TokenType.LPAREN:
            self.consume()
            expr = self.expression()
            self.consume_and_check(TokenType.RPAREN, "Expected RPAREN")
            return expr

        raise Exception("Expected expression.")
    
    def parse(self):

        statements = []
        while not self.is_at_end():
            statements.append(self.statement())
        
        return statements
    

class Node:
    def __repr__(self):
        fields = ", ".join(
            f"{k}={v!r}" for k, v in self.__dict__.items()
        )
        return f"{self.__class__.__name__}({fields})"


# === Statements ===

class Block(Node):
    def __init__(self, statements):
        self.statements = statements


class If(Node):
    def __init__(self, condition, then_branch, else_branch):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch


class While(Node):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class ExprStmt(Node):
    def __init__(self, expr):
        self.expr = expr


# === Expressions ===

class Assign(Node):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class Binary(Node):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right


class Unary(Node):
    def __init__(self, operator, operand):
        self.operator = operator
        self.operand = operand


class Literal(Node):
    def __init__(self, value):
        self.value = value


class Variable(Node):
    def __init__(self, name):
        self.name = name

class VarDecl(Node):
    def __init__(self, name, initializer):
        self.name = name
        self.initializer = initializer