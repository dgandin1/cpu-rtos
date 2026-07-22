# A simplified RISC-V code generator for my parse.
# This is in no way optimized, and for now I am just
# focusing on making it work.

from parser import Node, VarDecl, If, Binary, Literal, Variable, ExprStmt, Assign, Block, While, Struct
from lexer import TokenType

sizeof = {
    TokenType.INT: 32
}

class CodeGenerator:
    pass
    def __init__(self, tree, global_base_addr, n):
        self.tree = tree
        self.global_variables = {}
        self.stack_variables = {}
        self.symbols = {}
        #  global base address is special register: x4
        self.stack_base = global_base_addr + n #grows down from highest address
        self.global_base = global_base_addr
        self.current = 0
        self.code = []
        self.global_offset = global_base_addr
        self.stack_offset = self.stack_base
        self.used_registers = []
        self.stack_sizes = [0] #this keeps track of the size of the current stack frame

        # Struct stuff (just a dictionary of dictionarites of the format: {struct_name: {name:, type:}...})
        self.structs = {}
        # A list of structs that are either in stack_variables or global variables
        self.declared_structs = []
        # List of previously declared struct keywords
        self.declared_keywords = []

    def emit(self, line):

        self.code.append(line)

    def generate_code(self):
        self.globals()
        self.generate_block(self.tree[self.current:])
        return self.code
    
    #Gets a scratch register, or NULL if none available
    def get_scratch_register(self):
        
        for i in range(18, 32):
            if i not in self.used_registers:
                self.used_registers.append(i)
                return "x" + str(i)
        return null;

    def free_scratch_register(self, reg):

        self.used_registers.remove(int(reg[1:]))

    def save_global(self, value, name, type_):
        
        self.emit(f"// Save global variable {name}")
        reg1 = self.get_scratch_register();
        reg2 = self.get_scratch_register();        
        if type_ == TokenType.INT:
            self.emit(f"ADDI {reg1} x0 #{value}") # add value (assembler deals with converting to binary and too large values
            self.emit(f"ADDI {reg2} x0 #{self.global_offset}")
            self.emit(f"SW {reg1} 0({reg2})")
            self.global_variables[name] = self.global_offset
            self.global_offset += 4
        self.free_scratch_register(reg1)
        self.free_scratch_register(reg2)

    def save_local(self, reg, name, type_):

        self.emit(f"// Save local (stack) variable {name}")
        reg1 = self.get_scratch_register();

        if type_ == TokenType.INT:
            self.emit(f"SUBI sp sp #4")
            self.emit(f"SW {reg} 0(sp)")
            self.stack_sizes[len(self.stack_sizes) - 1] += 1
            self.free_scratch_register(reg1)
            self.stack_sizes[len(self.stack_sizes) - 1] += 1
            self.stack_variables[name] = self.stack_sizes[len(self.stack_sizes) - 1]
    
    def add_struct_field(self, name):

        reg1 = self.get_scratch_register()
        self.emit(f"SUBI sp sp #4")
      #  self.emit(f"ADDI {reg1} x0 #0")
      #  self.emit(f"SW {reg1} 0(sp)")
        self.stack_sizes[len(self.stack_sizes) - 1] += 1
        self.stack_variables[name] = self.stack_sizes[len(self.stack_sizes) - 1]
        self.free_scratch_register(reg1)

    def save_malloc(self, value, name, type_):

        self.emit(f"// Save malloc variable")
        reg1 = self.get_scratch_register();
        reg2 = self.get_scratch_register();
        if type_ == TokenType.INT:
            self.emit(f"ADDI {reg1} x0 #{value}")
            self.emit(f"ADDI {reg2} x0 #{self.global_offset}")
            self.emit(f"SW {reg1} 0({reg2})")
                        
    #This method is run to save all global variables at the beginning of a file
    def globals(self):

        while isinstance(self.tree[self.current], VarDecl):
            self.save_global(self.tree[self.current].initializer.value, self.tree[self.current].name, self.tree[self.current].type)
            self.current += 1
        
    def get_var_address(self, var):

        if var in self.global_variables:
            return self.global_offset + self.global_variables[var]
        elif var in self.stack_variables:
            return self.stack_offset + self.stack_variables[var]
        raise Exception("Variable " + var + " not declared in scope.")
    
    def generate_binary(self, node, used_registers):

        result_register = self.get_scratch_register()
        if isinstance(node, Literal):
            self.emit(f"ADDI {result_register} x0 #{node.value}")
            
        elif isinstance(node, Variable):
            addr = self.get_var_address(node.name)
            s_reg = self.get_scratch_register()
            self.emit(f"ADDI {s_reg} x0 #{addr}")
            self.emit(f"LW {result_register} 0({s_reg})")
            self.free_scratch_register(s_reg)
            
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
            self.emit(f"BLT {reg_left} {reg_right} {label_then}")
        elif condition.operator.type == TokenType.GT:
            self.emit(f"BGE {reg_left} {reg_right} {label_then}")
        elif condition.operator.type == TokenType.EQEQ:
            self.emit(f"BEQ {reg_left} {reg_right}  {label_then}")
        else:
            raise Exception("Unsupported operator")
        
        self.emit(f"BEQ x0 x0 {label_end}")

        self.emit(f"{label_then}:")
        self.free_scratch_register(reg_left)
        self.free_scratch_register(reg_right)
        self.generate_block(if_node.then_branch.statements)

        self.emit(f"{label_end}:")

    def generate_while(self, stmt):
        
        condition = stmt.condition

        label_start = f"start_{self.current}"
        label_end = f"end_{self.current}"

        self.emit(f"{label_start}:")

        reg_left = self.generate_binary(condition.left, None)
        reg_right = self.generate_binary(condition.right, None)

        if condition.operator.type == TokenType.LT:
            self.emit(f"BGE {reg_left} {reg_right} {label_end}")
        elif condition.operator.type == TokenType.GT:
            self.emit(f"BLT {reg_left} {reg_right} {label_end}")
        elif condition.operator.type == TokenType.EQEQ:
            self.emit(f"BNE {reg_left} {reg_right} {label_end}")
        else:
            raise Exception("Unsopported Operation in while loop")

        self.free_scratch_register(reg_left)
        self.free_scratch_register(reg_right)

        self.generate_block(stmt.body.statements)

        self.emit(f"J {label_start}")
        self.emit(f"{label_end}:")


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
            elif isinstance(stmt, Struct):
                # declare self.structs[stmt.name]
                self.structs[stmt.name] = []
                # add struct keywords:
                for s in stmt.declerations:
                    self.structs[stmt.name].append({"name": s["name"], "type":s["type"]})

    
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

    def generate_assign(self, stmt:Assign):

        if stmt.name in self.global_variables or stmt.name in self.stack_variables:
            reg_right = self.generate_binary(stmt.value, None)
            addr = self.get_var_address(stmt.name)
            reg_addr = self.get_scratch_register()
            self.emit(f"// Generate assign for {stmt.name}")
            self.emit(f"ADDI {reg_addr} x0 #{addr}")
            self.emit(f"SW {reg_right} 0({reg_addr})")
            self.free_scratch_register(reg_addr)
            self.free_scratch_register(reg_right)
        else:
            print(self.stack_variables)
            raise Exception(f"Variable {stmt.name} not declared in scope.")
        
    def generate_var_decl(self, stmt:VarDecl):

        #check if it is a struct decleration
        if stmt.initializer == None:
            # This means it is a struct, since only struct initalizers are allowed to be null as of now
            if stmt.type.value in self.structs:
                
                self.declared_structs.append({"place":self.stack_sizes[len(self.stack_sizes) - 1], "name":stmt.name.value, "type":stmt.type.value})
                self.stack_sizes[len(self.stack_sizes)-1] += len(self.structs[stmt.type.value]) 
                self.emit("// Allocate memory for struct " + stmt.type.value + " " + stmt.name.value)
                
                # Add all the fields
                for decl in self.structs[stmt.type.value]:
                    
                    self.add_struct_field(f"{stmt.name.value}.{decl["name"]}")

                return
            else:
                raise Exception(f"No struct of type {stmt.type.value} declared.")
        
        reg_right = self.generate_binary(stmt.initializer, None)
        self.save_local(reg_right, stmt.name, stmt.type)	
        self.free_scratch_register(reg_right)
