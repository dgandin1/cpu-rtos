import sys
import parser
import lexer
import generator2
import linker
import assembler


def write_of(of, content):

    with open(of, "w") as file:
        if isinstance(content[0], str):
            file.writelines(line + "\n" for line in content)
        else:
            file.write(str(content))

if sys.argv[1] == "--help":

    print("Usage: python g--.py [options] file...")
    print("Options:")
    print("--help       Display this information.")
    print("--version    Display this compiler version.")
    print("-o <file>    Place the output into <file>.")
    print("-L           Lex only. Outputs tokens.")
    print("-P           Lex and parse only. Outputs AST.")
    print("-S           Lex, parse and generate. Outputs un-linked assembly.")
    print("-C           Compile and link, outputs runnable assembly")
    sys.exit()

elif sys.argv[1] == "--version":
    print("g-- (G--) 0.0.1 20260723")
    sys.exit()

output_file = ""
first_file_arg = 0

if "-o" in sys.argv:
    i = sys.argv.index("-o")
    output_file = sys.argv[i + 1]
    first_file_arg = i + 2
else:
    print("ERROR: No ouput file selected")

files = sys.argv[first_file_arg:]

output_buf = ""

for i, filename in enumerate(files):

    with open(filename, "r") as f:

        output_buf += f.read() + "\n"

l = lexer.Lexer(output_buf)
p = l.tokenize()

if "-L" in sys.argv:
    write_of(output_file, p)
    sys.exit()

r = parser.Parser(p)
t = r.parse()

if "-P" in sys.argv:
    write_of(output_file, t)
    sys.exit()

g = generator2.CodeGeneratorSimplified(t, 100)
i = g.generate_code()

if "-S" in sys.argv:
    write_of(output_file, i)
    sys.exit()

li = linker.Linker(i)
final = li.replace_labels()

if "-C" in sys.argv:
    write_of(output_file, final)
    sys.exit()

a = assembler.assemble(output_file, final)

