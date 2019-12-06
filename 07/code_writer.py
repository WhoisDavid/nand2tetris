# from enum import Enum
#
# class Segments(Enum):
#     LCL
from parser import CommandTypes

import parser


class CodeWriter:

    def __init__(self, filepath):
        self.filepath = filepath
        self.file = open(self.filepath, 'w')
        self.filename = ""
        self.label_counter = 0

    def setFileName(self, filename):  # do not understand the use of this method
        self.filename = filename
        self.label_counter = 0

    def writeOut(self, original_command, assembly):
        self.file.write("\n// {0}\n".format(original_command))
        assembly = "\n".join([x for x in assembly.splitlines() if x])
        self.file.write(assembly)

    def writeArithmetic(self, command):
        if command in self.__unary_ops_map:
            op = self.__unary_ops_map[command]
            asm = self.__arithmetic_1_arg(op)
        elif command in self.__ops_map:
            op = self.__ops_map[command]
            asm = self.__arithmetic_2_args(op)
        else:
            asm = self.__arithmetic_jump(jump="J{0}".format(command.upper()))

        self.writeOut(original_command=command,
                      assembly=asm)

    def writePushPop(self, command, segment, index):

        asm = ""
        if command == parser.CommandTypes.C_POP:
            if segment == 'static':
                asm = self.__pop_static(index)
            else:  # all implementations are equivalent for local/arg/this/that/temp/pointer
                asm = self.__pop(segment, index)

        if command == parser.CommandTypes.C_PUSH:
            if segment == 'constant':
                asm = self.__push_constant(index)
            elif segment == 'static':
                asm = self.__push_static(index)
            else:
                asm = self.__push(segment, index)

        self.writeOut(original_command="{0} {1} {2}".format(command.name[2:].lower(), segment, index),
                      assembly=asm)

    def close(self):
        self.file.close()

    def __arithmetic_1_arg(self, op):
        return """
        {pop_stack}
        D={op}D
        {push_to_stack}
        """.format(pop_stack=self.__pop_stack(), op=op, push_to_stack=self.__push_to_stack())

    def __arithmetic_2_args(self, op):
        return """
        {pop_stack}
        @y
        M=D
        {pop_stack}
        @y
        D=D{op}M
        {push_to_stack}
        """.format(pop_stack=self.__pop_stack(), op=op, push_to_stack=self.__push_to_stack())

    def __arithmetic_jump(self, jump):
        self.label_counter += 1
        return """
        {pop_stack}
        @y
        M=D
        {pop_stack}
        @y
        D=D-M
        @TRUE{unique}
        D; {jump}
           
        D=0
        @END{unique}
        0; JMP
        (TRUE{unique})
        D=-1
  
        (END{unique})
        {push_to_stack}
        """.format(pop_stack=self.__pop_stack(), jump=jump, unique=self.label_counter, push_to_stack=self.__push_to_stack())

    # MEMORY SEGMENTS
    @staticmethod
    def __pop_stack():
        return """// pop stack
        @SP
        AM=M-1
        D=M
        """

    def __segment_address(self, segment, index, var_name):
        segment_label = self.__segments_map[segment]
        return """
        @{segment} // D = {segment}
        D={MorA}
        @{index} // D = {segment}+{index}
        D=D+A
        @{var_name} // {var_name} = {segment} + {index}
        M=D
        """.format(MorA=('A' if isinstance(segment_label, int) else 'M'),
                   segment=segment_label,
                   index=index,
                   var_name=var_name,
                   pop_stack=self.__pop_stack())

    def __pop(self, segment, index):
        var_name = "addr"
        return """
        {segment_addr}
        {pop_stack}
        @{var_name}
        A=M
        M=D
        """.format(segment_addr=self.__segment_address(segment, index, var_name),
                   var_name=var_name,
                   pop_stack=self.__pop_stack())

    def __pop_static(self, index):
        return """
        {pop_stack}
        @{filename}.{index}
        M=D
        """.format(pop_stack=self.__pop_stack(), filename=self.filename, index=index)

    @staticmethod
    def __push_to_stack():
        return """// push to stack
        @SP
        A=M
        M=D
        @SP // SP++
        M=M+1
        """

    def __push_constant(self, index):
        """
        *SP = {index}
        SP++
        """
        return """
        @{index} // D = {index}
        D=A
        {push_to_stack}""".format(index=index, push_to_stack=self.__push_to_stack())

    def __push(self, segment, index):
        """
        addr = [LCL|ARG|THIS|THAT]+i
        *SP = *addr
        SP++
        """
        var_name = "addr"
        return """
        {segment_addr}
        @{var_name}
        A=M
        D=M // D = *{var_name}
        {push_to_stack}
        """.format(segment_addr=self.__segment_address(segment, index, var_name),
                   var_name=var_name,
                   push_to_stack=self.__push_to_stack())

    def __push_static(self, index):
        return """
        @{filename}.{index}
        D=M
        {push_to_stack}
        """.format(filename=self.filename, index=index, push_to_stack=self.__push_to_stack())

    __segments_map = {
        "local": "LCL",
        "argument": "ARG",
        "this": "THIS",
        "that": "THAT",
        "pointer": 3,
        "temp": 5
    }

    __unary_ops_map = {
        "neg": "-",
        "not": "!"
    }
    __ops_map = {
        "add": "+",
        "sub": "-",
        "and": "&",
        "or": "|"
    }
