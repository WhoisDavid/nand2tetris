from JackTokenizer import JackTokenizer, TokenType, Keyword


class CompilationEngine:

    TYPE = (Keyword.INT.value, Keyword.CHAR.value, Keyword.BOOLEAN.value)  # TODO: add clasName when we add symbol table
    KEYWORD_CONSTANT = (Keyword.TRUE.value, Keyword.FALSE.value, Keyword.NULL.value, Keyword.THIS.value)
    OPS = ('+', '-', '*', '/', '&', '|', '<', '>', '=')
    UNARY_OPS = ('-', '~')

    def __init__(self, input, output):
        self.input = input
        self.output = open(output, 'w')
        self.tokenizer = JackTokenizer(input)
        self.current_token = self.tokenizer.current_token
        self.token_type = self.tokenizer.token_type
        self.tokenizer.advance()  # move to first token
        self.compileClass()

    def syntaxError(self, expected):
        raise SyntaxError("{0} - Line {1}: Expected {2} but got {3} '{4}' instead.".format(self.input,
                                                                                            self.tokenizer.line,
                                                                                            ' '.join(expected),
                                                                                            self.tokenizer.token_type.value,
                                                                                            self.tokenizer.current_token
                                                                                            ))

    def validateToken(self, token_type, value):
        if isinstance(value, str):
            value = (value,)
        restricted_token = token_type in (TokenType.KEYWORD, TokenType.SYMBOL)
        return self.tokenizer.token_type == token_type and (self.tokenizer.current_token in value or not restricted_token)

    def compile(self, token_type, value, raise_error=True):
        if self.validateToken(token_type, value):
            print(self.tokenizer.xml_converter(), file=self.output)
            return self.tokenizer.advance()
        else:
            if raise_error:
                self.syntaxError([token_type.value, "'{0}'".format(value)])
            else:
                return False

    def validateType(self, extra_types=tuple()):
        types = self.TYPE + extra_types
        return self.validateToken(TokenType.KEYWORD, types) or self.validateToken(TokenType.IDENTIFIER, '*')

    def compileType(self, extra_types=tuple()):
        if self.validateType(extra_types):
            print(self.tokenizer.xml_converter(), file=self.output)
            return self.tokenizer.advance()
        else:
            self.syntaxError(["type"])

    def compileClass(self):
        """
        'class' className '{' classVarDec* subroutineDec* '}'
        :return:
        """
        print("<class>", file=self.output)

        self.compile(TokenType.KEYWORD, Keyword.CLASS.value)
        self.compile(TokenType.IDENTIFIER, 'className')
        self.compile(TokenType.SYMBOL, '{')
        while self.compileClassVarDec():
            pass
        while self.compileSubroutine():
            pass
        self.compile(TokenType.SYMBOL, '}')

        print("</class>", file=self.output)

    def compileClassVarDec(self):
        """
        ('static'|'field') type varName (',' varName)* ';'
        :return:
        """

        if not self.validateToken(TokenType.KEYWORD, (Keyword.STATIC.value, Keyword.FIELD.value)):
            return False

        print("<classVarDec>", file=self.output)

        self.compile(TokenType.KEYWORD, (Keyword.STATIC.value, Keyword.FIELD.value))
        self.compileType()
        self.compile(TokenType.IDENTIFIER, 'varName')
        while self.compile(TokenType.SYMBOL, ",", raise_error=False):
            self.compile(TokenType.IDENTIFIER, 'varName')
        self.compile(TokenType.SYMBOL, ";")

        print("</classVarDec>", file=self.output)

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

        if not self.validateToken(TokenType.KEYWORD, (Keyword.CONSTRUCTOR.value, Keyword.FUNCTION.value, Keyword.METHOD.value)):
            return False

        print("<subroutineDec>", file=self.output)
        self.compile(TokenType.KEYWORD, (Keyword.CONSTRUCTOR.value, Keyword.FUNCTION.value, Keyword.METHOD.value))
        self.compileType(extra_types=(Keyword.VOID.value,))
        self.compile(TokenType.IDENTIFIER, 'subroutineName')
        self.compile(TokenType.SYMBOL, '(')
        print("<parameterList>", file=self.output)
        self.compileParameterList()
        print("</parameterList>", file=self.output)
        self.compile(TokenType.SYMBOL, ')')
        print("<subroutineBody>", file=self.output)
        self.compile(TokenType.SYMBOL, '{')
        while self.compileVarDec():
            pass
        self.compileStatements()
        self.compile(TokenType.SYMBOL, '}')
        print("</subroutineBody>", file=self.output)
        print("</subroutineDec>", file=self.output)

        return True

    def compileParameterList(self):
        """
        ((type varName) (','type varName)*)?
        :return:
        """
        if not self.validateType():
            return False  # no parameters

        self.compileType()
        self.compile(TokenType.IDENTIFIER, 'varName')
        while self.compile(TokenType.SYMBOL, ",", raise_error=False):
            self.compileType()
            self.compile(TokenType.IDENTIFIER, 'varName')


    def compileVarDec(self):
        """
        'var' type varName  (','type varName)* ';'
        :return:
        """
        if not self.validateToken(TokenType.KEYWORD, Keyword.VAR.value):
            return False

        print("<varDec>", file=self.output)
        self.compile(TokenType.KEYWORD, Keyword.VAR.value)
        self.compileType()
        self.compile(TokenType.IDENTIFIER, 'varName')
        while self.compile(TokenType.SYMBOL, ",", raise_error=False):
            self.compile(TokenType.IDENTIFIER, 'varName')
        self.compile(TokenType.SYMBOL, ';')
        print("</varDec>", file=self.output)

        return True

    def compileStatements(self):
        statement_types = (Keyword.LET.value, Keyword.IF.value, Keyword.WHILE.value, Keyword.DO.value, Keyword.RETURN.value)
        if not self.validateToken(TokenType.KEYWORD, statement_types):
            return False

        print("<statements>", file=self.output)
        while self.compileLet() or self.compileIf() or self.compileWhile() or self.compileDo() or self.compileReturn():
            pass
        print("</statements>", file=self.output)

        return True

    def compileLet(self):
        """
        'let' varName ('[' expression ']'')? '=' expression ';'
                          a[i+1]  = arrays
        :return:
        """
        if not self.validateToken(TokenType.KEYWORD, Keyword.LET.value):
            return False

        print("<letStatement>", file=self.output)
        self.compile(TokenType.KEYWORD, Keyword.LET.value)
        self.compile(TokenType.IDENTIFIER, 'varName')
        if self.compile(TokenType.SYMBOL, "[", raise_error=False):
            self.compileExpression()
            self.compile(TokenType.SYMBOL, "]")
        self.compile(TokenType.SYMBOL, "=")
        self.compileExpression()
        self.compile(TokenType.SYMBOL, ";")
        print("</letStatement>", file=self.output)

        return True

    def compileIf(self):
        """
        'if' '(' expression ')' '{' statements '}'  ('else' '{' statements '}')?
        :return:
        """
        if not self.validateToken(TokenType.KEYWORD, Keyword.IF.value):
            return False

        print("<ifStatement>", file=self.output)
        self.compile(TokenType.KEYWORD, Keyword.IF.value)
        self.compile(TokenType.SYMBOL, "(")
        self.compileExpression()
        self.compile(TokenType.SYMBOL, ")")
        self.compile(TokenType.SYMBOL, "{")
        statements = self.compileStatements()
        if not statements:
            raise SyntaxError("Line {0}: missing statement(s) in if-statement")
        self.compile(TokenType.SYMBOL, "}")

        if self.compile(TokenType.KEYWORD, Keyword.ELSE.value, raise_error=False):
            self.compile(TokenType.SYMBOL, "{")
            statements = self.compileStatements()
            if not statements:
                raise SyntaxError("Line {0}: missing statement(s) in else-statement")
            self.compile(TokenType.SYMBOL, "}")
        print("</ifStatement>", file=self.output)

        return True

    def compileWhile(self):
        """
        'while' '(' expression ')' '{' statements '}'
        :return:
        """
        if not self.validateToken(TokenType.KEYWORD, Keyword.WHILE.value):
            return False

        print("<whileStatement>", file=self.output)
        self.compile(TokenType.KEYWORD, Keyword.WHILE.value)
        self.compile(TokenType.SYMBOL, "(")
        self.compileExpression()
        self.compile(TokenType.SYMBOL, ")")
        self.compile(TokenType.SYMBOL, "{")
        self.compileStatements()
        self.compile(TokenType.SYMBOL, "}")
        print("</whileStatement>", file=self.output)

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
        if not self.validateToken(TokenType.KEYWORD, Keyword.DO.value):
            return False

        print("<doStatement>", file=self.output)
        self.compile(TokenType.KEYWORD, Keyword.DO.value)
        self.compile(TokenType.IDENTIFIER, 'subroutineOrClassOrVarName')
        self.compileSubroutineCall()
        self.compile(TokenType.SYMBOL, ";")
        print("</doStatement>", file=self.output)

        return True

    def compileSubroutineCall(self):
        if self.compile(TokenType.SYMBOL, '.', raise_error=False):
            self.compile(TokenType.IDENTIFIER, 'subroutineName')
        self.compile(TokenType.SYMBOL, "(")
        print("<expressionList>", file=self.output)
        if not self.validateToken(TokenType.SYMBOL, ")"):
            self.compileExpressionList()
        print("</expressionList>", file=self.output)
        self.compile(TokenType.SYMBOL, ")")

    def compileReturn(self):
        """
        'return' expression? ';'
        :return:
        """
        if not self.validateToken(TokenType.KEYWORD, Keyword.RETURN.value):
            return False

        print("<returnStatement>", file=self.output)
        self.compile(TokenType.KEYWORD, Keyword.RETURN.value)

        if not self.validateToken(TokenType.SYMBOL, ";"):
            self.compileExpression()
        self.compile(TokenType.SYMBOL, ";")
        print("</returnStatement>", file=self.output)

        return True

    def compileExpression(self):
        """
        term (op term)*
        :return:
        """
        print("<expression>", file=self.output)
        self.compileTerm()
        while self.compile(TokenType.SYMBOL, self.OPS, raise_error=False):
            self.compileTerm()
        print("</expression>", file=self.output)

    def compileTerm(self):
        """
        integerConstant|stringConstant|keywordConstant|varName|varName'[' expression ']'|subroutineCall|'(' expression ')'| unaryOp term
        :return:
        """
        print("<term>", file=self.output)
        if self.compile(TokenType.INT_CONST, 'integerConstant', raise_error=False):
            pass
        elif self.compile(TokenType.STRING_CONST, 'integerConstant', raise_error=False):
            pass
        elif self.compile(TokenType.KEYWORD, self.KEYWORD_CONSTANT, raise_error=False):
            pass
        elif self.compile(TokenType.IDENTIFIER, 'varNameOrSubroutineCall', raise_error=False):
            if self.compile(TokenType.SYMBOL, '[', raise_error=False):  # array expression
                self.compileExpression()
                self.compile(TokenType.SYMBOL, ']')
            elif self.validateToken(TokenType.SYMBOL, ('(', '.')):  # subroutineCall
                self.compileSubroutineCall()
        elif self.compile(TokenType.SYMBOL, '(', raise_error=False):
            self.compileExpression()
            self.compile(TokenType.SYMBOL, ')')
        elif self.compile(TokenType.SYMBOL, self.UNARY_OPS, raise_error=False):
            self.compileTerm()
        print("</term>", file=self.output)

    def compileExpressionList(self):
        self.compileExpression()
        while self.compile(TokenType.SYMBOL, ',', raise_error=False):
            self.compileExpression()


