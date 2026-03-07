import parser
import lexer
import generator

with open("example.c-", "r") as file:
    read_ = file.read()
l = lexer.Lexer(read_)
p = l.tokenize()
print(p)
r = parser.Parser(p)
t = r.parse()
print(t)
g = generator.CodeGenerator(t, 0, 100)
g.globals()
print(g.code)