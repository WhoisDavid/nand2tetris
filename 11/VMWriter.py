
class VMWriter:

    def __init__(self, file_path):
        self.output = open(file_path, 'w')

    def write(self, string):
        print(string, file=self.output)

    def writePush(self, segment, index):
        vm_cmd = "push {segment} {index}".format(segment=segment.value, index=index)
        self.write(vm_cmd)

    def writePop(self, segment, index):
        vm_cmd = "pop {segment} {index}".format(segment=segment.value, index=index)
        self.write(vm_cmd)

    def writeArithmetic(self, command):
        self.write(command.value)

    def writeLabel(self, label):
        self.write("label {0}".format(label))

    def writeGoto(self, label):
        self.write("goto {0}".format(label))

    def writeIf(self, label):
        self.write("if-goto {0}".format(label))

    def writeCall(self, name, nargs):
        self.write("call {0} {1}".format(name, nargs))

    def writeFunction(self, name, nlocals):
        self.write("function {0} {1}".format(name, nlocals))

    def writeReturn(self):
        self.write("return")

    def close(self):
        self.output.close()

