"""
Geração do corpo de interfaces C# a partir de estruturas PlantUMLInterface.
"""
from typing import List, TYPE_CHECKING
import re
import unicodedata

if TYPE_CHECKING:
    from back_end.plantuml_parser.data_structures import PlantUMLInterface, PlantUMLMetodo, PlantUMLAtributo
    from ..type_mapper import TypeMapper
    from ..using_manager import UsingManager

class InterfaceGenerator:
    """Gera o corpo de uma interface C#, incluindo métodos e propriedades."""
    
    def __init__(self, 
                 interface_structure: "PlantUMLInterface", 
                 type_mapper: "TypeMapper", 
                 using_manager: "UsingManager",
                 current_namespace: str):
        """
        Inicializa uma nova instância do InterfaceGenerator.

        Args:
            interface_structure: O objeto PlantUMLInterface parseado.
            type_mapper: Uma instância de TypeMapper para mapeamento de tipos.
            using_manager: Uma instância de UsingManager para gerenciar using statements.
            current_namespace: O namespace atual para resolver referências.
        """
        self.interface: "PlantUMLInterface" = interface_structure
        self.type_mapper: "TypeMapper" = type_mapper
        self.using_manager: "UsingManager" = using_manager
        self.current_namespace: str = current_namespace

    def _sanitize_name_for_csharp(self, name: str) -> str:
        """Sanitiza nome para C#."""
        # Remove acentos e caracteres especiais
        name = name.replace('ç', 'c').replace('Ç', 'C')
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
            return "_UnnamedMember"
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
        """
        Converte a visibilidade PlantUML para modificador C#.
        Para interfaces, todos os membros são implicitamente públicos.
        """
        # Em interfaces C#, todos os membros são implicitamente públicos
        # Não precisamos especificar public explicitamente
        return ""

    def _generate_static_properties_lines(self) -> List[str]:
        """
        Gera as linhas de código para as propriedades estáticas.
        Note: Em C#, interfaces não podem ter campos estáticos, 
        mas podem ter propriedades estáticas a partir do C# 8.0.
        """
        lines: List[str] = []
        indent_level = 2  # Dentro da interface
        
        def add_line(text: str): 
            lines.append("    " * indent_level + text)

        static_attributes = [attr for attr in self.interface.atributos if attr.is_static]
        if static_attributes:
            for attr in static_attributes:
                csharp_type = self.type_mapper.get_csharp_type_hint_and_imports(
                    attr.tipo, self.current_namespace
                )
                
                property_name = self._to_pascal_case(attr.nome)
                
                # Em interfaces C#, propriedades estáticas podem ter implementação padrão
                if attr.default_value is not None:
                    add_line(f"static {csharp_type} {property_name} {{ get; }} = {attr.default_value};")
                else:
                    # Propriedade estática sem implementação (deve ser implementada pela classe)
                    add_line(f"static abstract {csharp_type} {property_name} {{ get; set; }}")
            
            add_line("")
        return lines

    def _generate_instance_properties_lines(self) -> List[str]:
        """Gera as linhas de código para as propriedades de instância."""
        lines: List[str] = []
        indent_level = 2  # Dentro da interface
        
        def add_line(text: str): 
            lines.append("    " * indent_level + text)

        instance_attributes = [attr for attr in self.interface.atributos if not attr.is_static]
        if instance_attributes:
            for attr in instance_attributes:
                csharp_type = self.type_mapper.get_csharp_type_hint_and_imports(
                    attr.tipo, self.current_namespace
                )
                
                property_name = self._to_pascal_case(attr.nome)
                
                # Em interfaces, propriedades geralmente têm get e set
                # A visibilidade é ignorada pois em interfaces tudo é público
                add_line(f"{csharp_type} {property_name} {{ get; set; }}")
            
            add_line("")
        return lines

    def _generate_method_lines(self, met: "PlantUMLMetodo") -> List[str]:
        """Gera as linhas de código para um método da interface."""
        method_lines: List[str] = []
        base_indent_level = 2  # Dentro da interface
        
        # Em interfaces C#, métodos não têm modificadores de visibilidade
        # e são implicitamente públicos e abstratos
        modifiers = []
        
        if met.is_static:
            # A partir do C# 8.0, interfaces podem ter métodos estáticos
            modifiers.append("static")
        
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
        if modifiers_str:
            modifiers_str += " "
        params_str = ", ".join(param_list)
        
        # Assinatura do método
        if met.is_static:
            # Métodos estáticos em interfaces podem ter implementação padrão
            method_lines.append("    " * base_indent_level + f"{modifiers_str}{return_type} {method_name}({params_str})")
            method_lines.append("    " * base_indent_level + "{")
            
            # Implementação padrão
            body_indent_level = 3
            if return_type != "void":
                method_lines.append("    " * body_indent_level + f"throw new NotImplementedException();")
            else:
                method_lines.append("    " * body_indent_level + f"throw new NotImplementedException();")
            
            method_lines.append("    " * base_indent_level + "}")
        else:
            # Método de instância - apenas assinatura (sem implementação)
            method_lines.append("    " * base_indent_level + f"{return_type} {method_name}({params_str});")
        
        method_lines.append("    " * base_indent_level + "")
        
        return method_lines

    def generate_code_lines(self) -> List[str]:
        """Gera as linhas de código para o corpo completo da interface."""
        lines: List[str] = []
        
        # Propriedades estáticas (C# 8.0+)
        lines.extend(self._generate_static_properties_lines())
        
        # Propriedades de instância
        lines.extend(self._generate_instance_properties_lines())
        
        # Métodos
        if self.interface.metodos:
            for met in self.interface.metodos:
                lines.extend(self._generate_method_lines(met))
        
        # Se a interface está completamente vazia, não adiciona nada
        # (interfaces vazias são válidas em C#)
        if not lines:
            lines.append("        // Interface vazia")
        
        return lines