import sys

def rtb(register):

    num = bin(int(register[1:]))[2:]
    i = len(num)
    while i < 5:
        num = '0' + num
        i+=1
    return num

def imm12tb(imm):

    num = bin(int(imm[1:]))[2:]
    i = len(num)
    while i < 12:
        num = '0' + num
        i+=1
    return num

print("Tiny modified RISC-V Assembly Compiler for DukeCPU")
print("*****************************************")

file_name = sys.argv[1]
output_name = sys.argv[2]

with open(file_name, "r") as f:

    contents = f.readlines()

output = []

for line in contents:

    line = line.lower().split()
    line_o = ""

    if line[0] == "add":
        line_o = "0000000" + rtb(line[3]) + rtb(line[2]) + "000" + rtb(line[1]) + "0110011"
    elif line[0] == "sub":
        line_o = "0100000" + rtb(line[3]) + rtb(line[2]) + "000" + rtb(line[1]) + "0110011"
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
    output.append(line_o + "\n")

with open(output_name + ".mem", "w") as f:
    f.writelines(output)

print(f"Compiled machine code to {output_name}.mem successfully!")

 
 