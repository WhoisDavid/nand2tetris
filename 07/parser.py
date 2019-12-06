from enum import Enum


class CommandTypes(Enum):
    C_ARITHMETIC, C_PUSH, C_POP, C_LABEL, C_GOTO, C_IF, C_FUNCTION, C_CALL, C_RETURN = 1, 2, 3, 4, 5, 6, 7, 8, 9


class Parser:

    def __init__(self, filepath):
        self.filepath = filepath
        self.file = open(self.filepath, 'r')
        self.current_command = []
        self.next_command = self.file.readline()

    @staticmethod
    def __sanitize(line):
        return line.split("//")[0].strip()

    def hasMoreCommands(self):
        """
        Are there more commands in the input?
        :rtype: boolean
        """
        return bool(self.next_command)

    def advance(self):
        if self.hasMoreCommands():
            while not self.__sanitize(self.next_command):
                self.next_command = self.file.readline()
            self.current_command = self.__sanitize(self.next_command).split()
            self.next_command = self.file.readline()
        else:
            self.file.close()

    def commandType(self):
        return self.command_type_map[self.current_command[0]]

    def arg1(self):
        if self.commandType() == CommandTypes.C_RETURN:
            return None
        if self.commandType() == CommandTypes.C_ARITHMETIC:
            return self.current_command[0]

        return self.current_command[1]

    def arg2(self):
        if self.commandType() in (CommandTypes.C_PUSH, CommandTypes.C_POP, CommandTypes.C_FUNCTION, CommandTypes.C_CALL):
            return int(self.current_command[2])

    command_type_map = {
        "push": CommandTypes.C_PUSH,
        "pop": CommandTypes.C_POP,
        "add": CommandTypes.C_ARITHMETIC,
        "sub": CommandTypes.C_ARITHMETIC,
        "neg": CommandTypes.C_ARITHMETIC,
        "eq": CommandTypes.C_ARITHMETIC,
        "gt": CommandTypes.C_ARITHMETIC,
        "lt": CommandTypes.C_ARITHMETIC,
        "and": CommandTypes.C_ARITHMETIC,
        "or": CommandTypes.C_ARITHMETIC,
        "not": CommandTypes.C_ARITHMETIC,
        "label": CommandTypes.C_LABEL,
        "goto": CommandTypes.C_GOTO,
        "if-goto": CommandTypes.C_IF,
        "function": CommandTypes.C_FUNCTION,
        "call": CommandTypes.C_CALL,
        "return": CommandTypes.C_RETURN
    }
