"""SHACL Logical Syntax parser.

Parses a SHACL shapes graph into a parse tree of the SHACL Logical Syntax.
See the README for details on the SANode/PANode data structures.
"""

from slsparser.shapels import parse, SANode, Op
from slsparser.pathls import PANode, POp
from slsparser.utilities import (
    expand_shape,
    negation_normal_form,
    clean_parsetree,
)

__version__ = "1.0.0"

__all__ = [
    "parse",
    "SANode",
    "Op",
    "PANode",
    "POp",
    "expand_shape",
    "negation_normal_form",
    "clean_parsetree",
]
