"""
Transformação LibCST: Moderniza anotações de tipo para Python 3.12+
Coloque em: tools/libcst_transforms/modernize_typing.py

Transformações aplicadas:
1. List[X] → list[X]
2. Dict[K, V] → dict[K, V]
3. Tuple[X, ...] → tuple[X, ...]
4. Optional[X] → X | None
5. Union[X, Y] → X | Y
"""

import libcst as cst
from libcst import matchers as m
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor


class ModernizeTypingTransform(VisitorBasedCodemodCommand):
    """Moderniza anotações de tipo para sintaxe Python 3.10+"""

    DESCRIPTION = "Converte tipos typing.X para sintaxe nativa (PEP 585/604)"

    def __init__(self, context: CodemodContext) -> None:
        super().__init__(context)
        self.typing_imports_to_remove: set[str] = set()

    def leave_Annotation(self, original_node: cst.Annotation, updated_node: cst.Annotation) -> cst.Annotation:
        """Transforma anotações de tipo"""

        # List[X] → list[X]
        if m.matches(
            updated_node.annotation,
            m.Subscript(value=m.Name("List"), slice=[m.SubscriptElement(m.Index(m.DoNotCare()))]),
        ):
            self.typing_imports_to_remove.add("List")
            return updated_node.with_changes(annotation=updated_node.annotation.with_changes(value=cst.Name("list")))

        # Dict[K, V] → dict[K, V]
        if m.matches(updated_node.annotation, m.Subscript(value=m.Name("Dict"))):
            self.typing_imports_to_remove.add("Dict")
            return updated_node.with_changes(annotation=updated_node.annotation.with_changes(value=cst.Name("dict")))

        # Tuple[X, ...] → tuple[X, ...]
        if m.matches(updated_node.annotation, m.Subscript(value=m.Name("Tuple"))):
            self.typing_imports_to_remove.add("Tuple")
            return updated_node.with_changes(annotation=updated_node.annotation.with_changes(value=cst.Name("tuple")))

        # Set[X] → set[X]
        if m.matches(updated_node.annotation, m.Subscript(value=m.Name("Set"))):
            self.typing_imports_to_remove.add("Set")
            return updated_node.with_changes(annotation=updated_node.annotation.with_changes(value=cst.Name("set")))

        # Optional[X] → X | None
        if m.matches(
            updated_node.annotation,
            m.Subscript(
                value=m.Name("Optional"),
                slice=[m.SubscriptElement(m.Index(value=m.SaveMatchedNode(cst.BaseExpression, "inner_type")))],
            ),
        ):
            self.typing_imports_to_remove.add("Optional")
            inner = m.extractall(updated_node.annotation, m.SaveMatchedNode(cst.BaseExpression, "inner_type"))
            if inner:
                return updated_node.with_changes(
                    annotation=cst.BinaryOperation(
                        left=inner["inner_type"][0], operator=cst.BitOr(), right=cst.Name("None")
                    )
                )

        # Union[X, Y] → X | Y
        if m.matches(updated_node.annotation, m.Subscript(value=m.Name("Union"))):
            self.typing_imports_to_remove.add("Union")
            # Extrai tipos do Union
            if isinstance(updated_node.annotation, cst.Subscript):
                slice_elements = updated_node.annotation.slice
                if len(slice_elements) >= 2:
                    # Constrói cadeia de BitOr
                    types = [elem.slice.value for elem in slice_elements if isinstance(elem.slice, cst.Index)]
                    result = types[0]
                    for typ in types[1:]:
                        result = cst.BinaryOperation(left=result, operator=cst.BitOr(), right=typ)
                    return updated_node.with_changes(annotation=result)

        return updated_node

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Remove imports desnecessários após transformação"""
        for import_name in self.typing_imports_to_remove:
            RemoveImportsVisitor.remove_unused_import(context=self.context, module="typing", obj=import_name)
        return updated_node


class AddFutureAnnotationsTransform(VisitorBasedCodemodCommand):
    """Adiciona 'from __future__ import annotations' quando necessário"""

    DESCRIPTION = "Adiciona future annotations para compatibilidade"

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Verifica se precisa adicionar future import"""

        # Verifica se já tem o import
        for statement in updated_node.body:
            if m.matches(
                statement,
                m.SimpleStatementLine(
                    body=[m.ImportFrom(module=m.Attribute(value=m.Name("__future__")), names=m.DoNotCare())]
                ),
            ):
                return updated_node

        # Se tem anotações de tipo, adiciona o import
        has_annotations = False
        for node in updated_node.walk():
            if isinstance(node, cst.Annotation):
                has_annotations = True
                break

        if has_annotations:
            AddImportsVisitor.add_needed_import(context=self.context, module="__future__", obj="annotations")

        return updated_node


# Exemplo de uso standalone (para testes)
if __name__ == "__main__":
    from libcst.codemod import CodemodContext

    sample_code = """
from typing import List, Dict, Optional, Union

def process_data(items: List[str], config: Dict[str, int]) -> Optional[str]:
    result: Union[str, int] = items[0]
    return result
"""

    # Parse
    module = cst.parse_module(sample_code)

    # Transform
    context = CodemodContext()
    transformer = ModernizeTypingTransform(context)

    transformed = module.visit(transformer)

    print("=== BEFORE ===")
    print(sample_code)
    print("\n=== AFTER ===")
    print(transformed.code)
