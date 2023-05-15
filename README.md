# SHACL Logical Syntax parser

This project is in the experimental phase. It was originally used as a sub-package for experiments done for our work on [Provenance for SHACL](https://github.com/Shape-Fragments), [paper](https://openproceedings.org/2023/conf/edbt/paper-3.pdf).

However, this logical syntax parser can be used for multiple purposes so the idea is to extend it and publish it as its own package.

## Features

The idea is to have the following functionality:
- Parsing a SHACL shapes graph into a parse tree of the [SHACL Logical Syntax](https://www.mjakubowski.info/files/shacl.pdf)
- Given a parse tree of the logical syntax, output a SHACL shapes graph

## Use

The package is to be used for my research purposes, but it may be useful for other applications. If you are interested, please let me know. Currently, I'm working on an [alternative SHACL syntax](https://github.com/MaximeJakubowski/shacl_esyntax) based on the SHACL Logical Syntax.