from parser import Node, VarDecl, If, Binary, Literal, Variable, ExprStmt, Assign, Block, While, Struct, Funct, FunctCall, ReturnStmt
from lexer import TokenType


# ARCHITECTURE:
# SP - R1
# PC - R31
# Return Address - R30


class Symbol_Table:

    def __init__(self, parent_table=None):
        self.symbols = {}
        self.frame_offset = 0  # Bytes/words relative to SP
        self.parent_table = parent_table
        self.global_vars = {}
    
    def lookup(self, name):
        if name in self.symbols:
            return self.symbols[name]
        if self.parent_table:
            return self.parent_table.lookup(name)
        return None

    def declare_variable(self, name, type_):
        # Reserve slot on stack frame
        # Slot 0 is reserved for RA, so locals start at offset 1, 2, 3...
        self.frame_offset += 1
        self.symbols[name] = {
            "name": name,
            "offset": self.frame_offset,
            "type": type_
        }
        return self.frame_offset


class CodeGeneratorSimplified:

    def __init__(self, tree, stack_start):
        
        self.tree = tree
        self.current_register = 3
        self.code = []
        self.current_line = 0
        self.stack_pointer = stack_start
        self.current = 0

        self.scopes = []

        self.variables_to_regs = {}

        #{"name:"name, "location":global addr}
        self.globals = {}
        self.bss_base = 20
        self.bss_offset = self.bss_base

        self.free_registers = []

        self.current_frame_size = 0
    
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

        #setup stack pointer
        self.emit(f"ADDI x1 x0 {self.stack_pointer}")


        # --- STEP 2: SEPARATE AST NODES ---
        functions = []
        global_statements = []

        for stmt in self.tree:
            if isinstance(stmt, Funct):
                functions.append(stmt)
            else:
                global_statements.append(stmt)

        # --- STEP 3: GENERATE GLOBAL SCOPE & FUNCTIONS ---
        globals_scope = Symbol_Table(None)
        self.scopes.append(globals_scope)
        self.generate_globals(global_statements)

        # Jump directly to main function
        self.emit("ADDI r30 r31 2")  # Load return address
        self.emit("BEQ x0 x0 main")        # Call main
        
        # Infinite loop / Halt program when main returns
        self.emit("halt_loop:")
        self.emit("BEQ x0 x0 halt_loop")

        # Emit all functions first so they sit in memory independently
        for func in functions:
            self.generate_funct(func)

        return self.code
    
    def generate_globals(self, statements):

        for stmt in statements:
            name = stmt.name
            self.emit(f"ADDI r2 r0 {stmt.initializer.value}")
            self.emit(f"SW r2 r0 {self.bss_offset}")
            self.globals[name] = self.bss_offset
            self.bss_offset += 1
    
    
    def calulate_function_stack_size(self, stmt):
        def count_decls(statements):
            total = 0
            for s in statements:
                if isinstance(s, VarDecl):
                    total += 1
                elif isinstance(s, If):
                    total += count_decls(s.then_branch.statements)
                elif isinstance(s, While):
                    total += count_decls(s.body.statements)
            return total

        # 1 slot for Return Address + all local declarations + parameters
        return 1 + count_decls(stmt.body.statements) + len(stmt.params)
        
    def generate_funct(self, stmt):

        current_scope = Symbol_Table(parent_table=self.scopes[-1] if self.scopes else None)
        self.scopes.append(current_scope)

        frame_size = self.calulate_function_stack_size(stmt)
        self.current_frame_size = frame_size

        self.emit(f"{stmt.name}:")
        self.emit(f"ADDI r1 r1 -{self.calulate_function_stack_size(stmt)}")
        self.emit(f"SW r30 r1 0")

        #parameters
        for i, param in enumerate(stmt.params):
            offset = current_scope.declare_variable(param["name"], param["type"])
            arg_reg = f"r{i + 3}"
            self.emit(f"SW {arg_reg} r1 -{offset}")
        
        self.generate_block(stmt.body.statements)

        #restore PC
        self.emit(f"LW r30 r1 0")
        self.emit(f"ADDI r1 r1 {frame_size}")
        self.emit(f"JMP r30")
        self.scopes.pop()

    def generate_funct_call(self, stmt):

        #evaluate arguments and put into registers
        for i, arg in enumerate(stmt.expr.params):
            reg = self.generate_expr(arg)
            arg_reg = f"r{i + 3}"
            if reg != arg_reg:
                self.emit(f"ADD {arg_reg} x0 {reg}")
                self.free_reg(reg)
        
        #return address
        self.emit("ADDI r30 r31 2")

        self.emit(f"BEQ r0 r0 {stmt.expr.name.value}")

        return "r29"
    
    def generate_return(self, stmt):

        reg_val = self.generate_expr(stmt.expr)

        if reg_val != "r29":

            self.emit(f"ADD r29 r0 {reg_val}")
            self.free_reg(reg_val)

        #restore PC
        self.emit(f"LW r30 r1 0")
        self.emit(f"ADDI r1 r1 {self.current_frame_size}")
        self.emit(f"JMP r30")

    
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
            elif (isinstance(stmt, Funct)):
                self.generate_funct(stmt)
            elif (isinstance(stmt, ReturnStmt)):
                self.generate_return(stmt)
    
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

            if node.name in self.globals:
                offset = self.globals[node.name]
                result_register = self.next_reg()
                self.emit(f"LW {result_register} r0 {offset}")
                return result_register

            sym = self.scopes[-1].lookup(node.name)
            if not sym:
                raise Exception(f"Undefined variable {node.name}")
            
            result_register = self.next_reg()
            # LW result_register, offset(SP)
            self.emit(f"LW {result_register} r1 -{sym['offset']}")
            return result_register
            
        elif isinstance(node, Binary):
            result_register = self.next_reg()
            left_reg = self.generate_expr(node.left)
            right_reg = self.generate_expr(node.right)

            if node.operator.type == TokenType.PLUS:
                self.emit(f"ADD {result_register} {left_reg} {right_reg}")
            elif node.operator.type == TokenType.MINUS:
                self.emit(f"SUB {result_register} {left_reg} {right_reg}")
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
        elif isinstance(stmt.expr, FunctCall):
            return self.generate_funct_call(stmt)
        else:
            print(stmt)
            raise Exception("Unsupported expression type")
    
    def generate_assign(self, stmt:Assign):

        if stmt.name in self.globals:
            reg_val = self.generate_expr(stmt.value)
            self.emit(f"SW {reg_val} r0 {self.globals[stmt.name]}")
            self.free_reg(reg_val)
            return

        sym = self.scopes[-1].lookup(stmt.name)
        if not sym:
            raise Exception(f"Variable {stmt.name} not declared in scope.")

        reg_val = self.generate_expr(stmt.value)
        # Store updated value to stack location
        self.emit(f"SW {reg_val} r1 -{sym['offset']}")
        self.free_reg(reg_val)
    
    def generate_var_decl(self, stmt:VarDecl):

        offset = self.scopes[-1].declare_variable(stmt.name, stmt.type)
        reg_right = self.generate_binary(stmt.initializer)
        self.emit(f"SW {reg_right} r1 -{offset}")
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

        self.free_reg(reg_left)
        self.free_reg(reg_right)

        self.generate_block(stmt.body.statements)

        self.emit(f"BEQ x0 x0 {label_start}")
        self.emit(f"{label_end}:")

        
    
