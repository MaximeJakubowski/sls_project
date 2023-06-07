# SHACL Logical Syntax parser

This project is in the experimental phase. It was originally used as a sub-package for experiments done for our work on [Provenance for SHACL](https://github.com/Shape-Fragments), [paper](https://openproceedings.org/2023/conf/edbt/paper-3.pdf).

However, this logical syntax parser can be used for multiple purposes so the idea is to extend it and publish it as its own package.

## Features

The idea is to have the following functionality:
- Parsing a SHACL shapes graph into a parse tree of the [SHACL Logical Syntax](https://www.mjakubowski.info/files/shacl.pdf)
- Given a parse tree of the logical syntax, output a SHACL shapes graph

This framework allows for more shapes than you currently can write with W3C SHACL. However, every shape that you can write in W3C SHACL can be written in this framework. 

## Data Structure

When you parse a SHACL shapes graph, the output is a tuple of two dictionaries.
- The first dictionary represent all the shape definitions. The keys are rdflib IdentifiedNode objects. The values are SANode objects.
- The second dictionary represent all target statements. The keys are rdflib IdentifiedNode objects. The values are SANode objects.

### SANodes
A SANode is an object that represents a shape. The underlying idea is that this is a syntax tree of the logical syntax representation of a shape. It consists of two components:
- a type, which is an Enum called Op
- a list of children, the elements of this list are dependent on the Op

### Op
There are more/other Op types than there are defined in the logical syntax in the paper. Mostly out of efficiency conciderations.
- Op.HASVALUE has one child which is an rdflib IdentifiedNode or Literal. Only the value itself satisfies this shape.
- Op.TEST has different children, depending on what kind of test it represents. The list of children can be:
    - ['datatype', {datatypeIRI}]
    - ['nodekind', {nodekindIRI}]
    - ['']

### PANodes
A PANode is an object that represent a path expression. It is very similar to the structure of the SANode. The underlying idea is that this is a syntax tree of the path expressions. It consists of two components:
- a type, which is an Enum called POp
- a list of children, the elements of this list are dependent on the POp

### POp
There are several POp types:
- POp.PROP has one child, which is an URIRef representing a property name. It represents a simple property name.
- POp.INV has one child, which is a PANode. It represents the inverse of that PANode.
- POp.ZEROORONE has one child, which is a PANode. It represents the zero-or-one path expression.
- POp.ALT has one or more children, which are PANodes. It represents the alternative path expression.
- POp.KLEENE has one child, which is a PANode. It represents the zero-or-more path expression.
- POp.COMP has one or more children, which are PANodes. It represents the sequence path expression.
- POp.ID has no children. It represents the identity path expression. It is used to represent the path from which every node can only reach itself. It has no W3C SHACL standard counterpart, however it is useful to express some shapes.

## Use

The package is to be used for my research purposes, but it may be useful for other applications. If you are interested, please let me know. Currently, I'm working on an [alternative SHACL syntax](https://github.com/MaximeJakubowski/shacl_esyntax) based on the SHACL Logical Syntax.