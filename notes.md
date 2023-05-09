'numeric_range' als eerste element van een test waarbij er een sequentie van min/max_in/exclusive tests

Dit niet:
<!-- SANode(Op.TEST, 
      ['numeric_range', 'min_inclusive', rdflib.Literal(1),
       'max_exclusive', rdflib.Literal(5),
       'min_inclusive', rdflib.Literal(-3.14)]) -->

'length_range' zelfde idee voor 'min_length', 'max_length'

==> numeric ranges (en length ranges) slim aanpakken: hoogstens 1 min_... en hoogstens 1 max_...


Op.COUNTRANGE mincount maxcount property shape

Dit niet:
<!-- SANode(Op.COUNTRANGE, 
      ['mincount', rdflib.Literal(1),
       'mincount', rdflib.Literal(5),
       'maxcount', rdflib.Literal(3),
       'property', PANode(...),
       'shape', SANode(...)]) -->

==> countrange slim aanpakken: [1 None PANode SANode]


Voorbeeld van PANodes in geval Ceel:
PANode(POp.PROP, [rdflib.URIRef(...)])

PANode(POp.INV, [PANode(POp.PROP, [rdflib.URIRef(...)])])