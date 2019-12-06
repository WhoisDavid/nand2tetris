import parser as p
import code_writer as cw
import sys
import os

from parser import CommandTypes

class Main:

    def __init__(self, cli_input):
        if os.path.isdir(cli_input):
            if cli_input.endswith("/"):
                cli_input = cli_input[:-1]
            self.base_path = cli_input
            self.input_files = [file for file in os.listdir(cli_input) if file.endswith(".vm")]
            dir_name = os.path.basename(cli_input)
            self.output_file = dir_name + ".asm"
            sys_init = "Sys.vm" in self.input_files
        else:
            self.base_path = os.path.dirname(cli_input)
            self.input_files = [os.path.basename(cli_input)]
            self.output_file = self.input_files[0][:-2] + "asm"
            sys_init = False

        output_filepath = self.absolute_path(self.output_file)
        self.writer = cw.CodeWriter(output_filepath, sys_init=sys_init)

    def absolute_path(self, file):
        return os.path.join(self.base_path, file)

    def run(self, debug=False):

        for input_file in self.input_files:

            parser = p.Parser(self.absolute_path(input_file))
            self.writer.setFileName(input_file[:-3])

            while parser.hasMoreCommands():
                parser.advance()
                if debug:
                    print(parser.current_command)

                command_type = parser.commandType()
                arg1 = parser.arg1()
                arg2 = parser.arg2()
                if command_type == CommandTypes.C_ARITHMETIC:
                    self.writer.writeArithmetic(arg1)
                elif command_type == CommandTypes.C_LABEL:
                    self.writer.writeLabel(arg1)
                elif command_type == CommandTypes.C_GOTO:
                    self.writer.writeGoto(arg1)
                elif command_type == CommandTypes.C_IF:
                    self.writer.writeIf(arg1)
                elif command_type == CommandTypes.C_FUNCTION:
                    self.writer.writeFunction(arg1, arg2)
                elif command_type == CommandTypes.C_CALL:
                    self.writer.writeCall(arg1, arg2)
                elif command_type == CommandTypes.C_RETURN:
                    self.writer.writeReturn()
                else:
                    self.writer.writePushPop(command_type, arg1, arg2)

        self.writer.close()

        return self.output_file


def main():
    if len(sys.argv) < 2:
        print("python VMTranslator.py [-q] file|folder")
        sys.exit(0)

    arg1 = sys.argv[1]
    if arg1 == "-q":
        arg2 = sys.argv[2]
        output = Main(arg2).run(debug=False)
    else:
        print("Running vm translator...")
        output = Main(arg1).run(debug=True)
        print("Done!")

    print("Translated to file: {0}".format(output))


if __name__ == "__main__":
    main()