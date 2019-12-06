import re
import os
from enum import Enum


class TokenType(Enum):
    KEYWORD = "keyword"
    SYMBOL = "symbol"
    IDENTIFIER = "identifier"
    INT_CONST = "integerConstant"
    STRING_CONST = "stringConstant"


class Keyword(Enum):
    CLASS = "class"
    METHOD = "method"
    FUNCTION = "function"
    CONSTRUCTOR = "constructor"
    INT = "int"
    BOOLEAN = "boolean"
    CHAR = "char"
    VOID = "void"
    VAR = "var"
    STATIC = "static"
    FIELD = "field"
    LET = "let"
    DO = "do"
    IF = "if"
    ELSE = "else"
    WHILE = "while"
    RETURN = "return"
    TRUE = "true"
    FALSE = "false"
    NULL = "null"
    THIS = "this"


class JackTokenizer:
    # tokens_regexp groups = (digits, stringConstant, string, operator)
    tokens_regexp = re.compile("[^\n\S]*(?:(\d+)|(\".*\")|([a-zA-Z_]+[a-zA-Z_0-9]*)|([^a-zA-Z_0-9]))")
    spaces_regex = re.compile("(^[^\n\S]*)|([^\n\S]*$)", flags=re.MULTILINE)
    comments_regex = re.compile("//(?:.*?$)|/\*(?:.*?\n*)*\*/", flags=re.MULTILINE)

    symbols = ('{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/', '&', '|', '<', '>', '=', '~')

    xml_chars = {'<': "&lt;", '>': "&gt;",  "&": "&amp;", '"': "&quot;"}

    def __init__(self, file_path):
        self.current_token = None
        self.file_path = file_path
        with open(self.file_path, 'r') as f:
            self.jack_code = self.sanitize(f.read())

        self.tokens_generator = self.tokens_regexp.finditer(self.jack_code)
        self.matched_tokens = None
        self.current_token = None
        self.token_type = None
        self.line = 1

    def sanitize(self, code):
        code = self.spaces_regex.sub("", code)
        comments = self.comments_regex.findall(code)
        for comment in comments:
            # substitutes each comment with the appropruate number of new line for line counting (syntax analyzer)
            code = code.replace(comment, "\n" * comment.count("\n"))

        return code

    def tokenize(self):
        dir = os.path.dirname(self.file_path)
        filename = os.path.splitext(os.path.basename(self.file_path))[0]
        output = os.path.join(dir, filename + "__.xml")
        f = open(output, 'w')

        print("<tokens>", file=f)

        while self.advance():
            print(self.xml_converter(), file=f)

        print("</tokens>", file=f)
        f.close()

    def xml_converter(self):
        xml_token = re.sub('|'.join(self.xml_chars), lambda x: self.xml_chars[x.group(0)], self.current_token)
        xml_line = "<{type}> {value} </{type}>".format(type=self.token_type.value,
                                                       value=xml_token)
        return xml_line

    def advance(self):

        try:
            self.matched_tokens = next(self.tokens_generator).groups()
        except StopIteration:
            return False

        int_const, string_const, keyword_or_identifier, _symbol = self.matched_tokens

        if int_const:
            self.current_token = int_const
            self.token_type = TokenType.INT_CONST
            return True

        if string_const:
            self.current_token, self.token_type = string_const[1:-1], TokenType.STRING_CONST
            return True

        if keyword_or_identifier:
            if keyword_or_identifier.upper() in Keyword.__members__:
                self.current_token, self.token_type = keyword_or_identifier, TokenType.KEYWORD
                return True
            else:
                self.current_token, self.token_type = keyword_or_identifier, TokenType.IDENTIFIER
                return True

        if _symbol:
            if _symbol in self.symbols:
                self.current_token, self.token_type = _symbol, TokenType.SYMBOL
                return True

            if _symbol == "\n":
                self.line += 1
                return self.advance()

            raise SyntaxError("Line {0}: illegal symbol {1}".format(self.line, _symbol))

        raise SyntaxError("Line {0}: illegal token")

