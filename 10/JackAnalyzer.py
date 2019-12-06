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

        self.suffix = ".xml"

    def absolute_path(self, file):
        return os.path.join(self.base_path, file)

    def run(self, debug=False):
        for input_file in self.input_files:
            output_file = input_file[:-5] + self.suffix
            input_path = self.absolute_path(input_file)
            output_path = self.absolute_path(output_file)
            ce = CompilationEngine(input_path, output_path)
            ce.output.close()

            if debug:
                print(subprocess.check_output(["./TextComparer.sh", output_path, output_path[:-len(self.suffix)] + ".xml"], stderr=subprocess.STDOUT))

        return self.base_path


def main():
    parser = argparse.ArgumentParser(description='Jack Analyzer - jack to xml')
    parser.add_argument("path", help="Jack file or directory containing jack code", type=str)
    parser.add_argument("-t", "--test", help="test the output against provided xml files", action='store_true')

    args = parser.parse_args()

    print("Running Jack Analyzer...")
    print(args.path)
    output = Main(args.path).run(debug=args.test)
    print("Done!")
    print("See xml files results in: {0}".format(output))


if __name__ == "__main__":
    main()