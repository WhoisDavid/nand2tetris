from enum import Enum
from collections import namedtuple


class Segments(Enum):
    LOCAL = 'local'
    ARGUMENT = 'argument'
    THIS = 'this'
    THAT = 'that'
    STATIC = 'static'
    CONSTANT = 'constant'
    POINTER = 'pointer'
    TEMP = 'temp'


class VariableKind(Enum):
    STATIC = Segments.STATIC
    FIELD = Segments.THIS
    ARG = Segments.ARGUMENT
    VAR = Segments.LOCAL
    NONE = 0


class SymbolTable:

    SYMBOL = namedtuple("Symbol", ["type", "kind", "scope"])

    def __init__(self):
        self.class_table = {}  # dict{name: SYMBOL}
        self.subroutine_table = {}  # dict{name: SYMBOL}
        self._varCount = {kind: 0 for kind in VariableKind}

    def startSubroutine(self):
        self.subroutine_table = {}
        self._varCount[VariableKind.VAR] = 0
        self._varCount[VariableKind.ARG] = 0

    def define(self, name, type_, kind):
        """
        :str name:
        :str type:
        :enum kind: STATIC, FIELD, ARG or VAR
        :return:
        """
        if not isinstance(kind, VariableKind):
            if isinstance(kind, Enum):
                kind = VariableKind[kind.value.upper()]  # converts KEYWORD to VariableKind
            else:
                raise TypeError("Expected VariableKind got {0} in '{1}'".format(type(kind), kind))

        if kind in (VariableKind.FIELD, VariableKind.STATIC):
            table = self.class_table

        if kind in (VariableKind.ARG, VariableKind.VAR):
            table = self.subroutine_table

        table[name] = self.SYMBOL(type_, kind, self._varCount[kind])
        self._varCount[kind] += 1

        return

    def varCount(self, kind):
        return self._varCount[kind]

    def __table(self, name):
        if name in self.subroutine_table:
            return self.subroutine_table

        if name in self.class_table:
            return self.class_table

    def lookup(self, name):
        table = self.__table(name)
        return table[name]

    def kindOf(self, name):
        table = self.__table(name)
        return table[name].kind

    def typeOf(self, name):
        table = self.__table(name)
        if table:
            return table[name].type
        else:
            return None

    def indexOf(self, name):
        table = self.__table(name)
        return table[name].scope

    def segmentOf(self, name):
        return self.kindOf(name).value
