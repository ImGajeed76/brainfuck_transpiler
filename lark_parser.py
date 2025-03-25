import os
from lark import Lark, Transformer


class GrammarDefinition:
    @staticmethod
    def get_grammar():
        return r"""
    program: (define_directive | statement)+

    define_directive: "#define" IDENTIFIER constant

    constant: NUMBER -> number_constant
           | CHARACTER -> character_constant
           | STRING -> string_constant

    statement: variable_declaration
             | assignment
             | input_statement
             | output_statement
             | while_statement
             | if_statement
             | expression ";"

    variable_declaration: "var" IDENTIFIER "=" expression ";"

    assignment: IDENTIFIER "=" expression ";"

    input_statement: "input" "(" IDENTIFIER ")" ";"

    output_statement: "output" "(" expression ")" ";"

    while_statement: "while" "(" expression ")" "{" statement+ "}"

    if_statement: "if" "(" expression ")" "{" statement+ "}" else_clause?

    else_clause: "else" "{" statement+ "}"

    expression: term
              | expression "+" term -> add
              | expression "-" term -> subtract
              | expression "==" term -> equal
              | expression "!=" term -> not_equal

    term: IDENTIFIER -> variable
        | NUMBER -> number
        | CHARACTER -> character
        | "(" expression ")" -> parenthesized

    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
    NUMBER: /[0-9]+/
    CHARACTER: /'(\\.|[^\\'])'/ 
    STRING: /"(\\.|[^\\"])*"/

    COMMENT: /\/\/[^\n]*/ | /\/\*.*?\*\//s

    %import common.WS
    %ignore WS
    %ignore COMMENT
"""


# Manage symbol table
class SymbolTable:
    def __init__(self):
        self.symbols = {}  # Maps variable names to memory addresses
        self.next_address = 2  # Start at address 2, leaving 0 and 1 for temp storage

    def add_symbol(self, name):
        address = self.next_address
        self.next_address += 1
        self.symbols[name] = address
        return address

    def get_address(self, name):
        if name not in self.symbols:
            raise Exception(f"Undefined variable: {name}")
        return self.symbols[name]

    def has_symbol(self, name):
        return name in self.symbols

    def get_symbols(self):
        return self.symbols


# Handles code generation details
class CodeGenerator:
    @staticmethod
    def load_immediate(value):
        if value < 0 or value > 255:
            raise Exception(f"Value {value} out of range for 8-bit processor")
        return f"LOAD_A_IMM {value}"

    @staticmethod
    def load_from_memory(address):
        return f"LOAD_A_MEM {address}"

    @staticmethod
    def store_to_memory(address):
        return f"STORE_A {address}"

    @staticmethod
    def load_b_immediate(value):
        return f"LOAD_B_IMM {value}"

    @staticmethod
    def load_b_from_memory(address):
        return f"LOAD_B_MEM {address}"

    @staticmethod
    def add():
        return "ADD"

    @staticmethod
    def subtract():
        return "SUB"

    @staticmethod
    def input():
        return "IN_A"

    @staticmethod
    def output():
        return "OUT_A"

    @staticmethod
    def loop_start():
        return "LOOP_START"

    @staticmethod
    def loop_end():
        return "LOOP_END"


# Main compiler that handles tree transformation
class CompilerTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.symbol_table = SymbolTable()
        self.code_gen = CodeGenerator()
        self.optimizer = ExpressionOptimizer(self.code_gen)
        self.defined_constants = {
            # Default constants for true and false
            "true": 1,
            "false": 0
        }  # Store #define constants

    def program(self, items):
        result = []
        for item in items:
            if item and isinstance(item, list):  # Only append statements that generate code
                result.extend(item)
        return result

    def define_directive(self, items):
        name = items[0].value
        value = items[1]

        # Store the defined constant value
        self.defined_constants[name] = value
        # Return None since #define doesn't generate code
        return None

    def number_constant(self, items):
        return int(items[0].value)

    def character_constant(self, items):
        char_token = items[0].value
        char = self._extract_character(char_token)
        return ord(char)

    def string_constant(self, items):
        # For completeness, though we won't use this in the simple language
        string_token = items[0].value
        # Remove quotes and handle escaping
        return string_token[1:-1]

    def statement(self, items):
        if len(items) == 1:
            return items[0]
        return items

    def character(self, items):
        char_token = items[0].value
        char = self._extract_character(char_token)
        ascii_value = ord(char)

        if ascii_value < 0 or ascii_value > 255:
            raise Exception(f"ASCII value {ascii_value} out of range for 8-bit processor")

        return [self.code_gen.load_immediate(ascii_value)]

    def _extract_character(self, char_token):
        if len(char_token) == 3:  # Simple case: 'A'
            return char_token[1]
        elif char_token[1] == '\\':  # Escaped character: '\n'
            escape_map = {
                '\\n': '\n',
                '\\t': '\t',
                '\\r': '\r',
                '\\\\': '\\',
                '\\\'': '\'',
                '\\0': '\0'
            }
            escaped_seq = char_token[1:3]
            return escape_map.get(escaped_seq, escaped_seq[1])
        return char_token[1]

    def variable_declaration(self, items):
        var_name = items[0].value
        expr_code = items[1]

        # Allocate memory for the variable
        address = self.symbol_table.add_symbol(var_name)

        # Generate code to evaluate expression and store it
        code = expr_code.copy()  # Expression result will be in REG_A
        code.append(self.code_gen.store_to_memory(address))
        return ["# Variable declaration: " + var_name] + code

    def assignment(self, items):
        var_name = items[0].value
        expr_code = items[1]

        address = self.symbol_table.get_address(var_name)

        # Generate code to evaluate expression and store it
        code = expr_code.copy()  # Expression result will be in REG_A
        code.append(self.code_gen.store_to_memory(address))
        return ["# Assignment: " + var_name] + code

    def input_statement(self, items):
        var_name = items[0].value
        address = self.symbol_table.get_address(var_name)

        code = [
            self.code_gen.input(),
            self.code_gen.store_to_memory(address)
        ]
        return ["# Input statement"] + code

    def output_statement(self, items):
        expr_code = items[0]

        code = expr_code.copy()  # Expression result will be in REG_A
        code.append(self.code_gen.output())
        return ["# Output statement"] + code

    def while_statement(self, items):
        condition_code = items[0]
        body_statements = items[1:]

        # Collect all statement code in the body
        body_code = []
        for stmt in body_statements:
            if stmt:  # Some statements might return None
                body_code.extend(stmt)

        code = condition_code.copy()  # Condition result will be in REG_A
        code.append(self.code_gen.loop_start())
        code.extend(body_code)
        code.extend(condition_code)  # Re-evaluate condition
        code.append(self.code_gen.loop_end())

        return ["# While loop"] + code

    def add(self, items):
        return self.optimizer.optimize_binary_operation(items[0], items[1], "ADD")

    def subtract(self, items):
        return self.optimizer.optimize_binary_operation(items[0], items[1], "SUB")

    def equal(self, items):
        # Generate comparison code that will set A to 1 if equal, 0 if not
        left_code = items[0]
        right_code = items[1]

        # Temporary memory locations for comparison
        result_addr = 0  # Will hold final result (1 or 0)

        code = []

        # Initialize result to 1 (assume equal)
        code.append(self.code_gen.load_immediate(1))
        code.append(self.code_gen.store_to_memory(result_addr))

        # Calculate left expression
        code.extend(left_code)
        code.append(self.code_gen.store_to_memory(1))  # Store left value in temp location

        # Calculate right expression
        code.extend(right_code)  # Right result in A

        # Now A has right value, load B with left value
        code.append(self.code_gen.load_b_from_memory(1))

        # SUB will set A to 0 if they're equal
        code.append(self.code_gen.subtract())

        # Use loop to conditionally set result to 0 if values differ
        code.append(self.code_gen.loop_start())  # If A is non-zero (values not equal)
        code.append(self.code_gen.load_immediate(0))  # Set result to 0 (false)
        code.append(self.code_gen.store_to_memory(result_addr))
        code.append(self.code_gen.load_immediate(0))  # Ensure we exit the loop
        code.append(self.code_gen.loop_end())

        # Load final result
        code.append(self.code_gen.load_from_memory(result_addr))

        return ["# Equal"] + code

    def not_equal(self, items):
        # Similar to equal, but inverted result
        left_code = items[0]
        right_code = items[1]

        # Temporary memory locations for comparison
        result_addr = 0  # Will hold final result (1 or 0)

        code = []

        # Initialize result to 0 (assume not equal)
        code.append(self.code_gen.load_immediate(0))
        code.append(self.code_gen.store_to_memory(result_addr))

        # Calculate left expression
        code.extend(left_code)
        code.append(self.code_gen.store_to_memory(1))  # Store left value in temp location

        # Calculate right expression
        code.extend(right_code)  # Right result in A

        # Now A has right value, load B with left value
        code.append(self.code_gen.load_b_from_memory(1))

        # SUB will set A to 0 if they're equal
        code.append(self.code_gen.subtract())

        # Use loop to conditionally set result to 1 if values differ
        code.append(self.code_gen.loop_start())  # If A is non-zero (values not equal)
        code.append(self.code_gen.load_immediate(1))  # Set result to 1 (true)
        code.append(self.code_gen.store_to_memory(result_addr))
        code.append(self.code_gen.load_immediate(0))  # Ensure we exit the loop
        code.append(self.code_gen.loop_end())

        # Load final result
        code.append(self.code_gen.load_from_memory(result_addr))

        return ["# Not equal"] + code

    def variable(self, items):
        var_name = items[0].value

        # Check if it's a defined constant
        if var_name in self.defined_constants:
            constant_value = self.defined_constants[var_name]
            # Generate code based on the constant type
            if isinstance(constant_value, int):
                return [self.code_gen.load_immediate(constant_value)]
            # Handle other types if needed
            else:
                raise Exception(f"Unsupported constant type for {var_name}")

        # Regular variable
        address = self.symbol_table.get_address(var_name)
        return ["# Variable load: " + var_name] + [self.code_gen.load_from_memory(address)]

    def number(self, items):
        value = int(items[0].value)
        return [self.code_gen.load_immediate(value)]

    def parenthesized(self, items):
        return items[0]

    def expression(self, items):
        # For expression that isn't add or subtract
        if len(items) == 1:
            return items[0]
        return items

    def term(self, items):
        if len(items) == 1:
            return items[0]
        return items

    def if_statement(self, items):
        condition_code = items[0]
        if_body_statements = items[1:-1] if len(items) > 2 and isinstance(items[-1], list) else items[1:]
        else_clause = items[-1] if len(items) > 2 and isinstance(items[-1], list) else None

        # Collect all statement code in the if body
        if_body_code = []
        for stmt in if_body_statements:
            if stmt:  # Some statements might return None
                if_body_code.extend(stmt)

        # Check if there's an else block
        has_else = else_clause is not None

        # Generate code
        code = []

        # Create a control variable for the else block if needed
        go_else_address = None
        if has_else:
            # create a new variable to control the else block
            i = 0
            while not go_else_address:
                go_else_name = f"go_else_{i}"
                if not self.symbol_table.has_symbol(go_else_name):
                    go_else_address = self.symbol_table.add_symbol(go_else_name)
                i += 1

            # Initialize go_else to 1
            code.append(self.code_gen.load_immediate(1))
            code.append(self.code_gen.store_to_memory(go_else_address))

        # Evaluate condition
        code.extend(condition_code)

        # If condition is true, execute if block
        code.append(self.code_gen.loop_start())
        code.extend(if_body_code)

        # Set go_else to 0 to skip the else block if it exists
        if has_else:
            code.append(self.code_gen.load_immediate(0))
            code.append(self.code_gen.store_to_memory(go_else_address))

        code.append(self.code_gen.loop_end())

        # If there's an else block, execute it conditionally
        if has_else:
            else_body_code = else_clause

            code.append(self.code_gen.load_from_memory(go_else_address))
            code.append(self.code_gen.loop_start())
            code.extend(else_body_code)

            # Reset go_else to 0 after executing else block
            code.append(self.code_gen.load_immediate(0))
            code.append(self.code_gen.store_to_memory(go_else_address))

            code.append(self.code_gen.loop_end())

        return ["# If statement"] + code

    def else_clause(self, items):
        # Collect all statements in the else clause
        else_body_code = []
        for stmt in items:
            if stmt:  # Some statements might return None
                else_body_code.extend(stmt)
        return ["# Else clause"] + else_body_code


# Handles optimizations for expressions
class ExpressionOptimizer:
    def __init__(self, code_gen):
        self.code_gen = code_gen

    def _is_simple_expression(self, code):
        """Check if this is a simple expression (one instruction)"""
        return len(code) == 1 and (
                code[0].startswith("LOAD_A_IMM") or
                code[0].startswith("LOAD_A_MEM")
        )

    def optimize_binary_operation(self, left_code, right_code, operation):
        # Optimization for common cases
        if self._is_simple_expression(right_code):
            if right_code[0].startswith("LOAD_A_IMM"):
                # If right operand is immediate, extract the value
                value = right_code[0].split()[1]
                code = left_code.copy()  # Load left value to REG_A
                code.append(f"LOAD_B_IMM {value}")  # Load right value to REG_B
                code.append(operation)  # A = A op B
                return ["# Optimized: " + operation] + code

            if right_code[0].startswith("LOAD_A_MEM"):
                # If right operand is a memory reference
                address = right_code[0].split()[1]
                code = left_code.copy()  # Load left value to REG_A
                code.append(f"LOAD_B_MEM {address}")  # Load right value to REG_B
                code.append(operation)  # A = A op B
                return ["# Optimized: " + operation] + code

        # Fall back to general case
        code = left_code.copy()  # Load left value to REG_A
        code.append("STORE_A 0")  # Store to temp location
        code.extend(right_code)  # Calculate right value to REG_A
        code.append("STORE_A 1")  # Store to another temp location
        code.append("LOAD_B_MEM 1")  # Load right value to REG_B
        code.append("LOAD_A_MEM 0")  # Load left value to REG_A
        code.append(operation)  # A = A op B
        return ["# General case: " + operation] + code


# Preprocessor for handling include directives
class Preprocessor:
    @staticmethod
    def process_includes(source_code, current_file=None, included_files=None):
        """
        Process #include directives by replacing them with file contents.
        Checks for circular includes to prevent infinite recursion.
        """
        if included_files is None:
            included_files = set()

        if current_file:
            included_files.add(os.path.abspath(current_file))

        lines = source_code.split('\n')
        result = []

        for line in lines:
            # Check for include directive
            if line.strip().startswith('#include'):
                # Extract the filename
                parts = line.strip().split('"')
                if len(parts) < 2:
                    raise Exception(f"Invalid include directive: {line}")

                include_file = parts[1]

                # Resolve the path relative to the current file
                if current_file:
                    include_path = os.path.join(os.path.dirname(current_file), include_file)
                else:
                    include_path = include_file

                include_path = os.path.abspath(include_path)

                # Check for circular inclusion
                if include_path in included_files:
                    raise Exception(f"Circular include detected: {include_path}")

                # Read the included file
                try:
                    with open(include_path, 'r') as f:
                        include_content = f.read()
                except FileNotFoundError:
                    raise Exception(f"Include file not found: {include_file}")

                # Recursively process includes in the included file
                processed_content = Preprocessor.process_includes(
                    include_content,
                    current_file=include_path,
                    included_files=included_files.copy()
                )

                # Add the processed content
                result.append(f"// Begin included file: {include_file}")
                result.append(processed_content)
                result.append(f"// End included file: {include_file}")
            else:
                # Regular line, just add it
                result.append(line)

        return '\n'.join(result)


# Main compiler class that orchestrates the compilation process
class Compiler:
    def __init__(self):
        self.parser = Lark(GrammarDefinition.get_grammar(), start='program', parser='lalr')

    def compile(self, source_code):
        tree = self.parser.parse(source_code)

        transformer = CompilerTransformer()
        instructions = transformer.transform(tree)

        # Generate symbol table information as comments
        symbol_table_comments = ["# Memory map:"]
        for var_name, address in sorted(transformer.symbol_table.get_symbols().items(), key=lambda x: x[1]):
            symbol_table_comments.append(f"# {var_name}: address {address}")

        # Add defined constants as comments
        if transformer.defined_constants:
            symbol_table_comments.append("\n# Defined constants:")
            for const_name, const_value in sorted(transformer.defined_constants.items()):
                symbol_table_comments.append(f"# {const_name}: {const_value}")

        symbol_table_comments.append("")  # Empty line

        # Return combined comments and code
        return '\n'.join(symbol_table_comments + instructions)

    def compile_with_includes(self, source_code, main_file=None):
        # First, process all includes
        processed_code = Preprocessor.process_includes(source_code, current_file=main_file)

        # Then compile using the existing compiler
        return self.compile(processed_code)


# Maintain the original interface functions for backward compatibility
def compile_code(source_code):
    compiler = Compiler()
    return compiler.compile(source_code)


def preprocess_includes(source_code, current_file=None, included_files=None):
    return Preprocessor.process_includes(source_code, current_file, included_files)


def compile_with_includes(source_code, main_file=None):
    compiler = Compiler()
    return compiler.compile_with_includes(source_code, main_file)
