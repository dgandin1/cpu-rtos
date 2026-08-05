# Software

The CPU comes with a compiler, linker and assembler to assist with writing programs. The compiler's source lanugage (known as C-) uses C syntax, and implements a subset of C features. 

### C- Reference Guide

C- syntax is identicle to C syntax, but does not implement all C features. Below is a complete list of C features implemented:

* Variables of types `int`
* `if`, `else`, and `while` statements
* `structs`
* Functions of return type `int` and `void`
* Pointers (WIP)
* Conditionals (<, >, <=, >=, ==)

### Compiler

The compiler involves four stages: lexing, parsing and code generation. Lexing takes the text from a c- file and converts it into tokens. Parsing uses recursive descent to stucture the tokens into an abstract syntax tree (AST). Code generation takes that AST and converts each statement and block into its corresponding assembly. 

As of now, code generation prioritizes simplicity over optimality. There is no register re-use for variables, and variables are always loaded and stored upon modification or access. 

Global variables are saved on the heap beggining at address 0x00000005. The stack grows down and starts at address 0x000000064. All local varaibles are stored on the stack. 

Since there is no dedicated assembly instuctions to jump to or return from a function, the compiler manually saves the return address to r30 and utililizes a JMP instuction to go back upon return.

The compiled code immedietly jumps to the global `main` function entry point. If no such function exists a compile time error will be emitted.

### Using the Compiler

An included utility (g--) is included to help with compiling programs. To compiler run:
```
python g--.py -o output.hex src1.c- src2.c- ...*
```

No `#include` statements need to be added to source files, but every file must be included in the compilation command. The `-o` argument specifies the output file. Additional program arguments include:

* -L           Lex only. Outputs tokens.
* -P           Lex and parse only. Outputs AST.
* -S           Lex, parse and generate. Outputs un-linked assembly.
* -C           Compile and link, outputs runnable assembly

### Using Interrupts

To use interrupts, a function named `IRQ_handler` (case sensitive) must be declared. Upon interrupt, execution will immedietly jump to this function. Logic can then be added to respond the interrupt according to r26 (the interrupt cause register). This register will contain the ID of the interrupt triggered. No return statement should be added to the IRQ handler, and the compiler will automatically emit a MRET instuction at the end.

### Standard Library Reference

A number of standard C- utlities libraries are included in addition to the RTOS (see RTOS.md) to aid with development. They are located in the `compiler/std` directory and must be manually included in the compilation path.

`math.c`:
* mul(a, b): Returns the product of `a` and `b`.
* lshift(a, val): Returns `a` left shifted `val` times.
* rshift(a, val): Returns `a` right shifted `val` times.
* min(a, b): Returns the minimum of `a` and `b`.
* max(a, b): Returns the maximum of `a` and `b`.
* abs(a): Returns the absolute value of `a`.

`stdio.c`
* print(a): Prints `a` to stdout.
* pixel_on(x, y): Turns the pixel at coordinates `x`, `y` on.
* pixel_off(x, y): Turns the pixel at coordinates `x`, `y` offs.
