"""
Geração do corpo de interfaces C# a partir de estruturas PlantUMLInterface.
"""
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from back_end.plantuml_parser.data_structures import PlantUMLInterface, PlantUMLMetodo, PlantUMLAtributo
    from ..type_mapper import TypeMapper
    from ..using_manager import UsingManager

from ..utils import (
    to_pascal_case, to_camel_case, get_visibility_modifier,
    CodeLineBuilder, format_method_signature, format_property_declaration
)

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

    def _generate_static_properties_lines(self) -> List[str]:
        """
        Gera as linhas de código para as propriedades estáticas.
        Note: Em C#, interfaces não podem ter campos estáticos, 
        mas podem ter propriedades estáticas a partir do C# 8.0.
        """
        builder = CodeLineBuilder(2)  # Dentro da interface

        static_attributes = [attr for attr in self.interface.atributos if attr.is_static]
        if static_attributes:
            for attr in static_attributes:
                csharp_type = self.type_mapper.get_csharp_type_hint_and_imports(
                    attr.tipo, self.current_namespace
                )
                
                property_name = to_pascal_case(attr.nome)
                
                # Em interfaces C#, propriedades estáticas podem ter implementação padrão
                if attr.default_value is not None:
                    property_decl = format_property_declaration(
                        "", csharp_type, property_name, 
                        modifiers=["static"], default_value=attr.default_value,
                        is_interface=True
                    )
                else:
                    # Propriedade estática sem implementação (deve ser implementada pela classe)
                    builder.add_line(f"static abstract {csharp_type} {property_name} {{ get; set; }}")
                    continue
                
                builder.add_line(property_decl)
            
            builder.add_empty_line()
        return builder.get_lines()

    def _generate_instance_properties_lines(self) -> List[str]:
        """Gera as linhas de código para as propriedades de instância."""
        builder = CodeLineBuilder(2)  # Dentro da interface

        instance_attributes = [attr for attr in self.interface.atributos if not attr.is_static]
        if instance_attributes:
            for attr in instance_attributes:
                csharp_type = self.type_mapper.get_csharp_type_hint_and_imports(
                    attr.tipo, self.current_namespace
                )
                
                property_name = to_pascal_case(attr.nome)
                
                # Em interfaces, propriedades geralmente têm get e set
                # A visibilidade é ignorada pois em interfaces tudo é público
                property_decl = format_property_declaration(
                    "", csharp_type, property_name, is_interface=True
                )
                builder.add_line(property_decl)
            
            builder.add_empty_line()
        return builder.get_lines()

    def _generate_method_lines(self, met: "PlantUMLMetodo") -> List[str]:
        """Gera as linhas de código para um método da interface."""
        builder = CodeLineBuilder(2)  # Dentro da interface
        
        # Em interfaces C#, métodos não têm modificadores de visibilidade
        # e são implicitamente públicos e abstratos
        modifiers = []
        
        if met.is_static:
            # A partir do C# 8.0, interfaces podem ter métodos estáticos
            modifiers.append("static")
        
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
        if met.is_static:
            # Métodos estáticos em interfaces podem ter implementação padrão
            method_signature = format_method_signature(
                "", return_type, method_name, param_list, modifiers, is_interface=True
            )
            builder.add_line(method_signature)
            builder.add_line("{")
            
            # Implementação padrão
            builder.add_line("throw new NotImplementedException();", 1)
            
            builder.add_line("}")
        else:
            # Método de instância - apenas assinatura (sem implementação)
            method_signature = format_method_signature(
                "", return_type, method_name, param_list, is_interface=True
            )
            builder.add_line(f"{method_signature};")
        
        builder.add_empty_line()
        
        return builder.get_lines()

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