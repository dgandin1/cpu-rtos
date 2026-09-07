from parser import Node, VarDecl, If, Binary, Literal, Variable, ExprStmt, Assign, Block, While, Struct, Funct, FunctCall, ReturnStmt, Unary, PointerType, FieldAccess
from lexer import TokenType


# ARCHITECTURE:
# SP - R1
# PC - R31
# Return Address - R30
# Return value - r29
# interrupt status register - r26
# Interrupt retunr address - r27

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

    def declare_variable(self, name, type_, struct_layouts):
        # Reserve slot on stack frame
        # Slot 0 is reserved for RA, so locals start at offset 1, 2, 3...
        size = 1
        if isinstance(type_, str) and type_ in struct_layouts:
            size = struct_layouts[type_]["size"]

        base_offset = self.frame_offset + 1
        self.frame_offset += size
        self.symbols[name] = {
            "name": name,
            "offset": base_offset,
            "type": type_,
            "size": size
        }
        return base_offset


class CodeGeneratorSimplified:

    def __init__(self, tree, stack_start):
        
        self.tree = tree
        self.current_register = 8
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

        self.label_counter = 0

        self.struct_layouts = {}

        self.global_types = {}

        self.function_names = []
    
    def emit(self, line):

        self.code.append(line)

    def new_label(self, prefix):
        label = f"{prefix}_{self.label_counter}"
        self.label_counter += 1
        return label
    
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

        if self.current_register - 1 in [26, 27, 29, 30]:
            self.current_register += 1

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
                self.function_names.append(stmt.name)
            elif isinstance(stmt, Struct):
                self.register_struct(stmt)
            else:
                global_statements.append(stmt)

        # check if ISQ_handler() exists, if so, emit it
        irq_exists = False
        for func in functions:
            if func.name == "IRQ_handler":
                irq_exists = True
                break

        #If IRQ handler exists do, position jump to it correctly 
        if irq_exists:
            self.emit("BEQ x0 x0 4")
            self.emit("ADD x0 x0 x0")
            self.emit("ADD x0 x0 x0")
            self.emit("BEQ x0 x0 IRQ_handler")

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
            if not isinstance(stmt, VarDecl): 
                continue
                
            name = stmt.name
            
            self.global_types[name] = stmt.type
            
            if stmt.initializer is not None:
                self.emit(f"ADDI r2 r0 {stmt.initializer.value}")
                self.emit(f"SW r2 r0 {self.bss_offset}")
            
            self.globals[name] = self.bss_offset
            
            size = 1
            if isinstance(stmt.type, str) and stmt.type in self.struct_layouts:
                size = self.struct_layouts[stmt.type]["size"]
            self.bss_offset += size
    
    
    def calulate_function_stack_size(self, stmt):
        def count_decls(statements):
            total = 0
            for s in statements:
                if isinstance(s, VarDecl):
                    if isinstance(s.type, str) and s.type in self.struct_layouts:
                        total += self.struct_layouts[s.type]["size"]
                    else:
                        total += 1
                elif isinstance(s, If):
                    total += count_decls(s.then_branch.statements)
                elif isinstance(s, While):
                    total += count_decls(s.body.statements)
            return total

        # 1 slot for Return Address + all local declarations + parameters
        return 1 + count_decls(stmt.body.statements) + len(stmt.params)

    def get_type(self, node):
        if isinstance(node, Variable):
            sym = self.scopes[-1].lookup(node.name)
            if sym: return sym["type"]
            
            if node.name in self.global_types:
                return self.global_types[node.name]
                
        elif isinstance(node, FieldAccess):
            
            base_type = self.get_type(node.object_expr)
           
            return self.struct_layouts[base_type]["fields"][node.field]["type"]
            
        elif isinstance(node, Unary) and node.operator.type == TokenType.MUL:
            
            base_type = self.get_type(node.operand)
            if isinstance(base_type, PointerType):
                return base_type.base
                
        return TokenType.INT

    #Generates the address of a variable. Used for pointers
    def generate_address(self, node):

        

        if isinstance(node, Variable):

            result_register = self.next_reg()

            # Global variable
            if node.name in self.globals:
                address = self.globals[node.name]
                self.emit(f"ADDI {result_register} r0 {address}")
                return result_register

            # Local variable
            sym = self.scopes[-1].lookup(node.name)

            if not sym:
                raise Exception(f"Undefined variable {node.name}")

            self.emit(f"ADDI {result_register} r1 {sym['offset']}")
            return result_register

        if isinstance(node, FieldAccess):

            #recursively get the base address
            base_reg = self.generate_address(node.object_expr)
            struct_type = self.get_type(node.object_expr)
            field_offset = self.struct_layouts[struct_type]["fields"][node.field]["offset"]
            if field_offset > 0:
                self.emit(f"ADDI {base_reg} {base_reg} {field_offset}")
            return base_reg

        if isinstance(node, Unary) and node.operator.type == TokenType.MUL:
            return self.generate_expr(node.operand)

        raise Exception("Cannot take address of this expression")

    def register_struct(self, stmt):

        offset = 0
        fields = {}
        for decl in stmt.declerations:
            field_type = decl["type"]
            pointer_depth = decl.get("pointer_depth", 0)
            for _ in range(pointer_depth):
                field_type = PointerType(field_type)
            # Assuming only type is int [FIX when adding more datatypes]
            fields[decl["name"]] = {"offset":offset, "type":field_type}
            offset += 1
        self.struct_layouts[stmt.name] = {"size":offset, "fields":fields}
    
        
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
            offset = current_scope.declare_variable(param["name"], param["type"], self.struct_layouts)
            arg_reg = f"r{i + 3}"
            self.emit(f"SW {arg_reg} r1 {offset}")
        
        self.generate_block(stmt.body.statements)

        #restore PC
        self.emit(f"LW r30 r1 0")
        self.emit(f"ADDI r1 r1 {frame_size}")

        if stmt.name == "IRQ_handler":
            self.emit("MRET")
        else:
            self.emit(f"JMP r30")
        self.scopes.pop()

    def generate_funct_call(self, stmt):
        if stmt.expr.name.value == "__asm__":
            self.emit(stmt.expr.params[0].value)
            return
        elif stmt.expr.name.value == "__long__":
            tmp_reg = self.next_reg()
            val = stmt.expr.params[0].value
            if val == 0:
                self.emit(f"ADD {tmp_reg}, r0, r0")
                return tmp_reg
            bits = bin(val)[2:]  
            self.emit(f"ADDI {tmp_reg} r0 1")
            for bit in bits[1:]:
                self.emit(f"SLL {tmp_reg} {tmp_reg} 1")
                if bit == "1":
                    self.emit(f"ADDI {tmp_reg} {tmp_reg} 1")
            return tmp_reg
        elif stmt.expr.name.value == "__get_sp":
            reg = self.next_reg()
            self.emit(f"ADD {reg} r0 r1")
            return reg
        elif stmt.expr.name.value == "__save_sp":
            val_reg = self.generate_expr(stmt.expr.params[0])
            self.emit(f"ADD r1 r0 {val_reg}")
            self.free_reg(val_reg)
            return val_reg

        #evaluate in safe tempory register
        eval_regs = []
        for i, arg in enumerate(stmt.expr.params):
            reg = self.generate_expr(arg)
            eval_regs.append(reg)
        
        for i, reg in enumerate(eval_regs):
            arg_reg = f"r{i + 3}"
            self.emit(f"ADD {arg_reg} x0 {reg}")
            
            # Safely free the temporary register now that it's an argument
            self.free_reg(reg)
        
        # 3. Call the function
        self.emit("ADDI r30 r31 2")
        self.emit(f"BEQ r0 r0 {stmt.expr.name.value}")

        return "r29"
    
    def generate_return(self, stmt):

        reg_val = self.generate_expr(stmt.expr.expr)

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
                self.generate_if(stmt)
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


        label_then = self.new_label("if_then")
        label_end = self.new_label("if_end")

        if condition.operator.type == TokenType.LT:
            self.emit(f"BLT {reg_left} {reg_right} {label_then}")
            self.emit(f"BEQ x0 x0 {label_end}")
        elif condition.operator.type == TokenType.GT:
            self.emit(f"BLT {reg_right} {reg_left} {label_then}")
            self.emit(f"BEQ x0 x0 {label_end}")
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

        elif isinstance(node, FunctCall):

            return self.generate_funct_call(ExprStmt(expr=node))
            
            
        elif isinstance(node, Variable) or isinstance(node, FieldAccess):

            # Is variable a function pointer?
            if isinstance(node, Variable) and node.name in self.function_names:
                result_register = self.next_reg()
                self.emit(f"ADDI {result_register} r0 __ADDR__{node.name}")
                return result_register

            addr_reg = self.generate_address(node)
            
            self.emit(f"LW {addr_reg} {addr_reg} 0")
            return addr_reg
            
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

    def generate_unary(self, node):

        if node.operator.type == TokenType.AMPERSAND:
            return self.generate_address(node.operand)

        operand_reg = self.generate_expr(node.operand)
        result_register = self.next_reg()

        if node.operator.type == TokenType.MINUS:
            self.emit(f"SUB {result_register} x0 {operand_reg}")
        elif node.operator.type == TokenType.MUL:
            self.emit(f"LW {result_register} {operand_reg} 0")
        else:
            raise Exception("Unsupported unary operator")

        self.free_reg(operand_reg)

        return result_register

    def generate_expr(self, stmt):
            if isinstance(stmt, Literal):
                return self.generate_binary(stmt)

            elif isinstance(stmt, Variable) or isinstance(stmt, FieldAccess):
                return self.generate_binary(stmt)

            elif isinstance(stmt, Binary):
                return self.generate_binary(stmt)

            elif isinstance(stmt, Unary):
                return self.generate_unary(stmt)

            elif isinstance(stmt, Assign):
                return self.generate_assign(stmt)

            elif isinstance(stmt, ExprStmt):
                if isinstance(stmt.expr, Assign):
                    return self.generate_assign(stmt.expr)

                elif isinstance(stmt.expr, FunctCall):
                    return self.generate_funct_call(stmt)

                return self.generate_expr(stmt.expr)

            elif isinstance(stmt, FunctCall):
                return self.generate_funct_call(ExprStmt(expr=stmt))

            else:
                print(stmt)
                raise Exception("Unsupported expression type")
    
    def generate_assign(self, stmt:Assign):

        reg_val = self.generate_expr(stmt.value)
        addr_reg = self.generate_address(stmt.target)

        self.emit(f"SW {reg_val} {addr_reg} 0")

        self.free_reg(reg_val)
        self.free_reg(addr_reg)
        return

    
    def generate_var_decl(self, stmt:VarDecl):

        offset = self.scopes[-1].declare_variable(stmt.name, stmt.type, self.struct_layouts)
        if stmt.initializer is not None:
            reg_right = self.generate_expr(stmt.initializer)

            self.emit(f"SW {reg_right} r1 {offset}")
            self.free_reg(reg_right)
    
    def generate_while(self, stmt):
        
        condition = stmt.condition

        label_start = self.new_label("start")
        label_end = self.new_label("end")

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

        
    
