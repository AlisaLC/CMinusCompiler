# C-Minus Compiler
## Introduction
This is a compiler for the C-Minus language, which is a subset of the C language. The compiler is written in Python.
The compiler is divided into 4 parts:
1. Token Scanner
1. Top-Down Parser
1. Semantic Analyzer
1. Intermediate Code Generator

## C-Minus Language
The C-Minus language is a subset of the C language. It supports the following features:
1. Data types: int, void
1. Control flow: if-else, while
1. Operators: +, -, *, <, ==, =
1. Functions: function declaration, function call, return statement, parameter passing
1. Variables: global variables, local variables, scope
1. Recursion
1. Arrays: one-dimensional arrays
1. Comments: //, /* */

## Token Scanner
The token scanner is implemented using regular expressions. The following tokens are supported:
1. Keywords: int, void, if, else, while, return
1. Operators: +, -, *, <, ==, =
1. Separators: ;, ,, (, ), [, ], {, }
1. Identifiers: [a-zA-Z][a-zA-Z0-9]*
1. Integers: [0-9]+
1. Comments: //, /* */

## Top-Down Parser
The top-down parser is implemented using recursive descent with graph approach.

## Semantic Analyzer
The semantic analyzer is implemented using symbol table and type checking. The symbol table is implemented using hash table. The type checking is implemented using stack machine.

## Intermediate Code Generator
The intermediate code generator is implemented using three-address code. The three-address code is implemented using stack machine.