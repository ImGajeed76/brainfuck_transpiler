import os

from lark import Lark, Transformer

# Grammar definition using Lark
grammar = r"""
    program: statement+

    statement: variable_declaration
             | assignment
             | input_statement
             | output_statement
             | while_statement
             | expression ";"

    variable_declaration: "var" IDENTIFIER "=" expression ";"

    assignment: IDENTIFIER "=" expression ";"

    input_statement: "input" "(" IDENTIFIER ")" ";"

    output_statement: "output" "(" expression ")" ";"

    while_statement: "while" "(" expression ")" "{" statement+ "}"

    expression: term
              | expression "+" term -> add
              | expression "-" term -> subtract

    term: IDENTIFIER -> variable
        | NUMBER -> number
        | CHARACTER -> character
        | "(" expression ")" -> parenthesized

    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
    NUMBER: /[0-9]+/
    CHARACTER: /'(\\.|[^\\'])'/ 

    COMMENT: /\/\/[^\n]*/ | /\/\*.*?\*\//s

    %import common.WS
    %ignore WS
    %ignore COMMENT
"""


class OptimizedCompiler(Transformer):
    def __init__(self):
        super().__init__()
        self.symbol_table = {}  # Maps variable names to memory addresses
        self.next_address = 1  # Start at address 1, leaving 0 for temp storage

    def program(self, statements):
        # Combine all generated code
        result = []
        for stmt in statements:
            if stmt:  # Some statements might return None
                result.extend(stmt)
        return result

    def statement(self, items):
        # Handle statements that might be nested in while loops
        if len(items) == 1:
            return items[0]
        return items

    def character(self, items):
        # Get the character literal with quotes
        char_token = items[0].value

        # Extract the actual character (removing the quotes)
        # Handle escaped characters if needed
        if len(char_token) == 3:  # Simple case: 'A'
            char = char_token[1]
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
            char = escape_map.get(escaped_seq, escaped_seq[1])

        # Convert to ASCII value
        ascii_value = ord(char)

        # Ensure it fits in 8 bits
        if ascii_value < 0 or ascii_value > 255:
            raise Exception(f"ASCII value {ascii_value} out of range for 8-bit processor")

        return [f"LOAD_A_IMM {ascii_value}"]

    def variable_declaration(self, items):
        var_name = items[0].value
        expr_code = items[1]

        # Allocate memory for the variable
        address = self.next_address
        self.next_address += 1
        self.symbol_table[var_name] = address

        # Generate code to evaluate expression and store it
        code = expr_code.copy()  # Expression result will be in REG_A
        code.append(f"STORE_A {address}")
        return code

    def assignment(self, items):
        var_name = items[0].value
        expr_code = items[1]

        if var_name not in self.symbol_table:
            raise Exception(f"Undefined variable: {var_name}")

        address = self.symbol_table[var_name]

        # Generate code to evaluate expression and store it
        code = expr_code.copy()  # Expression result will be in REG_A
        code.append(f"STORE_A {address}")
        return code

    def input_statement(self, items):
        var_name = items[0].value

        if var_name not in self.symbol_table:
            raise Exception(f"Undefined variable: {var_name}")

        address = self.symbol_table[var_name]

        code = [
            "IN_A",
            f"STORE_A {address}"
        ]
        return code

    def output_statement(self, items):
        expr_code = items[0]

        code = expr_code.copy()  # Expression result will be in REG_A
        code.append("OUT_A")
        return code

    def while_statement(self, items):
        condition_code = items[0]
        body_statements = items[1:]

        # Collect all statement code in the body
        body_code = []
        for stmt in body_statements:
            if stmt:  # Some statements might return None
                body_code.extend(stmt)

        code = condition_code.copy()  # Condition result will be in REG_A
        code.append("LOOP_START")
        code.extend(body_code)
        code.extend(condition_code)  # Re-evaluate condition
        code.append("LOOP_END")

        return code

    def _is_simple_expression(self, code):
        """Check if this is a simple expression (one instruction)"""
        return len(code) == 1 and (
                code[0].startswith("LOAD_A_IMM") or
                code[0].startswith("LOAD_A_MEM")
        )

    def add(self, items):
        left_code = items[0]
        right_code = items[1]

        # Optimization for common cases
        if self._is_simple_expression(right_code):
            if right_code[0].startswith("LOAD_A_IMM"):
                # If right operand is immediate, extract the value
                value = right_code[0].split()[1]
                code = left_code.copy()  # Load left value to REG_A
                code.append(f"LOAD_B_IMM {value}")  # Load right value to REG_B
                code.append("ADD")  # A = A + B
                return code

            if right_code[0].startswith("LOAD_A_MEM"):
                # If right operand is a memory reference
                address = right_code[0].split()[1]
                code = left_code.copy()  # Load left value to REG_A
                code.append(f"LOAD_B_MEM {address}")  # Load right value to REG_B
                code.append("ADD")  # A = A + B
                return code

        # Fall back to general case
        code = left_code.copy()  # Load left value to REG_A
        code.append("STORE_A 0")  # Store to temp location
        code.extend(right_code)  # Calculate right value to REG_A
        code.append("STORE_A 255")  # Store to another temp location
        code.append("LOAD_B_MEM 255")  # Load right value to REG_B
        code.append("LOAD_A_MEM 0")  # Load left value to REG_A
        code.append("ADD")  # A = A + B
        return code

    def subtract(self, items):
        left_code = items[0]
        right_code = items[1]

        # Optimization for common cases
        if self._is_simple_expression(right_code):
            if right_code[0].startswith("LOAD_A_IMM"):
                # If right operand is immediate, extract the value
                value = right_code[0].split()[1]
                code = left_code.copy()  # Load left value to REG_A
                code.append(f"LOAD_B_IMM {value}")  # Load right value to REG_B
                code.append("SUB")  # A = A - B
                return code

            if right_code[0].startswith("LOAD_A_MEM"):
                # If right operand is a memory reference
                address = right_code[0].split()[1]
                code = left_code.copy()  # Load left value to REG_A
                code.append(f"LOAD_B_MEM {address}")  # Load right value to REG_B
                code.append("SUB")  # A = A - B
                return code

        # Fall back to general case
        code = left_code.copy()  # Load left value to REG_A
        code.append("STORE_A 0")  # Store to temp location
        code.extend(right_code)  # Calculate right value to REG_A
        code.append("STORE_A 255")  # Store to another temp location
        code.append("LOAD_B_MEM 255")  # Load right value to REG_B
        code.append("LOAD_A_MEM 0")  # Load left value to REG_A
        code.append("SUB")  # A = A - B
        return code

    def variable(self, items):
        var_name = items[0].value

        if var_name not in self.symbol_table:
            raise Exception(f"Undefined variable: {var_name}")

        address = self.symbol_table[var_name]
        return [f"LOAD_A_MEM {address}"]

    def number(self, items):
        value = int(items[0].value)
        if value < 0 or value > 255:
            raise Exception(f"Value {value} out of range for 8-bit processor")

        return [f"LOAD_A_IMM {value}"]

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


def compile_code(source_code):
    parser = Lark(grammar, start='program', parser='lalr')
    tree = parser.parse(source_code)

    compiler = OptimizedCompiler()
    instructions = compiler.transform(tree)

    # Generate symbol table information as comments
    symbol_table_comments = ["# Memory map:"]
    for var_name, address in sorted(compiler.symbol_table.items(), key=lambda x: x[1]):
        symbol_table_comments.append(f"# {var_name}: address {address}")

    symbol_table_comments.append("")  # Empty line

    # Return combined comments and code
    return '\n'.join(symbol_table_comments + instructions)


def preprocess_includes(source_code, current_file=None, included_files=None):
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
            processed_content = preprocess_includes(
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


def compile_with_includes(source_code, main_file=None):
    """
    Compile source code with include directive support.
    """
    # First, process all includes
    processed_code = preprocess_includes(source_code, current_file=main_file)

    # Then compile using the existing compiler
    return compile_code(processed_code)
