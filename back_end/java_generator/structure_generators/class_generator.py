"""
Geração do corpo de classes Java a partir de estruturas PlantUMLClasse.
"""
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from back_end.plantuml_parser.data_structures import PlantUMLClasse, PlantUMLAtributo, PlantUMLMetodo
    from ..type_mapper import TypeMapper
    from ..import_manager import ImportManager


from ..utils import (
    sanitize_name_for_java, to_pascal_case, to_camel_case, 
    get_visibility_modifier, CodeLineBuilder, format_method_signature,
    format_property_declaration
)

class ClassGenerator:
    """Gera o corpo de uma classe Java, incluindo campos, construtor e métodos."""
    
    def __init__(self, 
                 class_structure: "PlantUMLClasse", 
                 type_mapper: "TypeMapper", 
                 import_manager: "ImportManager",
                 current_package: str):
        self.classe: "PlantUMLClasse" = class_structure
        self.type_mapper: "TypeMapper" = type_mapper
        self.import_manager: "ImportManager" = import_manager
        self.current_package: str = current_package

    def _generate_static_fields_lines(self) -> List[str]:
        builder = CodeLineBuilder(1)  # Dentro da classe
        static_attributes = [attr for attr in self.classe.atributos if attr.is_static]
        for attr in static_attributes:
            java_type = self.type_mapper.get_java_type_hint_and_imports(attr.tipo)
            field_name = to_camel_case(attr.nome)
            visibility = get_visibility_modifier(attr.visibilidade)
            default_value = attr.default_value if attr.default_value is not None else None
            field_decl = format_property_declaration(
                visibility, java_type, field_name,
                modifiers=["static"], default_value=default_value
            )
            builder.add_line(field_decl)
        if static_attributes:
            builder.add_empty_line()
        return builder.get_lines()

    def _generate_instance_fields_lines(self) -> List[str]:
        builder = CodeLineBuilder(1)
        instance_attributes = [attr for attr in self.classe.atributos if not attr.is_static]
        for attr in instance_attributes:
            java_type = self.type_mapper.get_java_type_hint_and_imports(attr.tipo)
            field_name = to_camel_case(attr.nome)
            visibility = get_visibility_modifier(attr.visibilidade)
            default_value = attr.default_value if attr.default_value is not None else None
            field_decl = format_property_declaration(
                visibility, java_type, field_name,
                default_value=default_value
            )
            builder.add_line(field_decl)
        if instance_attributes:
            builder.add_empty_line()
        return builder.get_lines()

    def _generate_constructor_lines(self) -> List[str]:
        builder = CodeLineBuilder(1)
        instance_attributes = [attr for attr in self.classe.atributos if not attr.is_static]
        if not instance_attributes:
            return []
        params = []
        body_lines = []
        for attr in instance_attributes:
            param_name = to_camel_case(attr.nome)
            java_type = self.type_mapper.get_java_type_hint_and_imports(attr.tipo)
            params.append(f"{java_type} {param_name}")
            body_lines.append(f"this.{param_name} = {param_name};")
        class_name = to_pascal_case(self.classe.nome)
        params_str = ", ".join(params)
        builder.add_line(f"public {class_name}({params_str})")
        builder.add_line("{")
        for line_code in body_lines:
            builder.add_line(line_code, 1)
        builder.add_line("}")
        builder.add_empty_line()
        return builder.get_lines()

    def _generate_method_lines(self, met: "PlantUMLMetodo") -> List[str]:
        builder = CodeLineBuilder(1)
        visibility = get_visibility_modifier(met.visibilidade)
        modifiers = []
        if met.is_static:
            modifiers.append("static")
        if met.is_abstract:
            modifiers.append("abstract")
        param_list = []
        for p_obj in met.parametros:
            param_name = to_camel_case(p_obj.nome)
            param_type = self.type_mapper.get_java_type_hint_and_imports(p_obj.tipo)
            param_list.append(f"{param_type} {param_name}")
        return_type = self.type_mapper.get_java_type_hint_and_imports(met.tipo_retorno) if met.tipo_retorno else "void"
        method_name = to_camel_case(met.nome)
        method_signature = format_method_signature(
            visibility, return_type, method_name, param_list, modifiers, is_interface=False
        )
        builder.add_line(method_signature)
        builder.add_line("{")
        if met.is_abstract:
            builder.add_line("// Método abstrato", 1)
        else:
            builder.add_line("// TODO: Implementação", 1)
        builder.add_line("}")
        builder.add_empty_line()
        return builder.get_lines()

    def generate_code_lines(self) -> List[str]:
        lines: List[str] = []
        lines.extend(self._generate_static_fields_lines())
        lines.extend(self._generate_instance_fields_lines())
        lines.extend(self._generate_constructor_lines())
        for met in self.classe.metodos:
            lines.extend(self._generate_method_lines(met))
        if not lines:
            lines.append("    // Classe vazia")
        return lines