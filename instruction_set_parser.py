REG_A = 0
REG_B = 1
TEMP = 2


class Parser:
    def __init__(self, debug=False):
        self.instruction_handlers = {
            "LOAD_A_IMM": self._handle_load_immediate,
            "LOAD_A_MEM": self._handle_load_memory,
            "LOAD_B_IMM": self._handle_load_immediate,
            "LOAD_B_MEM": self._handle_load_memory,
            "STORE_A": self._handle_store,
            "STORE_B": self._handle_store,
            "ADD": self._handle_arithmetic,
            "SUB": self._handle_arithmetic,
            "LOOP_START": self._handle_loop_start,
            "LOOP_END": self._handle_loop_end,
            "IN_A": self._handle_input,
            "IN_B": self._handle_input,
            "OUT_A": self._handle_output,
            "OUT_B": self._handle_output,
        }
        self.loop_stack = []  # For tracking nested loops
        self.cursor = 0
        self.memory_offset = 3  # Start memory address for user data (reg_a, reg_b, temp)
        self.debug = "#" if debug else ""

    def parse(self, instructions: str) -> str:
        code = ""
        self.rows = instructions.strip().split("\n")

        for i, row in enumerate(self.rows):
            row = row.strip()
            if not row or row.startswith("#"):  # Skip empty lines and comments
                continue

            # Extract instruction and arguments
            parts = row.split()
            instruction = parts[0]
            args = parts[1:] if len(parts) > 1 else []

            # Call the appropriate handler
            if instruction in self.instruction_handlers:
                result = self.instruction_handlers[instruction](instruction, args)
                if result:
                    code += result + self.debug + "\n"
            else:
                raise ValueError(f"Error: Unknown instruction '{instruction}' at line {i}")

        return self._remove_redundant_instructions(code)

    def _remove_redundant_instructions(self, code):
        # Remove redundant instructions by simplifying cursor movements
        # "<<<>" -> "<<"
        # ">>><" -> ">>"

        while True:
            new_code = code.replace("<>", "").replace("><", "")
            if new_code == code:
                break
            code = new_code

        return code

    def _move_to(self, cell) -> str:
        code = ">" * (cell - self.cursor) if cell > self.cursor else "<" * (self.cursor - cell)
        self.cursor = cell
        return code

    def _move_offset(self, offset) -> str:
        code = ">" * offset if offset > 0 else "<" * abs(offset)
        self.cursor += offset
        return code

    def _clear_cell(self, register) -> str:
        return self._move_to(register) + "[-]"

    def _copy_value(self, source, destination) -> str:
        code = self._clear_cell(TEMP)
        code += self._clear_cell(destination)
        code += self._move_to(source)
        # Move the value to the destination cell and a temporary cell
        code += "[" + self._move_offset(destination - source) + "+" + self._move_offset(
            TEMP - destination) + "+" + self._move_offset(source - TEMP) + "-]"
        # Move the temporary cell back to the source cell
        code += self._move_to(TEMP)
        code += "[" + self._move_offset(source - TEMP) + "+" + self._move_offset(TEMP - source) + "-]"
        return code

    def _handle_load_immediate(self, instruction, args) -> str:
        register = REG_A if instruction.startswith("LOAD_A") else REG_B
        value = args[0]
        code = self._move_to(register)
        code += "[-]"  # Clear the current cell
        code += "+" * int(value)  # Increment the cell by the value
        return code

    def _handle_load_memory(self, instruction, args):
        register = REG_A if instruction.startswith("LOAD_A") else REG_B
        address = int(args[0]) + self.memory_offset

        return self._copy_value(address, register)

    def _handle_store(self, instruction, args):
        register = REG_A if instruction == "STORE_A" else REG_B
        address = int(args[0]) + self.memory_offset

        return self._copy_value(register, address)

    def _handle_arithmetic(self, instruction, args):
        if instruction == "ADD":
            code = self._move_to(REG_B)
            code += "[" + self._move_offset(REG_A - REG_B) + "+" + self._move_offset(REG_B - REG_A) + "-]"
            return code
        else:
            code = self._move_to(REG_B)
            code += "[" + self._move_offset(REG_A - REG_B) + "-" + self._move_offset(REG_B - REG_A) + "-]"
            return code

    def _handle_loop_start(self, instruction, args):
        return self._move_to(REG_A) + "["

    def _handle_loop_end(self, instruction, args):
        return self._move_to(REG_A) + "]"

    def _handle_input(self, instruction, args):
        register = REG_A if instruction == "IN_A" else REG_B

        code = self._move_to(register)
        code += ","
        return code

    def _handle_output(self, instruction, args):
        register = REG_A if instruction == "OUT_A" else REG_B

        code = self._move_to(register)
        code += "."
        return code
