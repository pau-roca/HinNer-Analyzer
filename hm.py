from __future__ import annotations
from antlr4 import *
from hmLexer import hmLexer
from hmParser import hmParser
from hmVisitor import hmVisitor
import streamlit as st
from hmVisitor import *
import graphviz
import pandas as pd
from dataclasses import dataclass

# PER CASA
# from typing import Union

# TYPE STRUCTURE


@dataclass
class Constant:
    ty: str


@dataclass
class Variable:
    ty: str


@dataclass
# To the left there will only ever be a Constant or a Variable
class Application:
    esq: Type
    dre: Type


# CASA
# Type = Union[Constant, Variable, Application]
# UNI
Type = Constant | Variable | Application

# PYTHON TREE


class Buit:
    pass


@dataclass
class Node:
    val: str
    label: Type
    esq: Arbre
    dre: Arbre


# CASA
# Arbre = Union[Node, Buit]
# UNI
Arbre = Node | Buit


class TreeVisitor(hmVisitor):
    def __init__(self):
        self.nivell = 0
        self.symbols = {}

    def visitRoot(self, ctx):
        l = list(ctx.getChildren())
        for el in l:
            tree = self.visit(el)
            if tree is not None:
                return self.symbols, tree
        return self.symbols, None

    def visitType_decl(self, ctx):
        [name, _, typ] = list(ctx.getChildren())
        self.symbols[name.getText()] = self.visit(typ)

    def visitTypeApl(self, ctx):
        [typ, _, typ2] = list(ctx.getChildren())
        typ2visited = self.visit(typ2)
        return Application(Constant(typ.getText()), typ2visited)

    def visitTypePlain(self, ctx):
        [typ] = list(ctx.getChildren())
        return Constant(typ.getText())

    def visitParentesis(self, ctx):
        [_, expr, _] = list(ctx.getChildren())
        return self.visit(expr)

    def visitAplicacio(self, ctx):
        [expr1, expr2] = list(ctx.getChildren())
        self.nivell += 1
        l = self.visit(expr1)
        r = self.visit(expr2)
        self.nivell -= 1
        return Node("@", None, l, r)

    def visitAbstraccio(self, ctx):
        [_, var, _, expr] = list(ctx.getChildren())
        self.nivell += 1
        l = Node(str(var), None, Buit, Buit)
        r = self.visit(expr)
        self.nivell -= 1
        return Node("λ", None, l, r)

    def visitNat(self, ctx):
        [nat] = list(ctx.getChildren())
        return Node(nat.getText(), None, Buit, Buit)

    def visitVar(self, ctx):
        [var] = list(ctx.getChildren())
        return Node(var.getText(), None, Buit, Buit)

    def visitSym(self, ctx):
        [sym] = list(ctx.getChildren())
        return Node(sym.getText(), None, Buit, Buit)

# Aquesta classe converteix un arbre de tipus algebraic de pyhton
# a un arbre de la llibreria graphviz llesta per imprimir per pantalla amb
# streamlit


class python2graphviz():
    def __init__(self):
        self.id = 0

    def convert(self, tree):
        g = graphviz.Digraph()
        self.convert_i(g, tree)
        return g

    def convert_i(self, g, tree):
        if tree == Buit:
            return -1
        self.id += 1
        myId = self.id

        g.node(str(myId), tree.val + '\n' + type2str(tree.label))

        f1 = self.convert_i(g, tree.esq)
        f2 = self.convert_i(g, tree.dre)

        if f1 != -1:
            g.edge(str(myId), str(f1))
        if f2 != -1:
            g.edge(str(myId), str(f2))

        return myId


class AST_Labeler():
    def __init__(self):
        self.id = 0

    # retorna un nou tipus anonim (t0, t1, t2...)
    def getIdNode(self):
        self.id += 1
        return Variable('t' + str(self.id - 1))

    def anotate(self, tree, symbols):
        if tree == Buit:
            return Buit
        l = self.anotate(tree.esq, symbols)
        r = self.anotate(tree.dre, symbols)

        isApplication = tree.val in ['@', 'λ']

        if tree.val in symbols and not isApplication:
            return Node(tree.val, symbols[tree.val], l, r)
        else:
            myId = self.getIdNode()
            if not isApplication:
                symbols[tree.val] = myId
            return Node(tree.val, myId, l, r)


class AST_Infering():
    def __init__(self):
        self.symbols = {}
        self.error_sent = False

    # adds a new type to the infered symbol table
    def addType(self, variable, typ):
        self.symbols[type2str(variable)] = typ

    # returns the type of a variable if any
    def getType(self, variable):
        if not self.hasType(variable):
            return None
        return self.symbols[type2str(variable)]

    # tells whether a variable has a type assigned or not
    def hasType(self, variable):
        return type2str(variable) in self.symbols

    # recovers a previously assigned type, if any
    def recoverType(self, label):
        if isinstance(label, Variable) and self.hasType(label):
            return self.getType(label)
        return label

    # applies the inferred types to any labels that havent been changed yet
    def applyInferedTypes(self, tree):
        if tree == Buit:
            return
        if isinstance(tree.label, Variable):
            if type2str(tree.label) in self.symbols:
                tree.label = self.symbols[type2str(tree.label)]
        self.applyInferedTypes(tree.esq)
        self.applyInferedTypes(tree.dre)

    def infer(self, tree):
        if tree == Buit:
            return
        self.infer(tree.esq)
        self.infer(tree.dre)
        if not isinstance(tree.label, Variable):
            return

        if tree.val == '@':
            inferedType = self.infer_apl(tree.esq.label, tree.dre.label)
            self.addType(tree.label, inferedType)
            tree.label = inferedType
        if tree.val == 'λ':
            inferedType = self.infer_abs(tree.esq.label, tree.dre.label)
            self.addType(tree.label, inferedType)
            tree.label = inferedType

        if tree.label == Constant('Error'):
            return 'Error'
        return self.symbols

    # assumes that the left element of a type is either a constant or a
    # variable
    def infer_apl(self, leftType, rightType):
        ty1, ty2 = leftType, rightType
        # get the actual element to compare
        if isinstance(leftType, Application):
            ty1 = leftType.esq
        if isinstance(rightType, Application):
            ty2 = rightType.esq

        # recover any previously assigned types
        ty1 = self.recoverType(ty1)
        ty2 = self.recoverType(ty2)

        # si un es variable i l altre constant, assignem la constant a la
        # variable
        if isinstance(ty1, Constant) and isinstance(ty2, Variable):
            self.addType(ty2, ty1)
            ty2 = ty1
        if isinstance(ty1, Variable) and isinstance(ty2, Constant):
            self.addType(ty1, ty2)
            ty2 = ty1

        if ty1 == ty2:
            # try to find the biggest match, recursively check to the right
            # until you fail
            if isinstance(
                    leftType,
                    Application) and isinstance(
                    rightType,
                    Application):
                extendedMatch = self.infer_apl(leftType.dre, rightType.dre)
                if extendedMatch == Constant('Error'):
                    return leftType.dre
                else:
                    return extendedMatch

            elif isinstance(leftType, Application):
                return leftType.dre

        # error control
        if not self.error_sent:
            if type2str(ty1) == type2str(ty2):
                st.write('Type error: types of the same length')
            else:
                st.write(
                    'Type error: ' +
                    type2str(ty1) +
                    ' vs. ' +
                    type2str(ty2))
            self.error_sent = True
        return Constant('Error')

    def infer_abs(self, leftType, rightType):
        # recover any previously assigned types
        leftType = self.recoverType(leftType)
        rightType = self.recoverType(rightType)

        # si un es variable i l altre constant, assignem la constant a la
        # variable
        if isinstance(leftType, Constant) and isinstance(rightType, Variable):
            self.addType(rightType, leftType)
            rightType = leftType
        if isinstance(leftType, Variable) and isinstance(rightType, Constant):
            self.addType(leftType, rightType)
            rightType = leftType

        return Application(leftType, rightType)


def type2str(typ):
    if typ is None:
        return ''
    if isinstance(typ, Constant):
        return typ.ty
    if isinstance(typ, Variable):
        return typ.ty
    return type2str(typ.esq) + '->' + type2str(typ.dre)


def dic2dataframe(dic):
    newdic = {}
    for d in dic:
        newdic[d] = type2str(dic[d])
    return pd.DataFrame.from_dict(newdic, orient="index", columns=["Tipus"])


def executar_tot():
    input_stream = InputStream(msg)
    lexer = hmLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = hmParser(token_stream)
    tree = parser.root()
    if parser.getNumberOfSyntaxErrors() == 0:

        # parse tree
        visitor = TreeVisitor()
        symbols, tree = visitor.visit(tree)
        # print symbol table
        st.dataframe(dic2dataframe(symbols), use_container_width=True)
        # process tree if any
        if tree is not None:
            converter = python2graphviz()
            # anotate tree and print it
            anotator = AST_Labeler()
            tree = anotator.anotate(tree, symbols)
            st.graphviz_chart(converter.convert(tree))
            # infer types on tree
            infering = AST_Infering()
            inferedTypes = infering.infer(tree)
            if inferedTypes != 'Error':
                infering.applyInferedTypes(tree)
                st.graphviz_chart(converter.convert(tree))
                st.dataframe(
                    dic2dataframe(inferedTypes),
                    use_container_width=True)

    else:
        st.write(parser.getNumberOfSyntaxErrors(), 'errors de sintaxi.')
        st.write(tree.toStringTree(recog=parser))
        print(parser.getNumberOfSyntaxErrors(), 'errors de sintaxi.')
        print(tree.toStringTree(recog=parser))


st.title('Analitzador HinNer')
msg = st.text_area('Expressió:', height=275)

if st.button('Fer'):
    executar_tot()
