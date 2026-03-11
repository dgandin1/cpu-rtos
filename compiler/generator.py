# A simplified RISC-V code generator for my parse.
# This is in no way optimized, and for now I am just
# focusing on making it work.

from parser import Node, VarDecl, If, Binary, Literal, Variable, ExprStmt, Assign, Block
from lexer import TokenType

class CodeGenerator:

    def __init__(self, tree, stack_base_addr, global_base_addr):
        self.tree = tree
        self.global_variables = {}
        self.stack_variables = {}
        self.symbols = {}
        self.stack_offset = stack_base_addr
        self.global_offset = global_base_addr
        self.current = 0
        self.code = []

    def emit(self, line):

        self.code.append(line)

    def generate_code(self):
        self.globals()
        self.generate_block(self.tree[self.current:])
        return self.code

    def globals(self):

        while isinstance(self.tree[self.current], VarDecl):

            self.emit("LW x0 #" + str(self.tree[self.current].initializer.value))
            self.emit("SW x0 #" + str(self.global_offset))
            self.global_offset += 4
            self.global_variables[self.tree[self.current].name] = self.global_offset - 4
            self.current += 1
        
    def get_var_address(self, var):

        if var in self.global_variables:
            return self.global_offset + self.global_variables[var]
        elif var in self.stack_variables:
            return self.stack_offset + self.stack_variables[var]
        raise Exception("Variable " + var + " not declared in scope.")
    
    def generate_binary(self, node, used_registers):

        result_register = "x1"
        if isinstance(node, Literal):
            self.emit(f"ADDI x12 x0 #{node.value}")
            self.emit(f"LW {result_register} x12")
            
        elif isinstance(node, Variable):
            addr = self.get_var_address(node.name)
            self.emit(f"LW {result_register} {addr}")
            
        elif isinstance(node, Binary):
            left_reg = self.generate_expr(node.left)
            right_reg = self.generate_expr(node.right)

            if node.operator.type == TokenType.PLUS:
                self.emit(f"ADD {result_register} {left_reg} {right_reg}")
            elif node.operator.type == TokenType.MINUS:
                self.emit(f"SUB {result_register} {left_reg} {right_reg}")
            else:
                raise Exception("Invalid Operator")
            
        else:
            raise Exception("Unsupported Expression Type") 
        
        return result_register

    def generate_if(self, stmt,used_registers):

        stack_base = self.stack_offset
        if_node:If = stmt
        self.current += 1
        condition:Binary = if_node.condition
        reg_left = self.generate_binary(condition.left, None)
        reg_right = self.generate_binary(condition.right, None)

        label_then = f"then_{self.current}"
        label_end = f"end_{self.current}"

        if condition.operator.type == TokenType.LT:
            self.emit(f"BGE {label_then}")
        elif condition.operator.type == TokenType.GT:
            self.emit(f"BLT #4 {label_then}")
        elif condition.operator.type == TokenType.EQEQ:
            self.emit(f"BEQ, #4 {label_then}")
        else:
            raise Exception("Unsupported operator")
        
        self.emit(f"J {label_end}")

        self.emit(f"{label_then}:")
        self.generate_block(if_node.then_branch.statements)

        self.emit(f"{label_end}:")

    def generate_block(self, statements):

        for stmt in statements:

            if isinstance(stmt, If):
                self.generate_if(stmt, None)
            elif isinstance(stmt, ExprStmt):
                self.generate_expr(stmt)
            elif (isinstance(stmt, VarDecl)):
                self.generate_var_decl(stmt)
    
    def generate_expr(self, stmt):

        if isinstance(stmt, Literal):
            return self.generate_binary(stmt, None)
        elif isinstance(stmt, Variable):
            return self.generate_binary(stmt, None)
        elif isinstance(stmt, Binary):
            return self.generate_binary(stmt, None)
        elif isinstance(stmt.expr, Assign):
            self.generate_assign(stmt.expr)
        else:
            print(stmt)
            raise Exception("Unsupported expression type")

    def generate_assign(self, stmt:VarDecl):

        if stmt.name in self.global_variables or stmt.name in self.stack_variables:
            reg_right = self.generate_binary(stmt.value, None)
            addr = self.get_var_address(stmt.name)
            self.emit(f"SW {addr} {reg_right}")
        else:
            raise Exception(f"Variable {stmt.name} not declared in scope.")
        
    def generate_var_decl(self, stmt:Assign):
        
        reg_right = self.generate_binary(stmt.initializer, None)
	
        self.emit(f"SW {reg_right} #" + str(self.stack_offset))
        self.stack_offset += 4
        self.stack_variables[stmt.name] = self.stack_offset - 4
