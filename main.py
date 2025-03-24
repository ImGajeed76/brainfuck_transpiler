from instruction_set_parser import Parser
from lark_parser import compile_code

# load code.bfs
with open("code.bfs") as f:
    # read complete file into one string with \n as separator
    code = f.read()

instructions = compile_code(code)

parser = Parser(debug=False)
code = parser.parse(instructions)

print(code)

# write code to output.bf
with open("output.bf", "w") as f:
    f.write(code)