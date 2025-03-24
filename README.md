# BrainfuckScript (bfs)

BrainfuckScript (bfs) is a higher-level language designed to make brainfuck programming more accessible and
maintainable. It provides a simplified syntax for common programming patterns while ultimately compiling down to pure
brainfuck code.

## Introduction

Brainfuck is known for its extreme minimalism, making it challenging to write practical programs. BrainfuckScript
bridges this gap by offering familiar programming constructs that automatically translate to optimized brainfuck
instructions.

## Language Features

### Variables

```
var name = value;  // Declare and initialize a variable
```

### Basic Arithmetic

```
var x = 5;
var y = 10;
var z = x + y;  // Addition
var w = z - x;  // Subtraction
```

### Control Flow

```
while (condition) {
    // Code to execute while condition is non-zero
}
```

### I/O Operations

```
output(value);  // Outputs the ASCII character corresponding to the value
```

### ASCII Constants

Common practice is to define ASCII values as variables:

```
var space = 32;
var star = 42;
var newline = 10;
```

## Compilation Process

BrainfuckScript analyzes your code and generates optimized brainfuck instructions that:

1. Manage memory cells for your variables
2. Implement arithmetic operations using brainfuck's increment/decrement
3. Handle control structures through brainfuck's looping mechanism
4. Translate high-level I/O into brainfuck's `.` and `,` operators

## Example

Here's a simple program that prints a pyramid:

```
// ASCII character codes
var space = 32;
var star = 42;
var newline = 10;

// Pyramid height
var height = 5;
var row = 0;

while (height) {
    // Print spaces
    var spaces = height - 1;
    while (spaces) {
        output(space);
        spaces = spaces - 1;
    }
    
    // Print stars
    var stars = row;
    stars = stars + row;
    stars = stars + 1;
    while (stars) {
        output(star);
        stars = stars - 1;
    }
    
    output(newline);
    
    height = height - 1;
    row = row + 1;
}
```

## Usage

> Make sure you have Python and Poetry installed on your system. Install needed dependencies by running `poetry install`.

1. Create a `code.bfs` file with your BrainfuckScript code in the same directory as the `main.py` script.
2. Run the `main.py` script to compile your BrainfuckScript code into raw brainfuck code.
3. Copy the generated brainfuck code and run it using a brainfuck interpreter.

## Limitations

- Only supports addition and subtraction for arithmetic
- No direct input handling in the current syntax examples
- Limited to the core features shown in examples
- No functions or subroutines defined

## Benefits

- Readable code compared to raw brainfuck
- Variable management abstracted away
- Memory allocation handled automatically
- Familiar syntax for programmers coming from C-like languages

## Purpose

BrainfuckScript makes brainfuck programming more approachable while maintaining the "compile to brainfuck" target,
allowing programmers to write complex algorithms without dealing with the extreme low-level nature of raw brainfuck
code.