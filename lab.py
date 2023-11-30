"""
6.101 Lab 12:
LISP Interpreter Part 1
"""

#!/usr/bin/env python3

import sys
import doctest     

sys.setrecursionlimit(20_000)

# NO ADDITIONAL IMPORTS!

#############################
# Scheme-related Exceptions #
#############################

class SchemeError(Exception):
    """
    A type of exception to be raised if there is an error with a Scheme
    program.  Should never be raised directly; rather, subclasses should be
    raised.
    """

    pass


class SchemeSyntaxError(SchemeError):
    """
    Exception to be raised when trying to evaluate a malformed expression.
    """

    pass


class SchemeNameError(SchemeError):
    """
    Exception to be raised when looking up a name that has not been defined.
    """

    pass


class SchemeEvaluationError(SchemeError):
    """
    Exception to be raised if there is an error during evaluation other than a
    SchemeNameError.
    """

    pass


############################
# Tokenization and Parsing #
############################


def number_or_symbol(value):
    """
    Helper function: given a string, convert it to an integer or a float if
    possible; otherwise, return the string itself

    >>> number_or_symbol('8')
    8
    >>> number_or_symbol('-5.32')
    -5.32
    >>> number_or_symbol('1.2.3.4')
    '1.2.3.4'
    >>> number_or_symbol('x')
    'x'
    """
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def tokenize(source):
    """
    Splits an input string into meaningful tokens (left parens, right parens,
    other whitespace-separated values).  Returns a list of strings.

    Arguments:
        source (str): a string containing the source code of a Scheme
                      expression
    """
    seperated = source.replace("(", " ( ").replace(")", " ) ")
    lines = seperated.splitlines() #splits string into a list of lines
    tokens = []
    for line in lines:
        partitioned = line.partition(";") #partitions line in code and comments
        tokens += partitioned[0].split() # adds only the code to the tokens
    return tokens

def formated_correctly(tokens):
    """
    Checks that tokens have:
      an equal number of closing and opening parenthesis
      starts and end with a parenthesis
    """
    if isinstance(tokens, list):
        if len(tokens) == 1:
            return tokens[0] not in ("(", ")")
        else:
            equal_num_of_parenthesis =  tokens.count("(") == tokens.count(")")
            starts_ends_with_parthesis = tokens[0] == "(" and tokens[-1] == ")"
            return equal_num_of_parenthesis and starts_ends_with_parthesis
    return True

def parse(tokens):
    """
    Parses a list of tokens, constructing a representation where:
        * symbols are represented as Python strings
        * numbers are represented as Python ints or floats
        * S-expressions are represented as Python lists

    Arguments:
        tokens (list): a list of strings representing tokens
    """
    if not formated_correctly(tokens):
        raise SchemeSyntaxError
    def nested_parser(rest):
        parsed = []
        i = 0
        while i < len(rest):
            token = rest[i]
            if token == ')':
                return parsed, i
            if token == '(' :
                i += 1 # add one to skip '('
                nests, added_index = nested_parser(rest[i:])
                parsed.append(nests)
                i += added_index
            else: 
                parsed.append(number_or_symbol(token))
            i += 1
        return parsed, i
    return nested_parser(tokens)[0][0]

######################
# Built-in Functions #
######################
def mul(args):
    #multiplies all args together
    if len(args) == 1:
        return args[0]
    else: 
        running_total = 1
        for arg in args:
            running_total *= arg
        return running_total
    
def div(args):
    # successively divides the first argument by the remaining arguments
    if len(args) == 1:
        return args[0]
    else: 
        to_divide = args[0]
        for arg in args[1:]:
            to_divide /= arg
        return to_divide

scheme_builtins = {
    "+": sum,
    "-": lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),
    "*": mul,
    "/": div
}



##############
# Evaluation #
##############
class Frame:
    # Creates a Frame to hold bindings for a function to access
    def __init__(self, parent = "global", bindings = None):
        if parent == "global":
            self.parent = global_frame
        else:
            self.parent = parent
        if bindings is None:
            self.bindings = {}
        else:
            self.bindings = bindings
        
    def __getitem__ (self, arg):
        if arg in self.bindings:
            return self.bindings[arg]
        elif self.parent is None:
            print("variable not bound:", arg)
            raise SchemeNameError("variable not bound:", arg)
        #recursive case
        return self.parent[arg]
    def __setitem__ (self, var, value):
        self.bindings[var] = value
global_frame = Frame(None, scheme_builtins)

def chars_in_string(chars, string):
    """
    given a list of chars and a string
    return a list of bool values True: if char in string
    """
    result = []
    for char in chars:
        result.append(char in string)
    return result

def valid_var_name(var_name):
    """
    given a variable name check that it is not a num/float
    and does not cotain "(" or ")"
    """
    forbidden = ("(", ")")
    if isinstance(var_name, (int, float)):
        return False
    elif any(chars_in_string(forbidden, var_name)):
        return False
    return True

def result_and_frame(tree, frame = None):
    """
    returns a tuple with two elements: 
    the result of the evaluation
    the frame in which the expression was evaluated
    """
    if frame is None: 
        return(evaluate(tree), Frame()) # Lab says if no frame is given must be brand new frame
    return (evaluate(tree), Frame(frame))

def evaluate(tree, framing = None):
    """
    Evaluate the given syntax tree according to the rules of the Scheme
    language.

    Arguments:
        tree (type varies): a fully parsed expression, as the output from the
                            parse function
    """
    if framing is None: 
        framing = global_frame
    def function_call(rest, frame):
        # evaluates each sub_expression for a unknown function
        evaluated_arguments = []
        for sub_exp in rest:
            evaluated_arguments.append(evaluate(sub_exp, frame))
        return evaluated_arguments
    
    def eval_helper(exp, frame):
        # Base cases
        if not isinstance(exp, list):
            if isinstance(exp, (int,float)):
                return exp
            elif exp in scheme_builtins:
                return scheme_builtins[exp]
            else:   
                return frame[exp] # check if expression is in frame or parent frames
        # Tree is a list
        else: 
            operator = exp[0]
            rest = exp[1:] 
            if operator in scheme_builtins:
                function_return = function_call(rest, frame)
                return scheme_builtins[operator](function_return)
            else:
                raise SchemeEvaluationError ("Operator not in built-in functions")
            
    def define(exp, frame):
        # handles define keyword to define a variable and it's value
        if len(exp) == 1:
            raise SchemeSyntaxError("var to define not given")
        elif not valid_var_name(exp[1]):
            raise SchemeSyntaxError("var name not valid")
        else:
            frame[exp[1]] = evaluate(exp[2], frame)
            return frame[exp[1]]
        
    if isinstance(tree, list):
        if tree[0] == "define":
            return define(tree, framing)
    return eval_helper(tree, framing)




    

########
# REPL #
########

import os
import re
import sys
import traceback
from cmd import Cmd

try:
    import readline
except:
    readline = None


def supports_color():
    """
    Returns True if the running system's terminal supports color, and False
    otherwise.  Not guaranteed to work in all cases, but maybe in most?
    """
    plat = sys.platform
    supported_platform = plat != "Pocket PC" and (
        plat != "win32" or "ANSICON" in os.environ
    )
    # IDLE does not support colors
    if "idlelib" in sys.modules:
        return False
    # isatty is not always implemented, #6223.
    is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    if not supported_platform or not is_a_tty:
        return False
    return True


class SchemeREPL(Cmd):
    """
    Class that implements a Read-Evaluate-Print Loop for our Scheme
    interpreter.
    """

    history_file = os.path.join(os.path.expanduser("~"), ".6101_scheme_history")

    if supports_color():
        prompt = "\033[96min>\033[0m "
        value_msg = "  out> \033[92m\033[1m%r\033[0m"
        error_msg = "  \033[91mEXCEPTION!! %s\033[0m"
    else:
        prompt = "in> "
        value_msg = "  out> %r"
        error_msg = "  EXCEPTION!! %s"

    keywords = {
        "define", "lambda", "if", "equal?", "<", "<=", ">", ">=", "and", "or",
        "del", "let", "set!", "+", "-", "*", "/", "#t", "#f", "not", "nil",
        "cons", "list", "cat", "cdr", "list-ref", "length", "append", "begin",
    }

    def __init__(self, use_frames=False, verbose=False):
        self.verbose = verbose
        self.use_frames = use_frames
        self.global_frame = None
        Cmd.__init__(self)

    def preloop(self):
        if readline and os.path.isfile(self.history_file):
            readline.read_history_file(self.history_file)

    def postloop(self):
        if readline:
            readline.set_history_length(10_000)
            readline.write_history_file(self.history_file)

    def completedefault(self, text, line, begidx, endidx):
        try:
            bound_vars = set(self.global_frame)
        except:
            bound_vars = set()
        return sorted(i for i in (self.keywords | bound_vars) if i.startswith(text))

    def onecmd(self, line):
        if line in {"EOF", "quit", "QUIT"}:
            print()
            print("bye bye!")
            return True

        elif not line.strip():
            return False

        try:
            token_list = tokenize(line)
            if self.verbose:
                print("tokens>", token_list)
            expression = parse(token_list)
            if self.verbose:
                print("expression>", expression)
            if self.use_frames:
                output, self.global_frame = result_and_frame(
                    *(
                        (expression, self.global_frame)
                        if self.global_frame is not None
                        else (expression,)
                    )
                )
            else:
                output = evaluate(expression)
            print(self.value_msg % output)
        except SchemeError as e:
            if self.verbose:
                traceback.print_tb(e.__traceback__)
                print(self.error_msg.replace("%s", "%r") % e)
            else:
                print(self.error_msg % e)

        return False

    completenames = completedefault

    def cmdloop(self, intro=None):
        while True:
            try:
                Cmd.cmdloop(self, intro=None)
                break
            except KeyboardInterrupt:
                print("^C")


if __name__ == "__main__":
    # code in this block will only be executed if lab.py is the main file being
    # run (not when this module is imported)
    msg = "\n\t['bare-name']\n"
    tokens = tokenize(msg)
    def output(string):
        tokens = tokenize(string)
        print(evaluate(parse(tokens)))
    print(tokens)
    print(parse(tokens))
    output("(define x ( + 3 2))")
    output("(define x2 (* x x))")
    
    SchemeREPL(use_frames=True, verbose=True).cmdloop()
    