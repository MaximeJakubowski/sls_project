from pytest import mark

from rdflib.namespace import RDF, RDFS, XSD, SH
from rdflib import Graph, Namespace, Literal

from slsparser.shapels import parse, Op, SANode
from slsparser.pathls import PANode, POp
from slsparser.utilities import expand_shape


EX = Namespace('http://ex.tt/')


@mark.parametrize('graph_file, expected', [
    ('shape_basic.ttl',
     {EX.shape: SANode(Op.HASSHAPE, [EX.oner], SH.PropertyConstraintComponent),
      EX.oner: SANode(Op.COUNTRANGE, [
          Literal(1),
          None,
          PANode(POp.PROP, [EX.r]),
          SANode(Op.TOP, [])], SH.MinCountConstraintComponent)}),
    ('shape_logic.ttl',
     {EX.shape: SANode(Op.AND, [
         SANode(Op.NOT, [SANode(Op.HASSHAPE, [EX.not1])], SH.NotConstraintComponent),
         SANode(Op.AND, [
            SANode(Op.HASSHAPE, [EX.and1]),
            SANode(Op.HASSHAPE, [EX.and2]),
            SANode(Op.HASSHAPE, [EX.and3])], SH.AndConstraintComponent),
         SANode(Op.OR, [
             SANode(Op.HASSHAPE, [EX.or1]),
             SANode(Op.HASSHAPE, [EX.or2]),
             SANode(Op.HASSHAPE, [EX.or3])], SH.OrConstraintComponent),
         SANode(Op.OR, [
             SANode(Op.AND, [
                 SANode(Op.HASSHAPE, [EX.xone1]),
                 SANode(Op.NOT, [SANode(Op.HASSHAPE, [EX.xone2])]),
                 SANode(Op.NOT, [SANode(Op.HASSHAPE, [EX.xone3])])]),
             SANode(Op.AND, [
                 SANode(Op.HASSHAPE, [EX.xone2]),
                 SANode(Op.NOT, [SANode(Op.HASSHAPE, [EX.xone1])]),
                 SANode(Op.NOT, [SANode(Op.HASSHAPE, [EX.xone3])])]),
             SANode(Op.AND, [
                 SANode(Op.HASSHAPE, [EX.xone3]),
                 SANode(Op.NOT, [SANode(Op.HASSHAPE, [EX.xone1])]),
                 SANode(Op.NOT, [SANode(Op.HASSHAPE, [EX.xone2])])])],
                SH.XoneConstraintComponent)])}),
    ('shape_tests.ttl',
     {EX.shape: SANode(Op.AND, [
         SANode(Op.COUNTRANGE, [Literal(1), 
                                None,
                                PANode(POp.COMP, [
                                    PANode(POp.PROP, [RDF.type]), 
                                    PANode(POp.KLEENE, [PANode(POp.PROP, [RDFS.subClassOf])])]),
                                SANode(Op.HASVALUE, [EX['class1']])], SH.ClassConstraintComponent),
         SANode(Op.TEST, [SH.DatatypeConstraintComponent, XSD.string], SH.DatatypeConstraintComponent),
         SANode(Op.TEST, [SH.NodeKindConstraintComponent, SH.IRI], SH.NodeKindConstraintComponent),
         SANode(Op.TEST, ['numeric_range', SH.MinExclusiveConstraintComponent, Literal(1), SH.MaxInclusiveConstraintComponent, Literal(10)]),
         SANode(Op.TEST, ['length_range', SH.MinLengthConstraintComponent, Literal(1), SH.MaxLengthConstraintComponent, Literal(10)]),
         SANode(Op.TEST, [SH.PatternConstraintComponent, '^B', [Literal('i')]], SH.PatternConstraintComponent)])}),
    ('shape_value_in_closed.ttl',
     {EX.shape: SANode(Op.AND, [
         SANode(Op.HASSHAPE, [EX.pshape1], SH.PropertyConstraintComponent),
         SANode(Op.HASSHAPE, [EX.pshape2], SH.PropertyConstraintComponent),
         SANode(Op.HASVALUE, [EX.val1], SH.HasValueConstraintComponent),
         SANode(Op.OR, [
             SANode(Op.HASVALUE, [EX.val2]),
             SANode(Op.HASVALUE, [EX.val3]),
             SANode(Op.HASVALUE, [EX.val4])], SH.InConstraintComponent),
         SANode(Op.CLOSED, [PANode(POp.PROP, [EX.p1]), PANode(POp.PROP, [EX.p2]), PANode(POp.PROP, [EX.p3])])], SH.ClosedConstraintComponent),
      EX.pshape1: SANode(Op.COUNTRANGE, [Literal(1), None, PANode(POp.PROP, [EX.p3]),
                                         SANode(Op.HASVALUE, [EX.val5])], SH.HasValueConstraintComponent),
      EX.pshape2: SANode(Op.COUNTRANGE, [Literal(1), 
                                         None,
                                         PANode(POp.COMP, [
                                            PANode(POp.PROP, [EX.p4]),
                                            PANode(POp.PROP, [EX.p5])
                                         ]),
                                         SANode(Op.HASVALUE, [EX.val6])], SH.HasValueConstraintComponent)}),
    ('shape_card_qual.ttl',
     {EX.shape1: SANode(Op.COUNTRANGE, [Literal(3), Literal(6),
                                        PANode(POp.PROP, [EX.p1]),
                                        SANode(Op.TOP, [])]),
      EX.shape: SANode(Op.AND, [
          SANode(Op.HASSHAPE, [EX.shape2]),
          SANode(Op.HASSHAPE, [EX.shape3])]),
      EX.shape2: SANode(Op.COUNTRANGE, [Literal(4), Literal(8),
                                PANode(POp.PROP, [EX.p2]),
                                SANode(Op.HASSHAPE, [EX.shape4])]),
      EX.shape3: SANode(Op.COUNTRANGE, [Literal(7), None,
                                        PANode(POp.PROP, [EX.p3]),
                                        SANode(Op.AND, [
                                            SANode(Op.HASSHAPE, [EX.shape5]),
                                            SANode(Op.NOT, [
                                                SANode(Op.HASSHAPE,
                                                        [EX.shape4])])])])}),
    ('shape_pair.ttl',
     {EX.shape: SANode(Op.AND, [
        SANode(Op.EQ, [PANode(POp.PROP, [EX.p1]),
                       PANode(POp.PROP, [EX.p2])]),
        SANode(Op.DISJ, [PANode(POp.PROP, [EX.p1]),
                         PANode(POp.PROP, [EX.p3])]),
        SANode(Op.LESSTHAN, [PANode(POp.PROP, [EX.p1]),
                             PANode(POp.PROP, [EX.p4])]),
        SANode(Op.LESSTHANEQ, [PANode(POp.PROP, [EX.p1]),
                               PANode(POp.PROP, [EX.p5])])])}),
    ('shape_all.ttl',
     {EX.shape: SANode(Op.AND, [
         SANode(Op.FORALL, [
             PANode(POp.PROP, [EX.p1]),
             SANode(Op.TEST, [SH.NodeKindConstraintComponent, SH.Literal])]),
         SANode(Op.COUNTRANGE, [Literal(1), 
                                None,
                                PANode(POp.PROP, [EX.p1]),
                                SANode(Op.HASVALUE, [Literal(10)])])])}),
    ('shape_lang.ttl',
     {EX.shape: SANode(Op.AND, [
        SANode(Op.FORALL, [PANode(POp.PROP, [EX.p1]),
                           SANode(Op.TEST, [SH.LanguageInConstraintComponent, [Literal('en'), Literal('nl')]])]),
        SANode(Op.UNIQUELANG, [PANode(POp.PROP, [EX.p1])])])}),
    ('shape_ideqdisj.ttl',
     {EX.shape1: SANode(Op.EQ, [PANode(POp.ID, []), PANode(POp.PROP, [EX.p])]),
      EX.shape2: SANode(Op.DISJ, [PANode(POp.ID, []), PANode(POp.PROP, [EX.p])])})])
def test_shape_parsing(graph_file, expected):
    print('==========================')
    print('==========================')
    print('==========================')
    print('==========================')
    print('==========================')
    g = Graph()
    g.parse(f'./tests/sls_testfiles/{graph_file}')
    g.namespace_manager.bind('rdf', RDF)
    # print('********* PARSED GRAPH  *********')
    # for s, p, o in g:
    #     print(s.n3(g.namespace_manager),
    #           p.n3(g.namespace_manager),
    #           o.n3(g.namespace_manager))

    parsed = parse(g)[0]

    print('********* SHAPE PARSING *********')
    for key in list(expected):
        #print('------PARSED------')
        #print(key, parsed[key])
        opt = parsed[key]
        print('------OPTIMIZED------')
        print(opt)
        print('------EXPECTED------')
        print(expected[key])
        assert opt == expected[key]


@mark.parametrize('graph_file, expected', [
    ('expand_test1.ttl',
     SANode(Op.COUNTRANGE, [Literal(1), None,
                            PANode(POp.PROP, [EX.r1]),
                            SANode(Op.HASVALUE, [Literal(1)])]))])
def test_shape_expansion(graph_file, expected):
    g = Graph()
    g.parse(f'./tests/sls_testfiles/{graph_file}')
    g.namespace_manager.bind('rdf', RDF)

    parsed = parse(g)[0]

    opt_schema = dict()
    for name in parsed.keys():
        opt_schema[name] = parsed[name]

    expanded = expand_shape(opt_schema, opt_schema[EX.shape])

    assert expanded == expected


