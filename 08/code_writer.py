from enum import Enum
from parser import CommandTypes


class MemorySegments(Enum):
    LOCAL = 'LCL'
    ARGUMENT = 'ARG'
    THIS = 'THIS'
    THAT = 'THAT'
    STATIC = 'static'
    CONSTANT = 'constant'
    POINTER = 3
    TEMP = 5


class CodeWriter:

    def __init__(self, filepath, sys_init=True):
        self.filepath = filepath
        self.file = open(self.filepath, 'w')
        self.filename = ""
        self.label_counter = 0
        self.function_counter = 0
        self.function_name = ""
        if sys_init:
            self.writeInit()

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

        __segment = MemorySegments[segment.upper()]
        asm = ""
        if command == CommandTypes.C_POP:
            if __segment == MemorySegments.STATIC:
                asm = self.__pop_static(index)
            else:  # all implementations are equivalent for local/arg/this/that/temp/pointer
                asm = self.__pop(__segment, index)

        if command == CommandTypes.C_PUSH:
            if __segment == MemorySegments.CONSTANT:
                asm = self.__push_constant(index)
            elif __segment == MemorySegments.STATIC:
                asm = self.__push_static(index)
            else:
                asm = self.__push(__segment, index)

        self.writeOut(original_command="{0} {1} {2}".format(command.name[2:].lower(), segment, index),
                      assembly=asm)

    def close(self):
        self.file.close()

    def setFileName(self, filename):  # do not understand the use of this method
        self.filename = filename

    def writeInit(self):
        asm = """
        @256
        D=A
        @SP
        M=D
        {call_sys}
        """.format(call_sys=self.__callFunction("Sys.init", 0))

        self.writeOut(original_command="init", assembly=asm)

    def writeLabel(self, label):
        original_command = "label {0}".format(label)
        asm = self.__label(label)
        self.writeOut(original_command=original_command, assembly=asm)

    def writeGoto(self, label):
        original_command = "goto {0}".format(label)
        asm = self.__goto(label)
        self.writeOut(original_command=original_command, assembly=asm)

    def writeIf(self, label):
        original_command = "if-goto {0}".format(label)
        asm = self.__ifgoto(label)
        self.writeOut(original_command=original_command, assembly=asm)

    def writeFunction(self, functionName, nVars):
        original_command = "function {0} {1}".format(functionName, nVars)
        self.function_name = ""
        asm = self.__function(functionName, nVars)
        self.writeOut(original_command=original_command, assembly=asm)
        self.function_name = functionName

    def writeCall(self, functionName, nArgs):
        original_command = "call {0} {1}".format(functionName, nArgs)
        # self.function_name = ""
        asm = self.__callFunction(functionName, nArgs)
        self.writeOut(original_command=original_command, assembly=asm)

    def writeReturn(self):
        original_command = "return"
        # self.function_name = ""
        asm = self.__return()
        self.writeOut(original_command=original_command, assembly=asm)

    # region functions
    def __callFunction(self, functionName, nArgs):
        """call functionName nargs

            push returnAddress
            push LCL  // begin save Frame
            push ARG
            push THIS
            push THAT // end save Frame
            ARG = SP - 5 - nargs // set arg0
            LCL = SP  //
            goto functionName
            (returnAddress) // push the label
        """
        self.function_counter += 1
        return_address = "{0}.{1}.{2}".format("return_addr_of", functionName, self.function_counter)

        return """
                // save frame
                @{return_addr}
                D=A
                {push_to_stack}
                
                @LCL
                D=M
                {push_to_stack}
                
                @ARG
                D=M
                {push_to_stack}
                
                @THIS
                D=M
                {push_to_stack}
                
                @THAT
                D=M
                {push_to_stack}
                
                @{nArgsp5} // ARG = SP - (nArgs + 5)
                D=A
                @SP
                D=M-D
                @ARG
                M=D
                
                @SP  // LCL = SP
                D=M
                @LCL
                M=D
                
                @{function_name} // goto function
                0; JMP
                {return_label}
                """.format(return_addr=self.__label_name(return_address),
                           function_name=functionName,
                           function_counter=self.function_counter,
                           push_to_stack=self.__push_to_stack(),
                           nArgsp5=nArgs + 5,
                           return_label=self.__label(return_address))

    def __function(self, functionName, nVars):
        """
        (functionName) // label
        repeat nVars times:
            push 0 // initialize
        """
        return """
                {function_label}
                {pushes}
                """.format(function_label=self.__label(functionName),
                           pushes=nVars * self.__push_to_stack(0))

    @staticmethod
    def __restore_frame_el(segment, shift, end_frame):
        return """
                @{shift} // {destination} = *(endFrame - {shift})
                D=A
                @{end_frame}
                A=M-D
                D=M
                @{destination}
                M=D
                """.format(shift=shift,
                           end_frame=end_frame,
                           destination=segment)

    def __return(self):
        """
        endFrame=LCL  // endFrame = temp var
        retAddr = *(endFrame - 5) // return address
        *ARG=pop()
        SP = ARG + 1
        THAT = *(endFrame - 1)
        THIS = *(endFrame - 2)
        ARG = *(endFrame - 3)
        LCL = *(endFrame - 4)
        goto retAddr
        """

        end_frame = "R13"
        return_address = "R14"

        return """
                @LCL // endFrame = LCL
                D=M
                @{end_frame}  // end_frame in {end_frame}
                M=D
                
                {restore_return} // return stored in {return_address}
                
                {pop_arg0_tostack}
                
                @ARG
                D=M
                @SP
                M=D+1
                
                {restore_THAT}
                {restore_THIS}
                {restore_ARG}
                {restore_LCL}
                
                @{return_address}
                A=M
                0; JMP
        
                """.format(end_frame=end_frame,
                           restore_return=self.__restore_frame_el(return_address, 5, end_frame),
                           pop_arg0_tostack=self.__pop(MemorySegments.ARGUMENT, 0),
                           restore_THAT=self.__restore_frame_el("THAT", 1, end_frame),
                           restore_THIS=self.__restore_frame_el("THIS", 2, end_frame),
                           restore_ARG=self.__restore_frame_el("ARG", 3, end_frame),
                           restore_LCL=self.__restore_frame_el("LCL", 4, end_frame),
                           return_address=return_address
                           )
    # endregion

    # region branching

    def __label_name(self, label):
        if self.function_name:
            return "{0}${1}".format(self.function_name, label)
        # elif self.filename:
        #     return "{0}.{1}".format(self.filename, label)
        else:
            return label

    def __label(self, label):
        return """
                ({label})
                """.format(label=self.__label_name(label))

    def __goto(self, label):
        return """
                @{label}
                0; JMP
                """.format(label=self.__label_name(label))

    def __ifgoto(self, label):
        return """
                {pop_stack}
                @{label}
                D; JNE
                """.format(pop_stack=self.__pop_stack(),
                           label=self.__label_name(label))
    # endregion

    # region arithmetic private
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
                @{true_label}.{label_counter}
                D; {jump}
                   
                D=0
                @END.{label_counter}
                0; JMP
                ({true_label}.{label_counter})
                D=-1
            
                (END.{label_counter})
                {push_to_stack}
                """.format(pop_stack=self.__pop_stack(),
                           true_label=self.__label_name("TRUE"),
                           jump=jump,
                           label_counter=self.label_counter,
                           push_to_stack=self.__push_to_stack())

    # endregion

    # region memory segments push pop private
    @staticmethod
    def __pop_stack():
        return """
                // pop stack
                @SP
                AM=M-1
                D=M
                """

    def __segment_address(self, segment, index, var_name):
        return """
                @{segment} // D = {segment}
                D={MorA}
                @{index} // D = {segment}+{index}
                D=D+A
                @{var_name} // {var_name} = {segment} + {index}
                M=D
                """.format(MorA=('A' if isinstance(segment.value, int) else 'M'),
                           segment=segment.value,
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
    def __push_to_stack(val="D"):
        return """
                // push to stack
                @SP
                A=M
                M={val}
                @SP // SP++
                M=M+1
                """.format(val=val)

    def __push_constant(self, index):
        """
        *SP = {index}
        SP++
        """
        return """
                @{index} // D = {index}
                D=A
                {push_to_stack}
                """.format(index=index,
                           push_to_stack=self.__push_to_stack())

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

    # endregion

    _end = ""
