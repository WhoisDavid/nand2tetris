import sys
import os
import subprocess
from CompilationEngine import CompilationEngine
import argparse


class Main:

    def __init__(self, cli_input):
        if os.path.isdir(cli_input):
            if cli_input.endswith("/"):
                cli_input = cli_input[:-1]
            self.base_path = cli_input
            self.input_files = [file for file in os.listdir(cli_input) if file.endswith(".jack")]
        else:
            self.base_path = os.path.dirname(cli_input)
            self.input_files = [os.path.basename(cli_input)]

    def absolute_path(self, file):
        return os.path.join(self.base_path, file)

    def run(self, print_xml=False, debug=False):
        for input_file in self.input_files:
            output_file = input_file[:-5]
            input_path = self.absolute_path(input_file)
            output_path = self.absolute_path(output_file)
            CompilationEngine(input_path, output_path, print_xml=print_xml)

            if debug:
                print(subprocess.check_output(["./TextComparer.sh", output_path + '.vmComp', output_path + ".vm"], stderr=subprocess.STDOUT))

        return self.base_path


def main():
    parser = argparse.ArgumentParser(description='Jack Compiler - jack to xml/vm')
    parser.add_argument("path", help="Jack file or directory containing jack code", type=str)
    parser.add_argument("-t", "--test", help="test the output against compiled vm files", action='store_true')
    parser.add_argument("--xml", help="Print the output of the Analyzer to xml files", action='store_true')

    args = parser.parse_args()

    print("Running Jack Compiler...")
    print(args.path)
    output = Main(args.path).run(print_xml=args.xml, debug=args.test)
    print("Done!")
    print("See vm files results in: {0}".format(output))


if __name__ == "__main__":
    main()
