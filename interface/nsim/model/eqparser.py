# Nmag micromagnetic simulator
# Copyright (C) 2010, 2011 University of Southampton
# Hans Fangohr, Thomas Fischbacher, Matteo Franchin and others
#
# WEB:     http://nmag.soton.ac.uk
# CONTACT: nmag@soton.ac.uk
#
# AUTHOR(S) OF THIS FILE: Matteo Franchin
# LICENSE: GNU General Public License 2.0
#          (see <http://www.gnu.org/licenses/>)

"""Provides a function to parse an equation of motion and return a tree
representation of the equation which can be used to simplify the equation,
examine the quantities involved in the equation and finally rewrite it as
text."""

from os.path import split, realpath

from eqtree import *

__all__ = ['lexer', 'parser', 'parse']

tokens = ('INT', 'FLOAT', 'STRING',
          'ASSIGN', 'LOCAL', 'RANGE',
          'LPAREN', 'RPAREN', 'LBRACKET','RBRACKET',
          'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
          'COLON','COMMA', 'SEMICOLON', 'UNDERSCORE')

# Tokens
t_STRING = r'[a-zA-Z][a-zA-Z0-9_]*'
t_ASSIGN = r'<-'
t_LOCAL = r'%local'
t_RANGE = r'%range'
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_COMMA = r','
t_COLON = r':'
t_SEMICOLON = r';'
t_UNDERSCORE = r'_'

def t_FLOAT(t):
    r'\d*[.]\d+([eE]-?\d+)?|\d+[eE]-?\d+'
    try:
        t.value = float(t.value)
    except ValueError:
        print "Floating point number is too large", t.value
        t.value = 0
    return t

def t_INT(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print "Integer number is too large", t.value
        t.value = 0
    return t

# Ignored characters
t_ignore = " \t\r\n"

def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

# Build the lexer
import ply.lex as lex
lexer = lex.lex(lextab='localeqn_lextab')

def p_parse_localeqn(t):
    """parse_localeqn : local_and_range_defs assignments"""
    lt = len(t)
    if lt == 1:
        t[0] = LocalEqnNode()
    else:
        t[0] = LocalEqnNode([t[1], t[2]])

def p_local_and_range_defs(t):
    """local_and_range_defs :
                            | local_and_range_defs LOCAL num_tensors SEMICOLON
                            | local_and_range_defs RANGE ix_ranges SEMICOLON"""
    if len(t) == 1:
        t[0] = LocalAndRangeDefsNode()
    elif t[2] == '%local':
        t[0] = t[1].add_local(t[3])
    else:
        assert t[2] == '%range'
        t[0] = t[1].add_range(t[3])

# Tensors with number-only indices
def p_num_tensors(t):
    """num_tensors :
                   | num_tensor
                   | num_tensors COMMA num_tensor"""
    lt = len(t)
    if lt == 1:
        t[0] = NumTensorsNode()
    elif lt == 2:
        t[0] = NumTensorsNode().add(t[1])
    else:
        assert lt == 4
        t[0] = t[1].add(t[3])

def p_num_tensor(t):
    """num_tensor : STRING
                  | STRING LPAREN int_indices RPAREN"""
    lt = len(t)
    if lt == 2:
        t[0] = NumTensorNode(None, t[1])
    else:
        assert lt == 5
        t[0] = NumTensorNode(t[3], t[1])

def p_int_indices(t):
    """int_indices :
                   | INT
                   | int_indices COMMA INT"""
    lt = len(t)
    if lt == 1:
        t[0] = IntsNode()
    elif lt == 2:
        t[0] = IntsNode().add(t[1])
    else:
        assert lt == 4
        t[0] = t[1].add(t[3])

def p_ix_ranges(t):
    """ix_ranges : STRING COLON INT
                 | ix_ranges COMMA STRING COLON INT"""
    lt = len(t)
    if lt == 1:
        t[0] = IxRangeNode()
    elif lt == 4:
        t[0] = IxRangeNode().add2(None, (t[1], t[3]))
    else:
        assert lt == 6
        t[0] = t[1].add2(None, (t[3], t[5]))

def p_assignments(t):
    """assignments :
                   | assignments idx_assignments SEMICOLON"""
    lt = len(t)
    if lt == 1:
        t[0] = AssignmentsNode()
    else:
        assert lt == 4
        t[0] = t[1].add(t[2])

def p_idx_assignments(t):
    """idx_assignments : lvalue ASSIGN tensor_sum
                       | LPAREN lvalue ASSIGN tensor_sum RPAREN \
                         UNDERSCORE LPAREN ix_ranges RPAREN"""
    lt = len(t)
    if lt == 4:
        t[0] = IdxAssignmentsNode(AssignmentNode([t[1], t[3]]))
    else:
        t[0] = IdxAssignmentsNode([AssignmentNode([t[2], t[4]]), t[8]])

def p_lvalue(t):
    """lvalue : tensor"""
    t[0] = t[1]

def p_tensor(t):
    """tensor : STRING
              | STRING LPAREN indices RPAREN"""
    lt = len(t)
    if lt == 2:
        t[0] = TensorNode(name=t[1])
    else:
        assert lt == 5
        t[0] = TensorNode(name=t[1], arg=t[3])

def p_indices(t):
    """indices :
               | index
               | indices COMMA index"""
    lt = len(t)
    if lt == 1:
        t[0] = IndicesNode()
    elif lt == 2:
        t[0] = IndicesNode().add(t[1])
    else:
        assert lt == 4
        t[0] = t[1].add(t[3])

def p_index(t):
    """index : INT
             | STRING"""
    if type(t[1]) == int:
        t[0] = NumIndexNode(t[1])
    else:
        t[0] = VarIndexNode(t[1])

def p_tensor_sum(t):
    """tensor_sum : tensor_product
                  | tensor_sum sign tensor_product"""
    lt = len(t)
    if lt == 2:
        t[0] = TensorSumNode().add2(t[1], None)
    else:
        assert lt == 4
        t[0] = t[1].add2(t[3], t[2])

def p_tensor_product(t):
    """tensor_product : signed_tensor_atom
                      | tensor_product TIMES signed_tensor_atom
                      | tensor_product DIVIDE signed_tensor_atom"""
    lt = len(t)
    if lt == 2:
        t[0] = TensorProductNode().add2(t[1], None)
    else:
        assert lt == 4
        t[0] = t[1].add2(t[3], t[2])

def p_sign(t):
    """sign : PLUS
            | MINUS"""
    if t[1] == '+':
        t[0] = 1.0
    else:
        assert t[1] == '-'
        t[0] = -1.0

def p_signed_tensor_atom(t):
    """signed_tensor_atom : tensor_atom
                          | sign signed_tensor_atom"""
    lt = len(t)
    if lt == 2:
        t[0] = SignedTensorAtomNode(t[1])
    else:
        assert lt == 3
        t[0] = t[2].sign(t[1])

# XXX TODO: change function and tensor argument parentheses: tensors use []
# indexing, functions use ()!
def p_tensor_atom(t):
    """tensor_atom : INT
                   | FLOAT
                   | STRING
                   | STRING LPAREN indices RPAREN
                   | STRING LBRACKET tensor_sum RBRACKET
                   | LPAREN tensor_sum RPAREN
                   | LPAREN tensor_sum RPAREN \
                     UNDERSCORE LPAREN ix_ranges RPAREN"""
    lt = len(t)
    if lt == 2:
        if isinstance(t[1], (int, float)):
            t[0] = FloatNode(t[1])
        else:
            t[0] = TensorNode(name=t[1])
    elif lt == 4:
        t[0] = ParenthesisNode(t[2])
    elif lt == 5:
        if isinstance(t[3], IndicesNode):
            t[0] = TensorNode(name=t[1], arg=t[3])
        else:
            t[0] = FunctionNode(name=t[1], arg=t[3])
    elif lt == 8:
        t[0] = IdxTensorSumNode([t[2], t[6]])

def p_error(t):
    if hasattr(t, 'value'):
        info = " (token='%s', value='%s')" % (str(t), t.value)
    else:
        info = " (token='%s')" % str(t)
    raise ValueError("Syntax error when parsing equation%s." % info)

import ply.yacc as yacc

try:
    import localeqn_parsetab
    tabmodule = localeqn_parsetab
except:
    tabmodule = "localeqn_parsetab"

parser = yacc.yacc(tabmodule=tabmodule,
                   debugfile='localeqn_parser.out',
                   outputdir=split(realpath(__file__))[0])

def parse(s):
    return parser.parse(s, lexer=lexer)
