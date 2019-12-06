import parser
import code_writer
import sys


class Main:

    def __init__(self, input_file):
        self.parser = parser.Parser(input_file)
        output_filepath = ".".join(input_file.split(".")[:-1])
        self.code_writer = code_writer.CodeWriter(output_filepath + ".asm")
        filename = output_filepath.split("/")[-1]
        self.code_writer.setFileName(filename)

    def run(self):
        while self.parser.hasMoreCommands():
            self.parser.advance()
            print(self.parser.current_command)
            if self.parser.commandType() == parser.CommandTypes.C_ARITHMETIC:
                self.code_writer.writeArithmetic(self.parser.arg1())
            else:
                self.code_writer.writePushPop(self.parser.commandType(), self.parser.arg1(), self.parser.arg2())
        self.code_writer.close()

        return self.code_writer.filename + ".asm"


def main():
    if len(sys.argv) < 2:
        print("python vm_translator.py Xxx.vm")
        sys.exit(0)

    file = sys.argv[1]
    if not file.endswith(".vm"):
        print("Files need to be of type vm (extension .vm)")
        sys.exit(0)

    print("Running assembler...")
    output = Main(file).run()
    print("Done!")
    print("Created file: {0}".format(output))


if __name__ == "__main__":
    main()