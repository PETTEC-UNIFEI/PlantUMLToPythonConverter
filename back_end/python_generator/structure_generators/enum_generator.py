"""
Geração do corpo de enums Python a partir de estruturas PlantUMLEnum.
"""
from typing import List, TYPE_CHECKING

# Importa a função de sanitização do diretório utils um nível acima
from ..utils import sanitize_name_for_python_module 

if TYPE_CHECKING:
    # Importa PlantUMLEnum de data_structures para type hinting,
    # usando o caminho completo para evitar problemas de import relativo aqui.
    from back_end.plantuml_parser.data_structures import PlantUMLEnum
    # Importa TypeMapper para type hinting.
    from ..type_mapper import TypeMapper

class EnumGenerator:
    """
    Gera o corpo de uma enumeração Python.
    """
    def __init__(self, 
                 enum_structure: "PlantUMLEnum", 
                 type_mapper: "TypeMapper", 
                 current_file_module_dot_path: str):
        """
        Inicializa uma nova instância do EnumGenerator.

        Args:
            enum_structure: O objeto PlantUMLEnum parseado.
            type_mapper: Uma instância de TypeMapper para qualquer necessidade
                         futura de mapeamento de tipos (atualmente não usado
                         intensivamente por enums simples).
            current_file_module_dot_path: O caminho pontilhado do módulo Python
                                          que está sendo gerado.
        """
        self.enum: "PlantUMLEnum" = enum_structure
        self.type_mapper: "TypeMapper" = type_mapper
        self.current_file_module_dot_path: str = current_file_module_dot_path

    def generate_code_lines(self) -> List[str]:
        """
        Gera as linhas de código para os valores do enum.

        Retorna:
            Uma lista de strings, cada uma representando uma linha de código
            para o corpo do enum.
        """
        lines: List[str] = []
        indent_level = 1 # Assume que já está dentro da definição da classe Enum

        def add_line(text: str, indent_delta: int = 0):
            nonlocal indent_level
            actual_indent = indent_level + indent_delta
            if actual_indent < 0: actual_indent = 0
            lines.append("    " * actual_indent + text)

        if not self.enum.valores_enum:
            add_line("pass")
        else:
            for valor in self.enum.valores_enum:
                valor_sanitizado = sanitize_name_for_python_module(valor).upper()
                add_line(f"{valor_sanitizado} = auto()")
        
        return lines