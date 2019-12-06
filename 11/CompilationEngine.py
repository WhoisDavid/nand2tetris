from JackTokenizer import JackTokenizer, TokenType, Keyword
from SymbolTable import SymbolTable, VariableKind, Segments
from VMWriter import VMWriter
from enum import Enum


class ArithmeticCommands(Enum):
    ADD = 'add'
    SUB = 'sub'
    NEG = 'neg'
    EQ = 'eq'
    GT = 'gt'
    LT = 'lt'
    AND = 'and'
    OR = 'or'
    NOT = 'not'
    MULT = 'call Math.multiply 2'
    DIV = 'call Math.divide 2'


class CompilationEngine:

    TYPE = (Keyword.INT, Keyword.CHAR, Keyword.BOOLEAN)
    KEYWORD_CONSTANT = (Keyword.TRUE, Keyword.FALSE, Keyword.NULL, Keyword.THIS)
    OPS = {'+': ArithmeticCommands.ADD,
           '-': ArithmeticCommands.SUB,
           '*': ArithmeticCommands.MULT,
           '/': ArithmeticCommands.DIV,
           '&': ArithmeticCommands.AND,
           '|': ArithmeticCommands.OR,
           '<': ArithmeticCommands.LT,
           '>': ArithmeticCommands.GT,
           '=': ArithmeticCommands.EQ}

    UNARY_OPS = {'-': ArithmeticCommands.NEG, '~': ArithmeticCommands.NOT}

    def __init__(self, input, output, print_xml=False):
        self.input = input
        self.vm = VMWriter(output + ".vm")
        self.print_xml = print_xml

        if self.print_xml:
            self.output = open(output + ".xml", 'w')

        self.unique_counters = {}

        # Initializes Tokenizer
        self.tokenizer = JackTokenizer(input)
        self.token_type = self.tokenizer.token_type
        self.tokenizer.advance()  # move to first token

        # Initializes SymbolTables
        self.symbolTable = SymbolTable()

        self.class_name = None
        self.compileClass()

        # Close streams
        if self.print_xml:
            self.output.close()
        self.vm.close()

    def syntaxError(self, expected):
        raise SyntaxError("{0} - Line {1}: Expected {2} but got {3} '{4}' instead.".format(self.input,
                                                                                           self.tokenizer.line,
                                                                                           ' '.join(expected),
                                                                                           self.tokenizer.token_type.value,
                                                                                           self.tokenizer.current_token
                                                                                           ))

    def validateToken(self, token_type, value):
        if isinstance(value, str) or isinstance(value, Enum):
            value = (value,)
        restricted_token = token_type in (TokenType.KEYWORD, TokenType.SYMBOL)
        return self.tokenizer.token_type == token_type and (self.tokenizer.current_token in value or not restricted_token)

    def processToken(self, token_type, value, raise_error=True):
        if self.validateToken(token_type, value):
            self.printXML(self.tokenizer.xml_converter())

            valid_token = self.tokenizer.current_token
            self.tokenizer.advance()
            return valid_token
        else:
            if raise_error:
                self.syntaxError([token_type.value, "'{0}'".format(value)])
            else:
                return False

    def validateType(self, extra_types=tuple()):
        types = self.TYPE + extra_types
        return self.validateToken(TokenType.KEYWORD, types) or self.validateToken(TokenType.IDENTIFIER, '*')

    def processType(self, extra_types=tuple()):
        if self.validateType(extra_types):
            self.printXML(self.tokenizer.xml_converter())

            valid_token = self.tokenizer.current_token
            self.tokenizer.advance()
            return valid_token
        else:
            self.syntaxError(["type"])

    def addToSymbolTable(self, name, type_, kind):
        self.symbolTable.define(name, type_, kind)
        self.printSymbolTable(name)

    def printSymbolTable(self, name):
        type_, kind, scope = self.symbolTable.lookup(name)
        self.printXML("<symbolTable>{0} {1} {2} {3}</symbolTable>".format(name, type_, kind, scope))

    def printXML(self, tag):
        if self.print_xml:
            print(tag, file=self.output)

    def getUniqueLabel(self, label):
        self.unique_counters.setdefault(label, 0)
        unique_label = "{0}{1}".format(label.upper(), self.unique_counters[label])
        self.unique_counters[label] += 1
        return unique_label

    def compileClass(self):
        """
        'class' className '{' classVarDec* subroutineDec* '}'
        :return:
        """

        self.printXML("<class>")

        self.processToken(TokenType.KEYWORD, Keyword.CLASS)
        self.class_name = self.processToken(TokenType.IDENTIFIER, 'className')
        self.processToken(TokenType.SYMBOL, '{')
        while self.compileClassVarDec():
            pass
        while self.compileSubroutine():
            pass
        self.processToken(TokenType.SYMBOL, '}')

        self.printXML("</class>")

    def compileClassVarDec(self):
        """
        ('static'|'field') type varName (',' varName)* ';'
        :return:
        """

        if not self.validateToken(TokenType.KEYWORD, (Keyword.STATIC, Keyword.FIELD)):
            return False

        self.printXML("<classVarDec>")

        property_kind = self.processToken(TokenType.KEYWORD, (Keyword.STATIC, Keyword.FIELD))
        property_type = self.processType()
        property_name = self.processToken(TokenType.IDENTIFIER, 'varName')

        self.addToSymbolTable(property_name, property_type, property_kind)

        while self.processToken(TokenType.SYMBOL, ",", raise_error=False):
            property_name = self.processToken(TokenType.IDENTIFIER, 'varName')
            self.addToSymbolTable(property_name, property_type, property_kind)
        self.processToken(TokenType.SYMBOL, ";")

        self.printXML("</classVarDec>")

        return True

    def compileSubroutine(self):
        """
        subroutineDec:
        ('constructor'|'function'|'method') ('void'|type) subroutineName '(' parameterList ')' subroutineBody

        parameterList:
        ((type varName) (','type varName)*)?
        subroutineBody:
        '{' varDec* statements* '}'
        varDec:
        'var' type varName  (','type varName)* ';'
        :return:
        """

        if not self.validateToken(TokenType.KEYWORD, (Keyword.CONSTRUCTOR, Keyword.FUNCTION, Keyword.METHOD)):
            return False

        self.symbolTable.startSubroutine()
        self.unique_counters = {}
        self.printXML("<subroutineDec>")
        subroutine_type = self.processToken(TokenType.KEYWORD, (Keyword.CONSTRUCTOR, Keyword.FUNCTION, Keyword.METHOD))
        if subroutine_type == Keyword.METHOD:
            self.addToSymbolTable(name="this", type_=self.class_name, kind=VariableKind.ARG)
        self.processType(extra_types=(Keyword.VOID,))
        subroutine_name = self.processToken(TokenType.IDENTIFIER, 'subroutineName')
        subroutine_name = "{class_name}.{subroutine}".format(class_name=self.class_name, subroutine=subroutine_name)
        self.processToken(TokenType.SYMBOL, '(')
        self.printXML("<parameterList>")
        self.compileParameterList()
        self.printXML("</parameterList>")
        self.processToken(TokenType.SYMBOL, ')')

        self.printXML("<subroutineBody>")
        self.processToken(TokenType.SYMBOL, '{')
        while self.compileVarDec():
            pass

        self.vm.writeFunction(subroutine_name, nlocals=self.symbolTable.varCount(VariableKind.VAR))

        if subroutine_type == Keyword.CONSTRUCTOR:
            # * constructor / function with k-args mapped to a function with k args.
            # NB:
            #  1. allocate memory block
            #  2. set the base of `this` to the base address of the object
            self.vm.writePush(Segments.CONSTANT, self.symbolTable.varCount(VariableKind.FIELD))
            self.vm.writeCall("Memory.alloc", 1)
            self.vm.writePop(Segments.POINTER, 0)

        if subroutine_type == Keyword.METHOD:
            # * method with k-args are mapped to a function with k+1 args.
            # * first need to set the base of `this` to `argument 0`
            self.vm.writePush(Segments.ARGUMENT, 0)
            self.vm.writePop(Segments.POINTER, 0)

        self.compileStatements()
        self.processToken(TokenType.SYMBOL, '}')
        self.printXML("</subroutineBody>")
        self.printXML("</subroutineDec>")

        return True

    def compileParameterList(self):
        """
        ((type varName) (','type varName)*)?
        :return:
        """
        if not self.validateType():
            return False  # no parameters

        var_type = self.processType()
        var_name = self.processToken(TokenType.IDENTIFIER, 'varName')
        self.addToSymbolTable(var_name, var_type, VariableKind.ARG)
        while self.processToken(TokenType.SYMBOL, ",", raise_error=False):
            var_type = self.processType()
            var_name = self.processToken(TokenType.IDENTIFIER, 'varName')
            self.addToSymbolTable(var_name, var_type, VariableKind.ARG)

    def compileVarDec(self):
        """
        'var' type varName  (','type varName)* ';'
        :return:
        """
        if not self.validateToken(TokenType.KEYWORD, Keyword.VAR):
            return False

        self.printXML("<varDec>")
        self.processToken(TokenType.KEYWORD, Keyword.VAR)
        var_type = self.processType()
        var_name = self.processToken(TokenType.IDENTIFIER, 'varName')
        self.addToSymbolTable(var_name, var_type, VariableKind.VAR)
        while self.processToken(TokenType.SYMBOL, ",", raise_error=False):
            var_name = self.processToken(TokenType.IDENTIFIER, 'varName')
            self.addToSymbolTable(var_name, var_type, VariableKind.VAR)
        self.processToken(TokenType.SYMBOL, ';')
        self.printXML("</varDec>")

        return True

    def compileStatements(self):
        statement_types = (Keyword.LET, Keyword.IF, Keyword.WHILE, Keyword.DO, Keyword.RETURN)
        if not self.validateToken(TokenType.KEYWORD, statement_types):
            return False

        self.printXML("<statements>")
        while self.compileLet() or self.compileIf() or self.compileWhile() or self.compileDo() or self.compileReturn():
            pass
        self.printXML("</statements>")

        return True

    def compileLet(self):
        """
        'let' varName ('[' expression ']'')? '=' expression ';'
                          a[i+1]  = arrays
        :return:
        """
        if not self.validateToken(TokenType.KEYWORD, Keyword.LET):
            return False

        self.printXML("<letStatement>")
        self.processToken(TokenType.KEYWORD, Keyword.LET)
        self.printSymbolTable(self.tokenizer.current_token)
        var_name = self.processToken(TokenType.IDENTIFIER, 'varName')
        array_expr = False
        if self.processToken(TokenType.SYMBOL, "[", raise_error=False):  # array expression arr[expr1] = expr2
            array_expr = True
            self.compileExpression()
            self.vm.writePush(self.symbolTable.segmentOf(var_name), self.symbolTable.indexOf(var_name))
            self.processToken(TokenType.SYMBOL, "]")
            self.vm.writeArithmetic(ArithmeticCommands.ADD)  # top of the stack is now the address of arr[expr1]

        self.processToken(TokenType.SYMBOL, "=")
        self.compileExpression()
        self.processToken(TokenType.SYMBOL, ";")

        if array_expr:
            self.vm.writePop(Segments.TEMP, 0)   # saves expr2 in a temp variable
            self.vm.writePop(Segments.POINTER, 1)  # set `that` to the right address
            self.vm.writePush(Segments.TEMP, 0)   # recovers expr2 on top of stack
            self.vm.writePop(Segments.THAT, 0)  # pop expr2 to arr[expr1]
        else:
            self.vm.writePop(self.symbolTable.segmentOf(var_name), self.symbolTable.indexOf(var_name))
        self.printXML("</letStatement>")

        return True

    def compileIf(self):
        """
        'if' '(' expression ')' '{' statements '}'  ('else' '{' statements '}')?
        :return:
        """
        if not self.validateToken(TokenType.KEYWORD, Keyword.IF):
            return False

        self.printXML("<ifStatement>")
        self.processToken(TokenType.KEYWORD, Keyword.IF)
        self.processToken(TokenType.SYMBOL, "(")
        self.compileExpression()
        self.processToken(TokenType.SYMBOL, ")")
        self.processToken(TokenType.SYMBOL, "{")

        if_true_label = self.getUniqueLabel("IF_TRUE")
        if_false_label = self.getUniqueLabel("IF_FALSE")
        self.vm.writeIf(if_true_label)
        self.vm.writeGoto(if_false_label)
        self.vm.writeLabel(if_true_label)
        statements = self.compileStatements()
        if not statements:
            raise SyntaxError("Line {0}: missing statement(s) in if-statement".format(self.tokenizer.line))
        self.processToken(TokenType.SYMBOL, "}")

        if self.processToken(TokenType.KEYWORD, Keyword.ELSE, raise_error=False):
            self.processToken(TokenType.SYMBOL, "{")
            if_end = self.getUniqueLabel("IF_END")
            self.vm.writeGoto(if_end)
            self.vm.writeLabel(if_false_label)

            statements = self.compileStatements()
            if not statements:
                raise SyntaxError("Line {0}: missing statement(s) in else-statement".format(self.tokenizer.line))
            self.processToken(TokenType.SYMBOL, "}")
            self.vm.writeLabel(if_end)
        else:
            self.vm.writeLabel(if_false_label)

        self.printXML("</ifStatement>")

        return True

    def compileWhile(self):
        """
        'while' '(' expression ')' '{' statements '}'
        :return:
        """
        if not self.validateToken(TokenType.KEYWORD, Keyword.WHILE):
            return False

        self.printXML("<whileStatement>")
        self.processToken(TokenType.KEYWORD, Keyword.WHILE)
        self.processToken(TokenType.SYMBOL, "(")

        while_expr = self.getUniqueLabel("WHILE_EXP")
        self.vm.writeLabel(while_expr)
        self.compileExpression()
        self.vm.writeArithmetic(ArithmeticCommands.NOT)
        while_end = self.getUniqueLabel("WHILE_END")
        self.vm.writeIf(while_end)

        self.processToken(TokenType.SYMBOL, ")")
        self.processToken(TokenType.SYMBOL, "{")
        self.compileStatements()
        self.vm.writeGoto(while_expr)
        self.processToken(TokenType.SYMBOL, "}")

        self.vm.writeLabel(while_end)
        self.printXML("</whileStatement>")

        return True

    def compileDo(self):
        """
        'do' subroutineCall ';'
        subroutineCall:
        subroutineName '('expressionList')' | (className|varName)'.'subroutineName '('expressionList')'
        expressionList:
        (expression (',' expression)*)?
        :return:
        """
        if not self.validateToken(TokenType.KEYWORD, Keyword.DO):
            return False

        self.printXML("<doStatement>")
        self.processToken(TokenType.KEYWORD, Keyword.DO)
        subroutine_or_class_or_var_name = self.processToken(TokenType.IDENTIFIER, 'subroutineOrClassOrVarName')
        self.compileSubroutineCall(subroutine_or_class_or_var_name)
        self.processToken(TokenType.SYMBOL, ";")
        self.vm.writePop(Segments.TEMP, 0)  # pop the return value
        self.printXML("</doStatement>")

        return True

    def compileSubroutineCall(self, class_or_var_or_subroutine_name):

        nargs = 0

        if self.processToken(TokenType.SYMBOL, '.', raise_error=False):  # class or var
            type_of_obj = self.symbolTable.typeOf(class_or_var_or_subroutine_name)
            if type_of_obj is None:  # Class Name e.g. "MyClass.new()"
                call_name = class_or_var_or_subroutine_name + '.' + self.processToken(TokenType.IDENTIFIER, 'constructorOrFunctionName')
            else:  # var e.g "obj.run()"
                nargs += 1  # the obj is pushed onto the stack to be passed as an arg
                self.vm.writePush(self.symbolTable.segmentOf(class_or_var_or_subroutine_name),
                                  self.symbolTable.indexOf(class_or_var_or_subroutine_name))
                call_name = type_of_obj + '.' + self.processToken(TokenType.IDENTIFIER, 'methodName')

        else:  # method of current class
            nargs += 1
            self.vm.writePush(Segments.POINTER, 0)  # push `this` on to the stack
            call_name = self.class_name + '.' + class_or_var_or_subroutine_name

        self.processToken(TokenType.SYMBOL, "(")
        self.printXML("<expressionList>")

        if not self.validateToken(TokenType.SYMBOL, ")"):
            nargs += self.compileExpressionList()
        self.printXML("</expressionList>")
        self.processToken(TokenType.SYMBOL, ")")

        self.vm.writeCall(call_name, nargs)

    def compileReturn(self):
        """
        'return' expression? ';'
        :return:
        """
        if not self.validateToken(TokenType.KEYWORD, Keyword.RETURN):
            return False

        self.printXML("<returnStatement>")
        self.processToken(TokenType.KEYWORD, Keyword.RETURN)

        if not self.validateToken(TokenType.SYMBOL, ";"):
            self.compileExpression()
        else:
            self.vm.writePush(Segments.CONSTANT, 0)
        self.processToken(TokenType.SYMBOL, ";")
        self.vm.writeReturn()
        self.printXML("</returnStatement>")

        return True

    def compileExpression(self):
        """
        term (op term)*
        :return:
        """
        self.printXML("<expression>")
        self.compileTerm()
        while self.validateToken(TokenType.SYMBOL, self.OPS):
            op = self.processToken(TokenType.SYMBOL, self.OPS)
            self.compileTerm()
            self.vm.writeArithmetic(self.OPS[op])
        self.printXML("</expression>")

    def compileTerm(self):
        """
        integerConstant|stringConstant|keywordConstant|varName|varName'[' expression ']'|subroutineCall|'(' expression ')'| unaryOp term
        :return:
        """
        self.printXML("<term>")
        if self.validateToken(TokenType.INT_CONST, 'integerConstant'):
            int_constant = self.processToken(TokenType.INT_CONST, 'integerConstant')
            self.vm.writePush(Segments.CONSTANT, int_constant)

        elif self.validateToken(TokenType.STRING_CONST, 'stringConstant'):
            string_constant = self.processToken(TokenType.STRING_CONST, 'stringConstant')
            self.vm.writePush(Segments.CONSTANT, len(string_constant))
            self.vm.writeCall("String.new", 1)
            for char in string_constant:
                self.vm.writePush(Segments.CONSTANT, ord(char))
                self.vm.writeCall("String.appendChar", 2)
        elif self.validateToken(TokenType.KEYWORD, self.KEYWORD_CONSTANT):
            keyword_constant = self.processToken(TokenType.KEYWORD, self.KEYWORD_CONSTANT)
            if keyword_constant in (Keyword.FALSE, Keyword.NULL):
                self.vm.writePush(Segments.CONSTANT, 0)
            elif keyword_constant == Keyword.TRUE:
                self.vm.writePush(Segments.CONSTANT, 0)
                self.vm.writeArithmetic(ArithmeticCommands.NOT)
            else:  # THIS
                self.vm.writePush(Segments.POINTER, 0)

        elif self.validateToken(TokenType.IDENTIFIER, 'varNameOrSubroutineCall'):
            var_or_subroutine_name = self.processToken(TokenType.IDENTIFIER, 'varNameOrSubroutineCall')
            if self.processToken(TokenType.SYMBOL, '[', raise_error=False):  # array expression
                array_name = var_or_subroutine_name
                self.compileExpression()
                self.vm.writePush(self.symbolTable.segmentOf(array_name), self.symbolTable.indexOf(array_name))
                self.vm.writeArithmetic(ArithmeticCommands.ADD)
                self.vm.writePop(Segments.POINTER, 1)
                self.vm.writePush(Segments.THAT, 0)
                self.processToken(TokenType.SYMBOL, ']')
            elif self.validateToken(TokenType.SYMBOL, ('(', '.')):  # subroutineCall
                subroutine_name = var_or_subroutine_name
                self.compileSubroutineCall(subroutine_name)
            else:
                var_name = var_or_subroutine_name
                self.printSymbolTable(var_name)
                var_segment = self.symbolTable.segmentOf(var_name)
                var_index = self.symbolTable.indexOf(var_name)
                if var_segment == Segments.THIS:  # field of current class => 'push this n'
                    self.vm.writePush(Segments.THIS, var_index)
                else:
                    self.vm.writePush(var_segment, var_index)

        elif self.processToken(TokenType.SYMBOL, '(', raise_error=False):
            self.compileExpression()
            self.processToken(TokenType.SYMBOL, ')')

        elif self.validateToken(TokenType.SYMBOL, self.UNARY_OPS):
            unary_op = self.processToken(TokenType.SYMBOL, self.UNARY_OPS)
            self.compileTerm()
            self.vm.writeArithmetic(self.UNARY_OPS[unary_op])
        self.printXML("</term>")

    def compileExpressionList(self):
        nargs = 0
        self.compileExpression()
        nargs += 1
        while self.processToken(TokenType.SYMBOL, ',', raise_error=False):
            self.compileExpression()
            nargs += 1

        return nargs


