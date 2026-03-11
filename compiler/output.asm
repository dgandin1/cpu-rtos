LW x0 #0
SW x0 #100
LW x1 204
ADDI x12 x0 #2
LW x1 x12
ADDI x12 x0 #1
LW x1 x12
ADD x1 x1 x1
BEQ, #4 then_2
J end_2
then_2:
LW x1 204
ADDI x12 x0 #1
LW x1 x12
ADD x1 x1 x1
SW 204 x1
ADDI x12 x0 #1
LW x1 x12
SW x1 #0
end_2: