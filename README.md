# Brainfuck Script - A High-Level Transpiler for Brainfuck

BrainfuckScript (BFS) is a human-readable programming language that transpiles to Brainfuck. While Brainfuck is notoriously difficult to write directly, BFS provides familiar syntax similar to C, making it accessible to write programs that ultimately run as Brainfuck code.

## Features

- **C-like syntax**: Write code with familiar syntax including variables, arithmetic, and control structures
- **Type system**: All variables are unsigned 8-bit integers (0-255)
- **Character literals**: Automatically converts character literals like `'A'` to their ASCII values
- **Preprocessor defines**: Use `#define` for constants
- **File inclusion**: Include other BFS files in your code
- **Control flow**: Conditional statements (`if`/`else`) and loops (`while`)
- **I/O operations**: Read input and output characters
- **Comparison operators**: Use `==` and `!=` for comparisons (other operators not supported)

## Installation

### Prerequisites

- Python 3.13 or higher
- Poetry

### Setup

```bash
# Clone the repository
git clone https://github.com/ImGajeed76/brainfuck_transpiler
cd brainfuck_transpiler

# Install dependencies
poetry install
```

## Usage

```bash
# Basic usage
poetry run python main.py your_code.bfs -o output.bf

# To see the intermediate instruction set (for debugging)
poetry run python main.py your_code.bfs -o output.bf --debug
```

## Example Code

The following example creates a pyramid of asterisks:

```bfs
#define SPACE ' '
#define STAR '*'
#define NEWLINE '
'
#define HEIGHT 7

// Pyramid height
var height = HEIGHT;
var row = 0;

while (height) {
    // Print spaces (height-1 spaces per row)
    var spaces = height - 1;
    while (spaces) {
        output(SPACE);
        spaces = spaces - 1;
    }

    // Print stars (2*row+1 stars per row)
    // Using only addition: row + row + 1
    var stars = row;
    stars = stars + row;
    stars = stars + 1;
    while (stars) {
        output(STAR);
        stars = stars - 1;
    }

    // Print newline
    output(NEWLINE);

    // Move to next row
    height = height - 1;
    row = row + 1;
}
```

Output:
```
      *
     ***
    *****
   *******
  *********
 ***********
*************
```

## Language Syntax

### Variables

```bfs
var name = value;  // Declare and initialize
name = value;      // Assignment
```

All variables are unsigned 8-bit integers (0-255).

### Preprocessor Directives

```bfs
#define NAME value  // Define constants
#include "file.bfs" // Include another file
```

### Control Flow

```bfs
// While loop
while (condition) {
    // Code block
}

// If statement
if (condition) {
    // Code block
}

// If-else statement
if (condition) {
    // Code block
} else {
    // Code block
}
```

Note: Conditions are considered true if non-zero, false if zero.

### I/O Operations

```bfs
output(variable);  // Output ASCII character
input(variable);   // Read ASCII character from input
```

## How It Works

The transpiler works in two stages:

1. **Parsing and Intermediate Code Generation**: The BFS code is parsed using the Lark parser, generating an intermediate instruction set.

2. **Brainfuck Code Generation**: The intermediate instructions are converted to Brainfuck.

### Example Intermediate Instruction Set

Using the `--debug` flag shows the intermediate instruction set:

```
LOAD_A_IMM 7
STORE_A 2
LOAD_A_IMM 0
STORE_A 3
LOAD_A_MEM 2
LOOP_START
...
```

### Memory Model

The transpiler manages memory allocation for variables. For example:

```
# Memory map:
# height: address 2
# row: address 3
# spaces: address 4
# stars: address 5
```

## Running Brainfuck Code

The transpiler doesn't include a Brainfuck interpreter. To run the generated code:

- Online interpreter: https://copy.sh/brainfuck/
- Debugging tool: https://www.iamcal.com/misc/bf_debug/

## Limitations

- Only unsigned 8-bit integers (0-255)
- Limited arithmetic operations (addition and subtraction)
- No function support (yet)
- No arrays (yet)
- No string literals (yet)

## Future Plans

- More arithmetic operations (multiplication, division)
- Arrays and pointers
- Function support
- String handling
- Compiler optimizations
- Built-in Brainfuck interpreter

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

---
Built with ❤️ by [Oliver Seifert](https://oseifert.ch)
