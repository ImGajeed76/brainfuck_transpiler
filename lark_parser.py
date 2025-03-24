from lark import Lark, Transformer, Token

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
        | "(" expression ")" -> parenthesized

    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
    NUMBER: /[0-9]+/

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

    # Add comments for special memory addresses
    symbol_table_comments.append(f"# Address 0: Temporary storage for operations")
    symbol_table_comments.append(f"# Address 255: Temporary storage for operations")
    symbol_table_comments.append("")  # Empty line

    # Return combined comments and code
    return '\n'.join(symbol_table_comments + instructions)

