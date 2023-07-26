from pytest import mark

from rdflib.namespace import RDF, RDFS, XSD, SH
from rdflib import Graph, Namespace, Literal, URIRef

from slsparser.shapels import parse, Op, SANode
from slsparser.pathls import PANode, POp
from slsparser.utilities import clean_parsetree

EX = Namespace('http://example.org/')

@mark.parametrize('tree, expected', [
    (SANode(Op.NOT, [SANode(Op.TOP, [])]),
     SANode(Op.BOT, [])),
    (SANode(Op.NOT, [SANode(Op.BOT, [])]),
     SANode(Op.TOP, [])),
    (SANode(Op.AND, [SANode(Op.HASVALUE, [EX.one]),
                     SANode(Op.EQ, [PANode(POp.PROP, [EX.p]),
                                    PANode(POp.PROP, [EX.q])]),
                     SANode(Op.TOP, [])]),
     SANode(Op.AND, [SANode(Op.HASVALUE, [EX.one]),
                     SANode(Op.EQ, [PANode(POp.PROP, [EX.p]),
                                    PANode(POp.PROP, [EX.q])])])),
    (SANode(Op.AND, [SANode(Op.TOP, []), SANode(Op.TOP, [])]),
     SANode(Op.TOP, [])),
    (SANode(Op.AND, [SANode(Op.HASVALUE, [EX.one]),
                     SANode(Op.EQ, [PANode(POp.PROP, [EX.p]),
                                    PANode(POp.PROP, [EX.q])]),
                     SANode(Op.BOT, [])]),
     SANode(Op.BOT, [])),
    (SANode(Op.OR, [SANode(Op.HASVALUE, [EX.one]),
                     SANode(Op.EQ, [PANode(POp.PROP, [EX.p]),
                                    PANode(POp.PROP, [EX.q])]),
                     SANode(Op.BOT, [])]),
     SANode(Op.OR, [SANode(Op.HASVALUE, [EX.one]),
                     SANode(Op.EQ, [PANode(POp.PROP, [EX.p]),
                                    PANode(POp.PROP, [EX.q])])])),
    (SANode(Op.OR, [SANode(Op.BOT, []), SANode(Op.BOT, [])]),
     SANode(Op.BOT, [])),
    (SANode(Op.OR, [SANode(Op.HASVALUE, [EX.one]),
                     SANode(Op.EQ, [PANode(POp.PROP, [EX.p]),
                                    PANode(POp.PROP, [EX.q])]),
                     SANode(Op.TOP, [])]),
     SANode(Op.TOP, [])),
    (SANode(Op.FORALL, [PANode(POp.PROP, [EX.p]), SANode(Op.TOP, [])]),
     SANode(Op.TOP, [])),
    (SANode(Op.FORALL, [PANode(POp.PROP, [EX.p]), SANode(Op.BOT, [])]),
     SANode(Op.COUNTRANGE, [0, 0, PANode(POp.PROP, [EX.p]), SANode(Op.TOP, [])])),
    (SANode(Op.COUNTRANGE, [1, 4, PANode(POp.PROP, [EX.p]), SANode(Op.BOT, [])]),
     SANode(Op.BOT, [])),
    (SANode(Op.COUNTRANGE, [0, 4, PANode(POp.PROP, [EX.p]), SANode(Op.BOT, [])]),
     SANode(Op.TOP, [])),
    (SANode(Op.AND, [SANode(Op.OR, [SANode(Op.TOP, []), SANode(Op.HASVALUE, [EX.one])]), 
                     SANode(Op.HASVALUE, [EX.dantes])]),
     SANode(Op.HASVALUE, [EX.dantes]))
])
def test_clean_parsetree(tree, expected):
    clean = clean_parsetree(tree) 
    print(clean)
    assert clean == expected