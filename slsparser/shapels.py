from typing import List, Optional, Dict
from enum import Enum, auto
import math

from rdflib import Graph
from rdflib import SH, RDF, RDFS
from rdflib.term import URIRef, Literal, BNode, Node
from rdflib.collection import Collection

from slsparser.pathls import parse as pparse
from slsparser.pathls import PANode, POp


class Op(Enum):
    HASVALUE = auto() # Op.HASVALUE val
    NOT = auto() # Op.NOT SANode
    AND = auto() # Op.AND SANode SANode ...
    OR = auto() # Op.OR SANode SANode ...
    TEST = auto() # Op.TEST "testname" argument
    # possible testnames: [testname, element1, element2, ...]
    # - [languageIn ...]
    # - [datatype, xsd:string] or other datatypes
    # - [nodekind, sh:iri] or other: any of the six combinations
    # - [pattern, patternstring, flags] 
    # - [numeric_range, <range_statement>, <value>]
    #   - <range_statement> is one of: min_exclusive, max_exclusive, min_inclusive, max_inclusive
    #   - <value> is an rdflib literal (numeric) value
    #   There is at most one of min_... and at most one of max_... followed by a value 
    # - [length_range, <range_statement>, <value>]
    #   - <range_statement> is one of: min_length, max_length
    #   - <value> is an rdflib literal (numeric) value
    #   There is at most one of min_... and at most one of max_... followed by a value 
    HASSHAPE = auto() # Op.HASSHAPE iri
    GEQ = auto() # Op.GEQ number PANode SANode
    LEQ = auto() # Op.LEQ number PANode SANode
    FORALL = auto() # Op.FORALL number PANode SANode
    EQ = auto() # Op.EQ PANode PANode
    DISJ = auto() # Op.DISJ PANode PANode 
    # for eq(id,p) and disj(id,p) I add id to pathls.POp.ID
    CLOSED = auto() # Op.CLOSED iri iri ...
    LESSTHAN = auto() # Op.LESSTHAN PANode PANode
    LESSTHANEQ = auto() # Op.LESSTHANEQ PANode PANode
    UNIQUELANG = auto() # Op.UNIQUELANG PANode
    TOP = auto() # Op.TOP
    BOT = auto() # Op.BOT

    COUNTRANGE = auto() # Op.COUNTRANGE num num/None PANode SANode

    # optimization constructs
    EXACTLY1 = auto() # exactly one is an optimization operator: mincount 1 and maxcount 1 --> exactly 1


class SANode:  # Shape Algebra Node
    def __init__(self, op: Op, children: List):
        self.op = op
        self.children = children

    def __eq__(self, other):
        """ Overwrite the '==' operator """
        if len(self.children) != len(other.children):
            return False

        same_children = True
        for child_self, child_other in zip(self.children, other.children):
            if type(child_self) == BNode and type(child_other) == BNode:
                continue
            same_children = same_children and child_self == child_other

        return (self.op == other.op) and same_children

    def __repr__(self):
        """ Pretty representation of the SANode tree """
        out = '\n('
        out += str(self.op) + ' '
        for c in self.children:
            for line in c.__repr__().split('\n'):
                out += ' ' + line + '\n'
        out = out[:-1] + ')'
        return out


def _extract_nodeshapes(graph: Graph) -> List[Node]:
    # this defines what nodeshapes are parsed, should follow the spec on what a
    # node shape is. (of type sh:NodeShape, object of sh:node, objects of sh:not...)
    nodeshapes = list(graph.subjects(RDF.type, SH.NodeShape)) + \
                 list(graph.objects(predicate=SH.node)) + \
                 list(graph.objects(predicate=SH.qualifiedValueShape)) + \
                 list(graph.objects(predicate=SH['not']))

    # also members of a shacl list which are objects of sh:and, sh:or, sh:xone
    logical_lists = list(graph.objects(predicate=SH['or'])) + \
                    list(graph.objects(predicate=SH['and'])) + \
                    list(graph.objects(predicate=SH.xone))

    for llist in logical_lists:
        for shapename in Collection(graph, llist):
            if SH.path not in graph.predicates(shapename):
                nodeshapes.append(shapename)

    return nodeshapes


def parse(graph: Graph):
    definitions = {}  # a mapping: shapename, SANode
    target = {}  # a mapping: shapename, target shape

    nodeshapes = _extract_nodeshapes(graph)

    for nodeshape in nodeshapes:
        definitions[nodeshape] = _nodeshape_parse(graph, nodeshape)
        target[nodeshape] = _target_parse(graph, nodeshape)

    # this defines what propertyshapes are parsed, should follow the spec on
    # what a propertyshape is. (of type sh:property, subjects of sh:path, object of sh:property)
    propertyshapes = list(graph.subjects(RDF.type, SH.PropertyShape)) + \
                     list(graph.objects(predicate=SH.property)) + \
                     list(graph.subjects(SH.path))
    
    propertyshapes = list(set(propertyshapes)) # remove duplicates

    for propertyshape in propertyshapes:
        path = _extract_parameter_values(graph, propertyshape, SH.path)[0]
        parsed_path = pparse(graph, path)
        definitions[propertyshape] = _propertyshape_parse(graph, parsed_path,
                                                          propertyshape)
        target[propertyshape] = _target_parse(graph, propertyshape)

    return definitions, target


def _target_parse(graph: Graph, shapename: Node) -> SANode:
    out = SANode(Op.OR, [])
    for tnode in _extract_parameter_values(graph, shapename, SH.targetNode):
        out.children.append(SANode(Op.HASVALUE, [tnode]))

    for tclass in _extract_parameter_values(graph, shapename, SH.targetClass):
        out.children.append(SANode(Op.COUNTRANGE, [
            Literal(1),
            None,
            PANode(POp.PROP, [RDF.type]),
            SANode(Op.HASVALUE, [tclass])]))

    if (shapename, RDF.type, RDFS.Class) in graph:
        out.children.append(SANode(Op.COUNTRANGE, [
            Literal(1),
            None,
            PANode(POp.PROP, [RDF.type]),
            SANode(Op.HASVALUE, [shapename])]))

    for tsub in _extract_parameter_values(graph, shapename,
                                          SH.targetSubjectsOf):
        out.children.append(SANode(Op.COUNTRANGE, [
            Literal(1),
            None,
            PANode(POp.PROP, [tsub]),
            SANode(Op.TOP, [])]))

    for tobj in _extract_parameter_values(graph, shapename,
                                          SH.targetObjectsOf):
        out.children.append(SANode(Op.COUNTRANGE, [
            Literal(1),
            None,
            PANode(POp.INV, [
                PANode(POp.PROP, [tobj])]),
            SANode(Op.TOP, [])]))

    if not out.children:
        out = SANode(Op.BOT, [])

    return out


def _nodeshape_parse(graph: Graph, shapename: Node) -> SANode:
    # Note: all *_parse(...) functions (e.g. _shape_parse(...)) follow the
    # same pattern: they return list[SANode] representing a conjunction of
    # SANodes. This list can be empty.
    conj = _shape_parse(graph, shapename) + \
            _logic_parse(graph, shapename) + \
            _tests_parse(graph, shapename) + \
            _value_parse(graph, shapename) + \
            _in_parse(graph, shapename) + \
            _closed_parse(graph, shapename) + \
            _pair_parse(graph, PANode(POp.ID, []), shapename) # EQ/DISJ id

    if conj:
        return SANode(Op.AND, conj)
    # otherwise, if the shape has no defining components:
    return SANode(Op.TOP, [])  # modeled after behaviour of validators


def _propertyshape_parse(graph: Graph, path: PANode,
                         shapename: Node) -> SANode:
    conj = _card_parse(graph, path, shapename) + \
            _pair_parse(graph, path, shapename) + \
            _qual_parse(graph, path, shapename) + \
            _all_parse(graph, path, shapename) + \
            _lang_parse(graph, path, shapename)
    
    if conj:
        return SANode(Op.AND, conj)
    # otherwise, if the shape has no defining components:
    return SANode(Op.TOP, [])  # modeled after behaviour of validators


def _shape_parse(graph: Graph, shapename: Node) -> list[SANode]:
    shapes = list(graph.objects(shapename, SH.node))
    shapes += list(graph.objects(shapename, SH.property))
    return [SANode(Op.HASSHAPE, [shape]) for shape in shapes]


def _logic_parse(graph: Graph, shapename: Node) -> list[SANode]:
    # Note: RDFlib does not like empty lists. It cannot parse an empty
    # rdf list
    conj_out = []

    for nshape in _extract_parameter_values(graph, shapename, SH['not']):
        conj_out.append(SANode(Op.NOT, [SANode(Op.HASSHAPE, [nshape])]))

    for ashape in _extract_parameter_values(graph, shapename, SH['and']):
        shacl_list = Collection(graph, ashape)
        conj_list = [SANode(Op.HASSHAPE, [s]) for s in shacl_list]
        conj_out.append(SANode(Op.AND, conj_list))

    for oshape in _extract_parameter_values(graph, shapename, SH['or']):
        shacl_list = Collection(graph, oshape)
        disj_list = [SANode(Op.HASSHAPE, [s]) for s in shacl_list]
        conj_out.append(SANode(Op.OR, disj_list))

    for xshape in _extract_parameter_values(graph, shapename, SH.xone):
        shacl_list = Collection(graph, xshape)
        _disj_out = []
        for s in shacl_list:
            single_xone = SANode(Op.AND, [SANode(Op.HASSHAPE, [s])])
            for not_s in shacl_list:
                if s != not_s:
                    single_xone.children.append(
                        SANode(Op.NOT, [SANode(Op.HASSHAPE, [not_s])]))
            _disj_out.append(single_xone)
        if _disj_out:
            conj_out.append(SANode(Op.OR, _disj_out))

    return conj_out


def _tests_parse(graph: Graph, shapename: Node) -> list[SANode]:
    conj_out = []

    # sh:class
    for sh_class in _extract_parameter_values(graph, shapename, SH['class']):
        conj_out.append(
            SANode(Op.COUNTRANGE, [Literal(1), None, PANode(POp.COMP, [
                PANode(POp.PROP, [RDF.type]),
                PANode(POp.KLEENE, [PANode(POp.PROP, [RDFS.subClassOf])])]),
                            SANode(Op.HASVALUE, [sh_class])]))

    # sh:datatype
    for sh_datatype in _extract_parameter_values(graph, shapename,
                                                 SH.datatype):
        conj_out.append(SANode(Op.TEST, ['datatype', sh_datatype]))

    # sh:nodeKind
    for sh_nodekind in _extract_parameter_values(graph, shapename,
                                                 SH.nodeKind):
        conj_out.append(SANode(Op.TEST, ['nodekind', sh_nodekind]))

    # sh:minInclusive
    for sh_minincl in _extract_parameter_values(graph, shapename,
                                                SH.minInclusive):
        conj_out.append(SANode(Op.TEST, ['min_inclusive', sh_minincl]))

    # sh:maxInclusive
    for sh_maxincl in _extract_parameter_values(graph, shapename,
                                                SH.maxInclusive):
        conj_out.append(SANode(Op.TEST, ['max_inclusive', sh_maxincl]))

    # sh:minExclusive
    for sh_minexcl in _extract_parameter_values(graph, shapename,
                                                SH.minExclusive):
        conj_out.append(SANode(Op.TEST, ['min_exclusive', sh_minexcl]))

    # sh:maxExclusive
    for sh_maxexcl in _extract_parameter_values(graph, shapename,
                                                SH.maxExclusive):
        conj_out.append(SANode(Op.TEST, ['max_exclusive', sh_maxexcl]))

    # sh:minLength
    for sh_minlen in _extract_parameter_values(graph, shapename, SH.minLength):
        conj_out.append(SANode(Op.TEST, ['min_length', sh_minlen]))

    # sh:maxLength
    for sh_maxlen in _extract_parameter_values(graph, shapename, SH.maxLength):
        conj_out.append(SANode(Op.TEST, ['max_length', sh_maxlen]))

    # sh:pattern
    flags = [sh_flags for sh_flags in _extract_parameter_values(graph,
                                                                shapename,
                                                                SH.flags)]
    for sh_pattern in _extract_parameter_values(graph, shapename, SH.pattern):
        escaped_pattern = _escape_backslash(str(sh_pattern))
        # something strange is going on with character escapes
        # if a pattern contains a double backslash 'hello\\w' for example
        # it will be read by the rdflib parser as 'hello\w'
        conj_out.append(SANode(Op.TEST, ['pattern', escaped_pattern, flags]))

    return conj_out


def _value_parse(graph: Graph, shapename: Node) -> list[SANode]:
    conj_out = []
    for sh_value in _extract_parameter_values(graph, shapename, SH.hasValue):
        conj_out.append(SANode(Op.HASVALUE, [sh_value]))
    return conj_out


def _in_parse(graph: Graph, shapename: Node) -> list[SANode]:
    conj_out = []
    for sh_in in _extract_parameter_values(graph, shapename, SH['in']):
        shacl_list = Collection(graph, sh_in)
        disj = SANode(Op.OR, [])
        for val in shacl_list:
            disj.children.append(SANode(Op.HASVALUE, [val]))
        conj_out.append(disj)
    return conj_out


def _closed_parse(graph: Graph, shapename: Node) -> list[SANode]:
    if (shapename, SH.closed, Literal(True)) not in graph:
        return []

    ignored = _extract_parameter_values(graph, shapename,
                                        SH.ignoredProperties)
    sh_ignored = []
    for ig in ignored:
        shacl_list = Collection(graph, ig)
        sh_ignored += list(shacl_list)

    direct_props = []
    for pshape in _extract_parameter_values(graph, shapename, SH.property):
        path = _extract_parameter_values(graph, pshape, SH.path)[0]
        if type(path) == URIRef:
            direct_props.append(path)

    closed_props = sh_ignored + direct_props
    children = [PANode(POp.PROP, [prop]) for prop in closed_props]
    return [SANode(Op.CLOSED, children)]


def _card_parse(graph: Graph, path: PANode, shapename: Node) -> list[SANode]:
    # TODO: no need anymore fore conj_out
    conj_out = []

    infinite = Literal(999999) # TODO: elegance
    smallest_min = infinite
    for min_card in _extract_parameter_values(graph, shapename, SH.minCount):
        if int(min_card) < int(smallest_min):
            smallest_min = min_card
        # conj_out.append(SANode(Op.GEQ, [min_card, path,
        #                                 SANode(Op.TOP, [])]))

    min_infinite = Literal(-1)
    largest_max = min_infinite
    for max_card in _extract_parameter_values(graph, shapename, SH.maxCount):
        if max_card > largest_max:
            largest_max = max_card
        # conj_out.append(SANode(Op.LEQ, [max_card, path,
        #                                 SANode(Op.TOP, [])]))
    
    if smallest_min != infinite or largest_max != min_infinite:
        conj_out.append(SANode(Op.COUNTRANGE, [smallest_min if smallest_min != infinite else Literal(0),
                                            largest_max if largest_max != min_infinite else None,
                                            path, SANode(Op.TOP, [])]))
    return conj_out


def _pair_parse(graph: Graph, path: PANode, shapename: Node) -> list[SANode]:
    conj_out = []

    # sh:equals
    for eq in _extract_parameter_values(graph, shapename, SH.equals):
        conj_out.append(SANode(Op.EQ, [path,
                                       pparse(graph, eq)]))

    # sh:disjoint
    for disj in _extract_parameter_values(graph, shapename, SH.disjoint):
        conj_out.append(SANode(Op.DISJ, [path,
                                         pparse(graph, disj)]))

    # sh:lessThan
    for lt in _extract_parameter_values(graph, shapename, SH.lessThan):
        conj_out.append(SANode(Op.LESSTHAN, [path,
                                             pparse(graph, lt)]))

    # sh:lessThanEq
    for lte in _extract_parameter_values(graph, shapename,
                                         SH.lessThanOrEquals):
        conj_out.append(SANode(Op.LESSTHANEQ, [path,
                                               pparse(graph, lte)]))

    return conj_out


def _qual_parse(graph: Graph, path: PANode, shapename: Node) -> list[SANode]:
    qual = _extract_parameter_values(graph, shapename,
                                     SH.qualifiedValueShape)
    qual_min = _extract_parameter_values(graph, shapename,
                                         SH.qualifiedMinCount)
    qual_max = _extract_parameter_values(graph, shapename,
                                         SH.qualifiedMaxCount)

    sibl = []
    if (shapename, SH.qualifiedValueShapesDisjoint, Literal(True)) in graph:
        parents = graph.subjects(SH.property, shapename)
        for parent in parents:
            for propshape in graph.objects(parent, SH.property):
                sibl += list(graph.objects(propshape, SH.qualifiedValueShape))

    conj_out = []
    for qvs in qual:
        result_qvs = SANode(Op.HASSHAPE, [qvs])  # normal qualifiedvalueshape

        if len(sibl) > 0:  # if there is a sibling, wrap it in an Op.AND
            result_qvs = SANode(Op.AND, [result_qvs])

        # for every sibling, add its negation, unless it is itself
        for s in sibl:
            if s == qvs:
                continue
            result_qvs.children.append(SANode(Op.NOT, [
                SANode(Op.HASSHAPE, [s])]))

        infinite = Literal(999999) # TODO: elegance
        smallest_min = infinite
        for count in qual_min:
            if int(count) < int(smallest_min):
                smallest_min = count
            # conj_out.append(SANode(Op.GEQ, [count, path, result_qvs]))
        min_infinite = Literal(-1)
        largest_max = min_infinite
        for count in qual_max:
            if count > largest_max:
                largest_max = count
            # conj_out.append(SANode(Op.LEQ, [count, path, result_qvs]))

        conj_out.append(SANode(Op.COUNTRANGE, [smallest_min if smallest_min != infinite else Literal(0),
                                               largest_max if largest_max != min_infinite else None,
                                               path, result_qvs]))

    return conj_out


def _all_parse(graph: Graph, path: PANode, shapename: Node) -> list[SANode]:
    conj_out = []
    forall_conj = _shape_parse(graph, shapename) + \
                  _logic_parse(graph, shapename) + \
                  _tests_parse(graph, shapename) + \
                  _in_parse(graph, shapename) + \
                  _closed_parse(graph, shapename)
    if forall_conj:
        conj_out.append(SANode(Op.FORALL, [path, SANode(Op.AND, forall_conj)]))

    for component in _value_parse(graph, shapename):
        conj_out.append(SANode(Op.COUNTRANGE, [Literal(1), None, path, component]))

    return conj_out


def _lang_parse(graph: Graph, path: PANode, shapename: Node) -> list[SANode]:
    conj_out = []

    # sh:languageIn
    literal_list = []
    for langin in _extract_parameter_values(graph, shapename, SH.languageIn):
        shacl_list = Collection(graph, langin)
        literal_list += [tag for tag in shacl_list]

    if literal_list:
        _out = SANode(Op.TEST, ['languageIn', literal_list])
        conj_out.append(SANode(Op.FORALL, [path, _out]))

    # sh:uniqueLang
    if (shapename, SH.uniqueLang, Literal(True)) in graph:
        conj_out.append(SANode(Op.UNIQUELANG, [path]))

    return conj_out


def _extract_parameter_values(graph: Graph, shapename: Node, parameter: URIRef) -> List[Node]:
    return list(graph.objects(shapename, parameter))


def _escape_backslash(string):
    new_string = ''
    for char in string:
        if char == '\\':
            new_string += '\\\\'
        else:
            new_string += char
    return new_string
