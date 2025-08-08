"""
Geração do corpo de classes C# a partir de estruturas PlantUMLClasse.
"""
from typing import List, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from back_end.plantuml_parser.data_structures import PlantUMLClasse, PlantUMLAtributo, PlantUMLMetodo
    from ..type_mapper import TypeMapper
    from ..using_manager import UsingManager

from ..utils import (
    sanitize_name_for_csharp, to_pascal_case, to_camel_case, 
    get_visibility_modifier, CodeLineBuilder, format_method_signature,
    format_property_declaration
)

class ClassGenerator:
    """Gera o corpo de uma classe C#, incluindo propriedades, construtor e métodos."""
    
    def __init__(self, 
                 class_structure: "PlantUMLClasse", 
                 type_mapper: "TypeMapper", 
                 using_manager: "UsingManager",
                 current_namespace: str):
        self.classe: "PlantUMLClasse" = class_structure
        self.type_mapper: "TypeMapper" = type_mapper
        self.using_manager: "UsingManager" = using_manager
        self.current_namespace: str = current_namespace

    def _generate_static_properties_lines(self) -> List[str]:
        """Gera as linhas de código para as propriedades estáticas."""
        builder = CodeLineBuilder(2)  # Dentro da classe
        
        static_attributes = [attr for attr in self.classe.atributos if attr.is_static]
        if static_attributes:
            for attr in static_attributes:
                csharp_type = self.type_mapper.get_csharp_type_hint_and_imports(
                    attr.tipo, self.current_namespace
                )
                
                property_name = to_pascal_case(attr.nome)
                visibility = get_visibility_modifier(attr.visibilidade)
                
                default_value = attr.default_value if attr.default_value is not None else None
                
                property_decl = format_property_declaration(
                    visibility, csharp_type, property_name, 
                    modifiers=["static"], default_value=default_value
                )
                builder.add_line(property_decl)
            
            builder.add_empty_line()
        return builder.get_lines()

    def _generate_instance_properties_lines(self) -> List[str]:
        """Gera as linhas de código para as propriedades de instância."""
        builder = CodeLineBuilder(2)  # Dentro da classe
        
        instance_attributes = [attr for attr in self.classe.atributos if not attr.is_static]
        if instance_attributes:
            for attr in instance_attributes:
                csharp_type = self.type_mapper.get_csharp_type_hint_and_imports(
                    attr.tipo, self.current_namespace
                )
                
                property_name = to_pascal_case(attr.nome)
                visibility = get_visibility_modifier(attr.visibilidade)
                
                property_decl = format_property_declaration(
                    visibility, csharp_type, property_name
                )
                builder.add_line(property_decl)
            
            builder.add_empty_line()
        return builder.get_lines()

    def _generate_constructor_lines(self) -> List[str]:
        """Gera as linhas de código para o construtor da classe."""
        builder = CodeLineBuilder(2)  # Dentro da classe
        
        # Parâmetros especiais para herança
        parent_required_params = []
        parent_required_args = []
        if self.classe.classe_pai == "Pessoa do Sistema":
            parent_required_params = ["string nome", "string id"]
            parent_required_args = ["nome", "id"]

        instance_attributes = [attr for attr in self.classe.atributos if not attr.is_static]
        
        # Se não há atributos de instância e não há herança, não gera construtor
        if not instance_attributes and not self.classe.classe_pai:
            return []

        required_params = []
        optional_params = []
        constructor_body_lines: List[str] = []

        for attr in instance_attributes:
            param_name = to_camel_case(attr.nome)
            
            # Evita duplicar parâmetros da classe pai
            if param_name in [arg.split()[-1] for arg in parent_required_args]:
                continue
                
            property_name = to_pascal_case(attr.nome)
            
            csharp_type = self.type_mapper.get_csharp_type_hint_and_imports(
                attr.tipo, self.current_namespace
            )
            
            # Determina se é opcional
            is_optional = False
            default_assignment = ""
            
            if attr.default_value is not None:
                default_assignment = f" = {attr.default_value}"
                is_optional = True
            elif csharp_type not in ["string", "int", "float", "double", "bool", "decimal"]:
                default_assignment = " = null"
                is_optional = True
                if not csharp_type.endswith("?") and not csharp_type.startswith("List") and not csharp_type.startswith("Dictionary"):
                    csharp_type += "?"

            param_str = f"{csharp_type} {param_name}{default_assignment}"
            
            if is_optional:
                optional_params.append(param_str)
            else:
                required_params.append(param_str)

            constructor_body_lines.append(f"{property_name} = {param_name};")

        # Monta a lista de parâmetros
        constructor_params = parent_required_params + required_params + optional_params
        
        # Cabeçalho do construtor
        class_name = to_pascal_case(self.classe.nome)
        visibility = "public"
        
        # Monta a chamada ao construtor base se necessário
        base_call = ""
        if self.classe.classe_pai and parent_required_args:
            base_call = f" : base({', '.join(parent_required_args)})"
        
        if constructor_params:
            params_str = ", ".join(constructor_params)
            builder.add_line(f"{visibility} {class_name}({params_str}){base_call}")
        else:
            builder.add_line(f"{visibility} {class_name}(){base_call}")
        
        # Abre o corpo do construtor
        builder.add_line("{")
        
        # Corpo do construtor
        if not constructor_body_lines:
            builder.add_line("// Construtor vazio", 1)
        else:
            for line_code in constructor_body_lines:
                builder.add_line(line_code, 1)
        
        # Fecha o construtor
        builder.add_line("}")
        builder.add_empty_line()
        
        return builder.get_lines()

    def _generate_method_lines(self, met: "PlantUMLMetodo") -> List[str]:
        """Gera as linhas de código para um método da classe."""
        builder = CodeLineBuilder(2)  # Dentro da classe
        
        visibility = get_visibility_modifier(met.visibilidade)
        modifiers = []
        
        if met.is_static:
            modifiers.append("static")
        if met.is_abstract:
            modifiers.append("abstract")
        
        # Parâmetros do método
        param_list = []
        for p_obj in met.parametros:
            param_name = to_camel_case(p_obj.nome)
            param_type = self.type_mapper.get_csharp_type_hint_and_imports(
                p_obj.tipo, self.current_namespace
            )
            param_list.append(f"{param_type} {param_name}")

        # Tipo de retorno
        return_type = self.type_mapper.get_csharp_type_hint_and_imports(
            met.tipo_retorno, self.current_namespace
        ) if met.tipo_retorno else "void"

        method_name = to_pascal_case(met.nome)
        
        # Assinatura do método
        method_signature = format_method_signature(
            visibility, return_type, method_name, param_list, modifiers
        )
        builder.add_line(method_signature)
        builder.add_line("{")
        
        # Corpo do método
        if met.is_abstract:
            # Métodos abstratos não têm implementação em C# se a classe for abstrata
            pass
        else:
            builder.add_line("throw new NotImplementedException();", 1)
        
        builder.add_line("}")
        builder.add_empty_line()
        
        return builder.get_lines()

    def generate_code_lines(self) -> List[str]:
        """Gera as linhas de código para o corpo completo da classe."""
        lines: List[str] = []
        
        # Propriedades estáticas
        lines.extend(self._generate_static_properties_lines())
        
        # Propriedades de instância
        lines.extend(self._generate_instance_properties_lines())
        
        # Construtor
        lines.extend(self._generate_constructor_lines())
        
        # Métodos
        for met in self.classe.metodos:
            lines.extend(self._generate_method_lines(met))
        
        # Se a classe está vazia, adiciona um comentário
        if not lines:
            lines.append("        // Classe vazia")
        
        return lines