"""
Geração do corpo de interfaces Java a partir de estruturas PlantUMLInterface.
"""
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from back_end.plantuml_parser.data_structures import PlantUMLInterface, PlantUMLMetodo, PlantUMLAtributo
    from ..type_mapper import TypeMapper
    from ..import_manager import ImportManager

from ..utils import (
    to_pascal_case, to_camel_case, get_visibility_modifier,
    CodeLineBuilder, format_method_signature, format_property_declaration
)

class InterfaceGenerator:
    """Gera o corpo de uma interface Java, incluindo métodos e campos constantes."""

    def __init__(self,
                 interface_structure: "PlantUMLInterface",
                 type_mapper: "TypeMapper",
                 import_manager: "ImportManager",
                 current_package: str):
        self.interface: "PlantUMLInterface" = interface_structure
        self.type_mapper: "TypeMapper" = type_mapper
        self.import_manager: "ImportManager" = import_manager
        self.current_package: str = current_package

    def _generate_static_fields_lines(self) -> List[str]:
        """
        Gera as linhas de código para os campos estáticos (constantes).
        Em Java, interfaces podem ter constantes ("public static final").
        """
        builder = CodeLineBuilder(1)
        static_attributes = [attr for attr in self.interface.atributos if attr.is_static]
        for attr in static_attributes:
            java_type = self.type_mapper.get_java_type_hint_and_imports(attr.tipo)
            field_name = to_camel_case(attr.nome)
            default_value = attr.default_value if attr.default_value is not None else None
            # Constantes em interfaces Java são public static final
            modifiers = ["public", "static", "final"]
            field_decl = format_property_declaration(
                "", java_type, field_name,
                modifiers=modifiers,
                default_value=default_value,
                is_interface=True
            )
            builder.add_line(field_decl)
        if static_attributes:
            builder.add_empty_line()
        return builder.get_lines()

    def _generate_instance_fields_lines(self) -> List[str]:
        """
        Em Java, interfaces não têm campos de instância, apenas constantes,
        mas se quiser suportar, gere como 'public abstract'.
        """
        builder = CodeLineBuilder(1)
        instance_attributes = [attr for attr in self.interface.atributos if not attr.is_static]
        for attr in instance_attributes:
            java_type = self.type_mapper.get_java_type_hint_and_imports(attr.tipo)
            field_name = to_camel_case(attr.nome)
            modifiers = ["public", "abstract"]
            field_decl = format_property_declaration(
                "", java_type, field_name,
                modifiers=modifiers,
                is_interface=True
            )
            builder.add_line(field_decl)
        if instance_attributes:
            builder.add_empty_line()
        return builder.get_lines()

    def _generate_method_lines(self, met: "PlantUMLMetodo") -> List[str]:
        builder = CodeLineBuilder(1)
        visibility = ""  # Métodos de interface são implicitamente públicos e abstratos
        modifiers = []
        if met.is_static:
            modifiers.append("static")
        if met.is_abstract and not met.is_static:
            modifiers.append("abstract")
        param_list = []
        for p_obj in met.parametros:
            param_name = to_camel_case(p_obj.nome)
            param_type = self.type_mapper.get_java_type_hint_and_imports(p_obj.tipo)
            param_list.append(f"{param_type} {param_name}")
        return_type = self.type_mapper.get_java_type_hint_and_imports(met.tipo_retorno) if met.tipo_retorno else "void"
        method_name = to_camel_case(met.nome)

        # Métodos static em interfaces Java podem ter implementação
        if met.is_static:
            method_signature = format_method_signature(
                "public", return_type, method_name, param_list, modifiers, is_interface=True
            )
            builder.add_line(method_signature)
            builder.add_line("{")
            builder.add_line("// TODO: Implementação de método estático", 1)
            builder.add_line("}")
        else:
            # Métodos abstratos (interface padrão)
            method_signature = format_method_signature(
                "public", return_type, method_name, param_list, modifiers, is_interface=True
            )
            builder.add_line(f"{method_signature};")
        builder.add_empty_line()
        return builder.get_lines()

    def generate_code_lines(self) -> List[str]:
        lines: List[str] = []
        lines.extend(self._generate_static_fields_lines())
        lines.extend(self._generate_instance_fields_lines())
        if self.interface.metodos:
            for met in self.interface.metodos:
                lines.extend(self._generate_method_lines(met))
        if not lines:
            lines.append("    // Interface vazia")
        return lines