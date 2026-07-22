import sys

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
        
        elif line[0] == "jmp":
            
            imm_str = "000000000000"
            sa_str = rtb(line[1])
            sb_str = "00000"
            line_o = imm_str + sa_str + "011" + sb_str + "0100111"

        hex_string = f"{int(line_o, 2):08x}"
        output.append(hex_string.upper() + "\n")

    with open(output_file, "w") as f:
        f.writelines(output)

    print(f"Compiled machine code to {output_name}.mem successfully!")

    
    

if __name__ == "__main__":

    print("Tiny modified RISC-V Assembly Compiler for DukeCPU")
    print("*****************************************")

    file_name = sys.argv[1]
    output_name = sys.argv[2]

    with open(file_name, "r") as f:

        contents = f.readlines()

    assemble(output_name, contents)

