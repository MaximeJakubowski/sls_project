# SHACL Logical Syntax parser

This project is in the experimental phase. It was originally used as a sub-package for experiments done for our work on [Provenance for SHACL](https://github.com/Shape-Fragments), [paper](https://openproceedings.org/2023/conf/edbt/paper-3.pdf).

However, this logical syntax parser can be used for multiple purposes so the idea is to extend it and publish it as its own package.

## Features

The idea is to have the following functionality:
- Parsing a SHACL shapes graph into a parse tree of the [SHACL Logical Syntax](https://www.mjakubowski.info/files/shacl.pdf)
- Given a parse tree of the logical syntax, output a SHACL shapes graph

## Data Structure

When you parse a SHACL shapes graph, the output is a tuple of two dictionaries.
- The first dictionary represent all the shape definitions. The keys are rdflib IdentifiedNode objects. The values are SANode objects.
- The second dictionary represent all target statements. The keys are rdflib IdentifiedNode objects. The values are SANode objects.

### SANodes
An SANode is an object that represents a shape. The underlying idea is that this is a syntax tree of the logical syntax representation of a shape. It consists of two components:
- a type, which is an Enum called Op
- a list of children, the elements of this list are dependent on the Op

### Op
There are more/other Op types than there are defined in the logical syntax in the paper. Mostly out of efficiency conciderations.
- Op.HASVALUE has one child which is an rdflib IdentifiedNode or Literal
- Op.TEST has different children, depending on what kind of test it represents.


## Use

The package is to be used for my research purposes, but it may be useful for other applications. If you are interested, please let me know. Currently, I'm working on an [alternative SHACL syntax](https://github.com/MaximeJakubowski/shacl_esyntax) based on the SHACL Logical Syntax.