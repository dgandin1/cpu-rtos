#A simple recursive descent parser for a subset of C (C-).
    
from lexer import TokenType

class Parser:

    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0
        self.structs = []

    def previous(self):

        return self.tokens[self.current - 1]

    def peek(self):

        return self.tokens[self.current]

    def peek2(self):

        return self.tokens[self.current + 1]

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
    
    def func_decl(self, type_):

        params = []

        name_token = self.consume_and_check(TokenType.IDENT, "Expected function name").value
        self.consume()

        while not self.peek().type == TokenType.RPAREN:
            param_type = self.consume()
            param_name = self.consume_and_check(TokenType.IDENT, "Expected param name").value
            params.append({"name":param_name, "type":param_type})

            if self.peek().type == TokenType.COMMA:
                self.consume()
            
        self.consume()
        body = self.statement()
        return Funct(name_token, type_, params, body)
            

    def var_decl(self, type_):

        if self.peek2().type == TokenType.LPAREN:
            return self.func_decl(type_)
            

        name_token = self.consume_and_check(TokenType.IDENT, "Expected variable name")
        var_name = name_token.value

        initializer = None

        if self.peek().type == TokenType.ASSIGN:
            self.consume()
            initializer = self.expression()
        

        self.consume_and_check(TokenType.SEMI, "Expected semicolon")

        return VarDecl(var_name, initializer, type_)

    def while_stmt(self):

        self.consume_and_check(TokenType.LPAREN, "Expected LPAREN")
        condition = self.expression()
        self.consume_and_check(TokenType.RPAREN, "Expected RPARAN")
        body = self.statement()
        return While(condition, body)
    
    def funct_call(self):
        
        params = []
        name = self.consume()
        self.consume() # (
        while not self.peek().type == TokenType.RPAREN:
           # name = self.consume_and_check(TokenType.IDENT, "expeted parameter to be an identifier")
            params.append(self.expression())
            if (self.peek().type == TokenType.COMMA):
                self.consume()
        self.consume() #)
        return FunctCall(name, params)
        

    def expression(self):
        
        if self.peek2().type == TokenType.LPAREN:
            return self.funct_call()

        return self.assignment()

    def expr_stmt(self):
        expr = self.expression()
        self.consume_and_check(TokenType.SEMI, "Expected semicolon")
        return ExprStmt(expr)

    def struct_stmt(self): 

        definitions = [] 
        
        name = self.consume_and_check(TokenType.IDENT, "Expected Struct Identifier")
        self.structs.append(name.value)
        if not self.peek().type == TokenType.LBRACE:
            var_name = self.consume()
            self.consume_and_check(TokenType.SEMI, "Expected semicolon")
            return VarDecl(var_name, None, name)

        self.consume_and_check(TokenType.LBRACE, "Expected LBRACE")

        while self.peek().type == TokenType.INT:

            self.consume()
            var_name = self.consume_and_check(TokenType.IDENT, "Expected identifier")
            definitions.append({"name":var_name.value, "type":TokenType.INT})
            self.consume_and_check(TokenType.SEMI, "Expected semicolon")
        
        self.consume_and_check(TokenType.RBRACE, "Expected RPAREN")
        return Struct(name.value, definitions)

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
            return self.var_decl(TokenType.INT)
        elif self.peek().type == TokenType.VOID:
            self.consume()
            return self.var_decl(TokenType.VOID)
        elif self.peek().type == TokenType.STRUCT:
            self.consume()
            return self.struct_stmt()
        elif self.peek().type == TokenType.RETURN:
            self.consume()
            expr = self.expr_stmt()
            return ReturnStmt(expr)
        # elif self.peek().value in self.structs:
        #     # deal with struct
        #     s_name = self.consume()
        #     name = self.consume()
        #     equals = self.consume()
        #     value = self.consume()
        #     self.consume_and_check(TokenType.SEMI, "expected semicolon")
        #     return VarDecl(name.value, Literal(value.value), s_name.value)
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

        while self.peek().type == TokenType.EQEQ or self.peek().type == TokenType.NEQ:
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
        if self.peek().type == TokenType.D_QUOTE:
            self.consume()
            literal_string = ""
            while self.peek().type == TokenType.IDENT or self.peek().type == TokenType.NUMBER or self.peek().type == TokenType.MINUS:
                if (self.peek().type == TokenType.MINUS):
                    self.consume()
                    literal_string += "-"
                else:
                    literal_string += str(self.consume().value) + " "
            self.consume_and_check(TokenType.D_QUOTE, "Need closing quotation")
            return Literal(literal_string[:-1])

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

class Funct(Node):
    def __init__(self, name, return_type, params, body):

        self.name = name
        self.return_type = return_type
        self.params = params
        self.body = body

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
    def __init__(self, name, initializer, type_):
        self.name = name
        self.initializer = initializer
        self.type = type_

class Struct(Node):
    def __init__(self, name, declerations): 
        self.name = name
        self.declerations = declerations

class FunctCall(Node):
    def __init__(self, name, params):
        self.name = name
        self.params = params

class ReturnStmt(Node):
    def __init__(self, expr):
        self.expr = expr
        