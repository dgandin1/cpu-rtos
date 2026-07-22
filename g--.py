# End-To-End compiler for C-

import sys

from enum import Enum, auto

def rtb(register):

    num = bin(int(register[1:]))[2:]
    i = len(num)
    while i < 5:
        num = '0' + num
        i+=1
    return num

def imm12tb(imm):

    imm_clean = imm.replace(",", "")
    val = int(imm_clean)
    
    # Handle two's complement for negative immediates safely
    if val < 0:
        val = (1 << 12) + val
        
    num = bin(val)[2:]
    return num.zfill(12)


def assemble(output_file, lines):

    output = []

    for line in lines:
        # 1. Strip whitespace and remove comments
        clean_line = line.strip()
        
        # Skip if the line is completely blank or just a comment
        if not clean_line or clean_line.startswith("//"):
            continue

        line = line.lower().split()
        line_o = ""
        
        if line[0] == "add":
            line_o = "0000000" + rtb(line[3]) + rtb(line[2]) + "000" + rtb(line[1]) + "0110011"
        elif line[0] == "sub":
            line_o = "0100000" + rtb(line[3]) + rtb(line[2]) + "000" + rtb(line[1]) + "0110011"
        elif line[0] == "sll": # Added your 1-bit software shift!
            line_o = "0000000" + rtb(line[3]) + rtb(line[2]) + "001" + rtb(line[1]) + "0110011"
        elif line[0] == "srl": 
            line_o = "0000000" + rtb(line[3]) + rtb(line[2]) + "101" + rtb(line[1]) + "0110011"
        elif line[0] == "or":
            line_o = "0000000" + rtb(line[3]) + rtb(line[2]) + "110" + rtb(line[1]) + "0110011"
        elif line[0] == "and":
            line_o = "0000000" + rtb(line[3]) + rtb(line[2]) + "111" + rtb(line[1]) + "0110011"
        elif line[0] == "addi":
            line_o = imm12tb(line[3]) + rtb(line[2]) + "000" + rtb(line[1]) + "0010011"
        elif line[0] == "lw":
            print(imm12tb(line[3]))
            #Modified (not offset() syntax)
            line_o = imm12tb(line[3]) + rtb(line[2]) + "010" + rtb(line[1]) + "0000011"
        elif line[0] == "sw":
            #Modified, changed encoding to match lw
            line_o = imm12tb(line[3]) + rtb(line[2]) + "010" + rtb(line[1]) + "0100011"
        elif line[0] == "beq":
            # Syntax: beq rs1 rs2 offset
            # Maps to your CPU decoder: imm12 (offset) + rs2 + rs1 + funct3 (000) + opcode (1100011)
            # Syntax: beq rs1 rs2 offset
            # Your decoder expects:
            # IMM = INST[31:20] -> 12 bits
            # SA  = INST[19:15] -> 5 bits
            # SB  = INST[11:7]  -> 5 bits
            
            imm_str = imm12tb(line[3]) # 12 bits
            sa_str  = rtb(line[1])     # 5 bits
            sb_str  = rtb(line[2])     # 5 bits
            
            # Bits [14:12] are 3'b000, Bits [6:0] are 7'b1100011
            # Total bits: 12 + 5 + 3 + 5 + 7 = 32 bits
            line_o = imm_str + sa_str + "000" + sb_str + "1100011"
        
        elif line[0] == "blt":

            imm_str = imm12tb(line[3]) # 12 bits
            sa_str  = rtb(line[1])     # 5 bits
            sb_str  = rtb(line[2])     # 5 bits

            line_o = imm_str + sa_str + "001" + sb_str + "1100011"

        hex_string = f"{int(line_o, 2):08x}"
        output.append(hex_string.upper() + "\n")

    with open(output_file, "w") as f:
        f.writelines(output)


class TokenType(Enum):

    INT = auto()
    IF = auto()
    WHILE = auto()
    RETURN = auto()
    ELSE = auto()
    LONG = auto()
    
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
    FUNCT = auto()

KEYWORDS = {
        "if": TokenType.IF,
        "while": TokenType.WHILE,
        "return": TokenType.RETURN,
        "else": TokenType.ELSE,
        "int": TokenType.INT,
        "struct": TokenType.STRUCT,
        "function": TokenType.FUNCT,
        "if": TokenType.LONG
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
        return Token(TokenType.ERROR)
    
    # Tokenize the current text contained in the Lexer. Returns a list of Tokens.
    def tokenize(self):

        tokens = []
        while self.currentChar < len(self.text):
            tokens.append(self.nextToken())
        return tokens
        

class Parser:

    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0
        self.structs = []

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
    
    def var_decl(self, type_):

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

    def expression(self):

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
            print(var_name)
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
        elif self.peek().type == TokenType.STRUCT:
            self.consume()
            return self.struct_stmt()
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
    def __init__(self, name, initializer, type_):
        self.name = name
        self.initializer = initializer
        self.type = type_

class Struct(Node):
    def __init__(self, name, declerations): 
        self.name = name
        self.declerations = declerations




class CodeGeneratorSimplified:

    def __init__(self, tree):
        
        self.tree = tree
        self.current_register = 1
        self.code = []
        self.current_line = 0

        self.variables_to_regs = {}

        self.free_registers = []
    
    def emit(self, line):

        self.code.append(line)
    
    def free_reg(self, reg):

        # Check against dictionary values (the register strings), not the keys (variable names)
        if reg and reg not in self.variables_to_regs.values():
            # Avoid duplicate additions to the free list
            if reg not in self.free_registers:
                self.free_registers.append(reg)
    
    def next_reg(self):

        if len(self.free_registers) > 0:
            
            return self.free_registers.pop()

        self.current_register += 1
        self.current_line += 1

        return f"r{self.current_register - 1}"
    
    
    def generate_code(self):
        
        self.generate_block(self.tree)
        return self.code
    
    def generate_block(self, statements):

        for stmt in statements:

            if isinstance(stmt, If):
                self.generate_if(stmt, None)
            elif isinstance(stmt, ExprStmt):
                self.generate_expr(stmt)
            elif (isinstance(stmt, VarDecl)):
                self.generate_var_decl(stmt)
            elif (isinstance(stmt, While)):
                self.generate_while(stmt)
    
    def generate_if(self, stmt):

        if_node:If = stmt
        condition:Binary = if_node.condition
        reg_left = self.generate_binary(condition.left)
        reg_right = self.generate_binary(condition.right)


        label_then = f"then_{self.current_line}"
        label_end = f"end_{self.current_line}"

        if condition.operator.type == TokenType.LT:
            self.emit(f"BLT {reg_left} {reg_right} {label_then}")
            self.emit(f"BEQ x0 x0 {label_end}")
        elif condition.operator.type == TokenType.GT:
            self.emit(f"BLT {reg_left} {reg_right} {label_then}")
            print("TokenType.GT (>): NOT IMPLEMENTED")
            self.emit(f"BGE {reg_left} {reg_right} {label_then}")
        elif condition.operator.type == TokenType.EQEQ:
            self.emit(f"BEQ {reg_left} {reg_right}  {label_then}")
            self.emit(f"BEQ x0 x0 {label_end}")
        elif condition.operator.type == TokenType.NEQ:
            self.emit(f"BEQ {reg_left} {reg_right} {label_end}")
        else:
            raise Exception("Unsupported operator")
        
        #self.emit(f"J {label_end}")

        self.emit(f"{label_then}:")
        self.generate_block(if_node.then_branch.statements)

        self.emit(f"{label_end}:")

        self.free_reg(reg_right)
        self.free_reg(reg_left)
    
    def generate_binary(self, node):

        
        if isinstance(node, Literal):
            result_register = self.next_reg()
            self.emit(f"ADDI {result_register} x0 {node.value}")
            
            
        elif isinstance(node, Variable):
            result_register = self.variables_to_regs.get(node.name)
            
        elif isinstance(node, Binary):
            result_register = self.next_reg()
            left_reg = self.generate_expr(node.left)
            right_reg = self.generate_expr(node.right)

            if node.operator.type == TokenType.PLUS:
                self.emit(f"ADD {result_register} {left_reg} {right_reg}")
            elif node.operator.type == TokenType.MINUS:
                self.emit(f"SUB {result_register} {left_reg} {right_reg}")
            elif node.operator.type == TokenType.MUL:
                temp_reg = self.next_reg()
                one_reg = self.next_reg()
                self.emit(f"ADDI {one_reg} {one_reg} 1")
                self.emit((f"SUB {result_register} {result_register} {result_register}"))
                self.emit((f"BEQ x2 x0 done"))
                self.emit(f"AND {temp_reg} {right_reg} {one_reg}")
                self.emit(f"{temp_reg} x0 skip add")
                self.emit(f"ADD {result_register} {result_register} {left_reg}")
                self.emit(f"SLL {left_reg} {left_reg} {one_reg}")
                self.emit(f"SRL {right_reg} {right_reg} {one_reg}")
                self.emit(f"BEQ x0 x0 loop")
            else:
                raise Exception("Invalid Operator")

            self.free_reg(left_reg)
            self.free_reg(right_reg)
            
        else:
            raise Exception("Unsupported Expression Type") 
        
        return result_register

    def generate_expr(self, stmt):

        if isinstance(stmt, Literal):
            return self.generate_binary(stmt)
        elif isinstance(stmt, Variable):
            return self.generate_binary(stmt)
        elif isinstance(stmt, Binary):
            return self.generate_binary(stmt)
        elif isinstance(stmt.expr, Assign):
            self.generate_assign(stmt.expr)
        else:
            print(stmt)
            raise Exception("Unsupported expression type")
    
    def generate_assign(self, stmt:Assign):

        if stmt.name in self.variables_to_regs:
            reg_right = self.generate_binary(stmt.value)
            reg_addr = self.variables_to_regs.get(stmt.name)
            self.emit(f"ADD {reg_addr} x0 {reg_right}")
            self.free_reg(reg_right)
        else:
            print(self.stack_variables)
            raise Exception(f"Variable {stmt.name} not declared in scope.")
    
    def generate_var_decl(self, stmt:VarDecl):

        target_reg = self.next_reg()
        self.variables_to_regs[stmt.name] = target_reg
        reg_right = self.generate_binary(stmt.initializer)
        self.emit(f"ADD {target_reg} x0 {reg_right}")
        self.free_reg(reg_right)
    
    def generate_while(self, stmt):
        
        condition = stmt.condition

        label_start = f"start_{self.current_line}"
        label_end = f"end_{self.current_line}"

        self.emit(f"{label_start}:")

        reg_left = self.generate_binary(condition.left)
        reg_right = self.generate_binary(condition.right)

        if condition.operator.type == TokenType.LT:
            self.emit(f"BLT {reg_left} {reg_right} 2")
            self.emit(f"BEQ x0 x0 {label_end}")
        elif condition.operator.type == TokenType.GT:
            print("NOT IMPLEMENTED")
            self.emit(f"BLT {reg_left} {reg_right} {label_end}")
        elif condition.operator.type == TokenType.EQEQ:
            self.emit(f"BEQ {reg_left} {reg_right} 2")
            self.emit(f"BEQ x0 x0 {label_end}")
        elif condition.operator.type == TokenType.NEQ:
            self.emit(f"BEQ {reg_left} {reg_right} {label_end}")
        else:
            raise Exception("Unsopported Operation in while loop")

        self.generate_block(stmt.body.statements)

        self.emit(f"BEQ x0 x0 {label_start}")
        self.emit(f"{label_end}:")

        self.free_reg(reg_left)
        self.free_reg(reg_right)
    
class Linker:

    def __init__(self, assembly):
        # Clean up the initial list to remove empty strings and raw newlines
        self.assembly = [line.strip() for line in assembly if line.strip() != ""]
    
    def replace_labels(self):
        locations = {}

        # --- PASS 1: Find pure label positions ---
        instruction_idx = 0
        for line in self.assembly:
            if line.startswith("//"):
                continue

            # If the line ends with a colon, it's a declaration line (e.g., "start_7:")
            if line.endswith(":"):
                clean_label = line.replace(":", "").strip()
                locations[clean_label] = instruction_idx
            else:
                # Only increment for real instructions
                instruction_idx += 1
        
        # --- PASS 2: Filter out the declaration lines ---
        cleaned_assembly = []
        for line in self.assembly:
            if line.endswith(":") and (line.startswith("start") or line.startswith("end")):
                continue
            cleaned_assembly.append(line)
        self.assembly = cleaned_assembly
        
        # --- PASS 3: Replace label targets with relative offsets ---
        for i in range(len(self.assembly)):
            line = self.assembly[i]
            if line.startswith("//"):
                continue

            # Split line into tokens to check if a label is sitting inside it
            tokens = line.split()
            for j in range(len(tokens)):
                token = tokens[j]
                # Check if this exact token matches any known label name
                if token in locations:
                    offset = locations[token] - i
                    tokens[j] = str(offset)
            
            # Reconstruct the line back together
            self.assembly[i] = " ".join(tokens)

        return self.assembly



file_name = sys.argv[1]
output_name = sys.argv[2]
optional_arg = "none"
if (len(sys.argv) > 3):
    optional_arg = sys.argv[3]

with open(file_name, "r") as inf:

    read_ = inf.read()

l = Lexer(read_)
p = l.tokenize()
r = Parser(p)
t = r.parse()
g = CodeGeneratorSimplified(t)
i = g.generate_code()
li = Linker(i)
final = li.replace_labels()

if optional_arg == "none":
    
    assemble(output_name, final)
else:
    with open(output_name, "w") as f:
        f.writelines(line + "\n" for line in final)
