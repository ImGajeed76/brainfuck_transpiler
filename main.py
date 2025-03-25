import argparse

from instruction_set_parser import Parser
from lark_parser import compile_with_includes


def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Compile BFS code to BF code')
    parser.add_argument('input_file', nargs='?', default='main.bfs',
                        help='Input file (default: main.bfs)')
    parser.add_argument('-o', '--output', dest='output_file',
                        help='Output file (default: derived from input filename)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode and generate instructions.txt')

    args = parser.parse_args()

    # Determine output filename if not specified
    if not args.output_file:
        # Replace .bfs extension with .bf, or just append .bf if no .bfs
        if args.input_file.endswith('.bfs'):
            output_filename = args.input_file[:-4] + '.bf'
        else:
            output_filename = args.input_file + '.bf'
    else:
        output_filename = args.output_file

    # Load and compile code
    with open(args.input_file) as f:
        code = f.read()

    instructions = compile_with_includes(code, args.input_file)

    # Save intermediate instructions only in debug mode
    if args.debug:
        # Format instructions for debugging
        indent_cnt = 0
        formatted_instructions = []
        for line in instructions.split("\n"):
            if line.startswith("LOOP_END"):
                indent_cnt -= 1
            formatted_instructions.append("    " * indent_cnt + line)
            if line.startswith("LOOP_START"):
                indent_cnt += 1

        with open("instructions.bfi", "w") as f:
            f.write("\n".join(formatted_instructions))
        print("Debug: Intermediate instructions written to instructions.bfi")

    # Parse instructions with debug flag
    instruction_parser = Parser(debug=args.debug)
    compiled_code = instruction_parser.parse(instructions)

    # Write output
    with open(output_filename, "w") as f:
        f.write(compiled_code)

    print(f"Compilation complete. Output written to {output_filename}")


if __name__ == "__main__":
    main()
