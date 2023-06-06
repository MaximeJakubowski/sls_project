from typing import Optional, Dict
from rdflib import Literal
from slsparser.shapels import SANode, Op


def expand_shape(definitions: Dict, node: SANode) -> SANode:
    """Removes all hasshape references and replaces them with shapes"""

    if node.op == Op.HASSHAPE:
        if node.children[0] not in definitions:
            return SANode(Op.TOP, [])  # mimics real SHACL semantics
        return expand_shape(definitions, definitions[node.children[0]])

    new_children = []
    for child in node.children:
        new_child = child
        if type(child) == SANode:
            new_child = expand_shape(definitions, child)
        new_children.append(new_child)
    return SANode(node.op, new_children)


def negation_normal_form(node: SANode) -> SANode:
    # The input should be a node without that has no HASSHAPE in its tree (it is expanded)
    if node.op != Op.NOT:
        new_children = []
        for child in node.children:
            if type(child) != SANode:
                new_children.append(child)
            else:
                new_children.append(negation_normal_form(child))
        return SANode(node.op, new_children)

    nnode = node.children[0]
    if nnode.op == Op.AND:
        new_children = []
        for child in nnode.children:
            new_children.append(
                negation_normal_form(SANode(Op.NOT, [child])))
        return SANode(Op.OR, new_children)

    if nnode.op == Op.OR:
        new_children = []
        for child in nnode.children:
            new_children.append(
                negation_normal_form(SANode(Op.NOT, [child])))
        return SANode(Op.AND, new_children)

    if nnode.op == Op.NOT:
        return nnode.children[0]

    if nnode.op == Op.GEQ:
        return SANode(Op.LEQ, [Literal(int(nnode.children[0]) - 1),
                               nnode.children[1],
                               negation_normal_form(
                                   SANode(Op.NOT, [nnode.children[2]]))])

    if nnode.op == Op.LEQ:
        return SANode(Op.GEQ, [Literal(int(nnode.children[0]) + 1),
                               nnode.children[1],
                               negation_normal_form(
                                   SANode(Op.NOT, [nnode.children[2]]))])

    if nnode.op == Op.FORALL:
        return SANode(Op.GEQ, [Literal(1), nnode.children[0],
                               negation_normal_form(
                                   SANode(Op.NOT, [nnode.children[1]]))])
    # We do not consider HASSHAPE as this function works on expanded shapes
    return node


def optimize_tree(tree: SANode) -> Optional[SANode]:
    """
    go through tree in post-order
    remove empty conjunctions,
    replace singleton conjunctions with self,
    remove top from conjunction
    """

    new_children = []
    for child in tree.children:
        if type(child) == SANode:
            new_child = optimize_tree(child)
            if new_child:  # if it is not removed
                new_children.append(new_child)
        else:
            new_children.append(child)

    tree = SANode(tree.op, new_children)

    # if there is a TOP, filter it out
    if tree.op == Op.AND and any(map(lambda c: c.op == Op.TOP, tree.children)):
        tree.children = list(filter(lambda c: c.op != Op.TOP, tree.children))
        return optimize_tree(tree)

    # if there is an AND node with AND children, merge them to one AND
    if tree.op == Op.AND and any(map(lambda c: c.op == Op.AND, tree.children)):
        new_children = []
        for child in tree.children:
            if child.op == Op.AND:
                new_children.extend(child.children)
            else:
                new_children.append(child)
        tree.children = new_children
        return optimize_tree(tree)

    # if there is an OR node with OR children, merge them to one OR
    if tree.op == Op.OR and any(map(lambda c: c.op == Op.OR, tree.children)):
        new_children = []
        for child in tree.children:
            if child.op == Op.OR:
                new_children.extend(child.children)
            else:
                new_children.append(child)
        tree.children = new_children
        return optimize_tree(tree)

    # remove a disjunction between TOPs
    if tree.op == Op.OR and all(map(lambda c: c.op == Op.TOP, tree.children)):
        return None

    if tree.op == Op.FORALL and len(tree.children) == 1:
        return None

    if tree.op in [Op.AND, Op.OR] and not tree.children:
        return None

    if tree.op in [Op.AND, Op.OR] and len(tree.children) == 1:
        return optimize_tree(tree.children[0])

    return tree