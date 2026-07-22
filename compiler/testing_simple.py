import parser
import lexer
import generator2
import linker

with open("example.c-", "r") as file:
    read_ = file.read()
l = lexer.Lexer(read_)
p = l.tokenize()
print(p)
r = parser.Parser(p)
t = r.parse()
print(t)
g = generator2.CodeGeneratorSimplified(t, 100)
i =  g.generate_code()
print(i)
li = linker.Linker(i)
final = li.replace_labels()

with open("output.asm", "w") as file:
    file.write('\n'.join(final))
