"""
Geração do corpo de classes C# a partir de estruturas PlantUMLClasse.
"""
from typing import List, Set, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from back_end.plantuml_parser.data_structures import PlantUMLClasse, PlantUMLAtributo, PlantUMLMetodo
    from ..type_mapper import TypeMapper
    from ..using_manager import UsingManager

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

    def _sanitize_name_for_csharp(self, name: str) -> str:
        """Sanitiza nome para C#."""
        # Remove acentos e caracteres especiais
        name = name.replace('ç', 'c').replace('Ç', 'C')
        import unicodedata
        nfkd = unicodedata.normalize('NFKD', name)
        name = "".join([c for c in nfkd if not unicodedata.combining(c)])
        
        # Remove aspas e caracteres inválidos
        name = name.replace('"', '').replace("'", "")
        name = re.sub(r'[^0-9a-zA-Z_]', '', name)
        
        if not name:
            return "_Unnamed"
        if name[0].isdigit():
            name = "_" + name
        
        return name

    def _to_pascal_case(self, name: str) -> str:
        """Converte nome para PascalCase."""
        name = self._sanitize_name_for_csharp(name)
        parts = re.split(r'[_\s]+', name)
        if len(parts) == 1 and name:
            parts = re.findall(r'[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])', name)
        
        capitalized_parts = [p.capitalize() for p in parts if p]
        pascal_case_name = "".join(capitalized_parts)
        
        if not pascal_case_name:
            return "_UnnamedClass"
        if pascal_case_name[0].isdigit():
            return "_" + pascal_case_name
        return pascal_case_name

    def _to_camel_case(self, name: str) -> str:
        """Converte nome para camelCase."""
        pascal_name = self._to_pascal_case(name)
        if pascal_name:
            return pascal_name[0].lower() + pascal_name[1:]
        return pascal_name

    def _get_visibility_modifier(self, visibilidade: str) -> str:
        """Converte a visibilidade PlantUML para modificador C#."""
        visibility_map = {
            "+": "public",
            "-": "private", 
            "#": "protected",
            "~": "internal"
        }
        return visibility_map.get(visibilidade, "public")

    def _generate_static_properties_lines(self) -> List[str]:
        """Gera as linhas de código para as propriedades estáticas."""
        lines: List[str] = []
        indent_level = 2  # Dentro da classe
        
        def add_line(text: str): 
            lines.append("    " * indent_level + text)

        static_attributes = [attr for attr in self.classe.atributos if attr.is_static]
        if static_attributes:
            for attr in static_attributes:
                csharp_type = self.type_mapper.get_csharp_type_hint_and_imports(
                    attr.tipo, self.current_namespace
                )
                
                property_name = self._to_pascal_case(attr.nome)
                visibility = self._get_visibility_modifier(attr.visibilidade)
                
                default_value = ""
                if attr.default_value is not None:
                    default_value = f" = {attr.default_value};"
                else:
                    default_value = ";"
                
                add_line(f"{visibility} static {csharp_type} {property_name} {{ get; set; }}{default_value}")
            
            add_line("")
        return lines

    def _generate_instance_properties_lines(self) -> List[str]:
        """Gera as linhas de código para as propriedades de instância."""
        lines: List[str] = []
        indent_level = 2  # Dentro da classe
        
        def add_line(text: str): 
            lines.append("    " * indent_level + text)

        instance_attributes = [attr for attr in self.classe.atributos if not attr.is_static]
        if instance_attributes:
            for attr in instance_attributes:
                csharp_type = self.type_mapper.get_csharp_type_hint_and_imports(
                    attr.tipo, self.current_namespace
                )
                
                property_name = self._to_pascal_case(attr.nome)
                visibility = self._get_visibility_modifier(attr.visibilidade)
                
                add_line(f"{visibility} {csharp_type} {property_name} {{ get; set; }}")
            
            add_line("")
        return lines

    def _generate_constructor_lines(self) -> List[str]:
        """Gera as linhas de código para o construtor da classe."""
        lines: List[str] = []
        base_indent_level = 2
        body_indent_level = 3

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
            param_name = self._to_camel_case(attr.nome)
            
            # Evita duplicar parâmetros da classe pai
            if param_name in [arg.split()[-1] for arg in parent_required_args]:
                continue
                
            property_name = self._to_pascal_case(attr.nome)
            
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
        class_name = self._to_pascal_case(self.classe.nome)
        visibility = "public"
        
        # Monta a chamada ao construtor base se necessário
        base_call = ""
        if self.classe.classe_pai and parent_required_args:
            base_call = f" : base({', '.join(parent_required_args)})"
        
        if constructor_params:
            params_str = ", ".join(constructor_params)
            lines.append("    " * base_indent_level + f"{visibility} {class_name}({params_str}){base_call}")
        else:
            lines.append("    " * base_indent_level + f"{visibility} {class_name}(){base_call}")
        
        # Abre o corpo do construtor
        lines.append("    " * base_indent_level + "{")
        
        # Corpo do construtor
        if not constructor_body_lines:
            lines.append("    " * body_indent_level + "// Construtor vazio")
        else:
            for line_code in constructor_body_lines:
                lines.append("    " * body_indent_level + line_code)
        
        # Fecha o construtor
        lines.append("    " * base_indent_level + "}")
        lines.append("    " * base_indent_level + "")
        
        return lines

    def _generate_method_lines(self, met: "PlantUMLMetodo") -> List[str]:
        """Gera as linhas de código para um método da classe."""
        method_lines: List[str] = []
        base_indent_level = 2
        body_indent_level = 3
        
        visibility = self._get_visibility_modifier(met.visibilidade)
        modifiers = [visibility]
        
        if met.is_static:
            modifiers.append("static")
        if met.is_abstract:
            modifiers.append("abstract")
        
        # Parâmetros do método
        param_list = []
        for p_obj in met.parametros:
            param_name = self._to_camel_case(p_obj.nome)
            param_type = self.type_mapper.get_csharp_type_hint_and_imports(
                p_obj.tipo, self.current_namespace
            )
            param_list.append(f"{param_type} {param_name}")

        # Tipo de retorno
        return_type = self.type_mapper.get_csharp_type_hint_and_imports(
            met.tipo_retorno, self.current_namespace
        ) if met.tipo_retorno else "void"

        method_name = self._to_pascal_case(met.nome)
        modifiers_str = " ".join(modifiers)
        params_str = ", ".join(param_list)
        
        # Assinatura do método
        method_lines.append("    " * base_indent_level + f"{modifiers_str} {return_type} {method_name}({params_str})")
        method_lines.append("    " * base_indent_level + "{")
        
        # Corpo do método
        if met.is_abstract:
            # Métodos abstratos não têm implementação em C# se a classe for abstrata
            pass
        else:
            if return_type != "void":
                method_lines.append("    " * body_indent_level + f"throw new NotImplementedException();")
            else:
                method_lines.append("    " * body_indent_level + f"throw new NotImplementedException();")
        
        method_lines.append("    " * base_indent_level + "}")
        method_lines.append("    " * base_indent_level + "")
        
        return method_lines

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