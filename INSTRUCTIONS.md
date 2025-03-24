# Simple 8-bit Processor Instruction Set Documentation

## Overview

This document describes a simple 8-bit processor architecture with two registers, memory storage, and basic I/O capabilities. The processor executes a small set of instructions for loading values, performing arithmetic, handling loops, and processing input/output.

## Architecture

- **Registers**: Two 8-bit registers (REG_A and REG_B)
- **Memory**: Addressable 8-bit memory locations
- **Data Range**: All values (registers and memory) are unsigned 8-bit integers (0-255)
- **I/O**: Character-based ASCII input and output

## Instruction Set

### Register and Memory Operations

| Instruction | Description |
|-------------|-------------|
| `LOAD_A_IMM <value>` | Load immediate value into REG_A |
| `LOAD_A_MEM <address>` | Load value from memory address into REG_A |
| `LOAD_B_IMM <value>` | Load immediate value into REG_B |
| `LOAD_B_MEM <address>` | Load value from memory address into REG_B |
| `STORE_A <address>` | Store value from REG_A to memory address |
| `STORE_B <address>` | Store value from REG_B to memory address |

### Arithmetic Operations

| Instruction | Description |
|-------------|-------------|
| `ADD` | Add REG_B to REG_A, result stored in REG_A |
| `SUB` | Subtract REG_B from REG_A, result stored in REG_A |

### Loop Control

| Instruction | Description |
|-------------|-------------|
| `LOOP_START` | Begin a loop; continues if REG_A > 0, otherwise jumps to after matching LOOP_END |
| `LOOP_END` | End of loop; if REG_A > 0, jumps back to matching LOOP_START, otherwise continues |

### Input/Output Operations

| Instruction | Description |
|-------------|-------------|
| `IN_A` | Read an ASCII character from input into REG_A |
| `IN_B` | Read an ASCII character from input into REG_B |
| `OUT_A` | Output ASCII character represented by value in REG_A |
| `OUT_B` | Output ASCII character represented by value in REG_B |

## Loop Behavior

Loops are based on the value in REG_A:

1. At `LOOP_START`:
   - If REG_A > 0: The processor enters the loop
   - If REG_A = 0: The processor skips to after the matching `LOOP_END`

2. At `LOOP_END`:
   - If REG_A > 0: The processor jumps back to the matching `LOOP_START`
   - If REG_A = 0: The processor continues to the next instruction

Loops can be nested. Each `LOOP_END` instruction corresponds to the most recent `LOOP_START` that hasn't been matched yet.

## Example Program

The following program reads 3 characters from input, increments each character's ASCII value by 1, and outputs the results:

```
# Initialize counter for the loop
LOAD_A_IMM 3     # Load immediate value 3 into REG_A
STORE_A 0        # Store counter in memory address 0

# Main loop
LOOP_START       # Begin loop (runs while REG_A > 0)
    IN_B         # Read a character into REG_B
    
    LOAD_A_IMM 1 # Load immediate value 1 into REG_A
    ADD          # Add REG_B to REG_A (increments the character)
    
    OUT_A        # Output the incremented character
    
    LOAD_A_MEM 0 # Load loop counter from memory into REG_A
    LOAD_B_IMM 1 # Load immediate value 1 into REG_B
    SUB          # Subtract REG_B from REG_A (decrement counter)
    STORE_A 0    # Save updated counter back to memory
LOOP_END         # End loop - goes back to LOOP_START if REG_A > 0
```

This program effectively implements a simple Caesar cipher with a shift of 1 on three input characters.

## Memory Constraints

- All memory addresses and register values are limited to 8 bits (0-255)
- If arithmetic operations result in values outside this range, they will overflow or underflow

## Notes

- This processor follows a simple execution model with no flags or condition codes
- The loop mechanism provides basic control flow capabilities
- There are no jump or branch instructions other than the loop constructs
- The processor has no built-in stack; any subroutine-like behavior must be manually implemented using memory locations