"""
Geração do corpo de interfaces Python a partir de estruturas PlantUMLInterface.
"""
from typing import List, TYPE_CHECKING

# Importa funções de sanitização do diretório utils um nível acima
from ..utils import sanitize_name_for_python_module, to_pascal_case 

if TYPE_CHECKING:
    # Importa estruturas de data_structures para type hinting
    from back_end.plantuml_parser.data_structures import PlantUMLInterface, PlantUMLMetodo, PlantUMLAtributo
    # Importa TypeMapper para type hinting
    from ..type_mapper import TypeMapper

class InterfaceGenerator:
    """
    Gera o corpo de uma interface Python, incluindo métodos abstratos e atributos estáticos.
    """
    def __init__(self, 
                 interface_structure: "PlantUMLInterface", 
                 type_mapper: "TypeMapper", 
                 current_file_module_dot_path: str):
        """
        Inicializa uma nova instância do InterfaceGenerator.

        Args:
            interface_structure: O objeto PlantUMLInterface parseado.
            type_mapper: Uma instância de TypeMapper para converter tipos PlantUML
                         para type hints Python.
            current_file_module_dot_path: O caminho pontilhado do módulo Python
                                          que está sendo gerado.
        """
        self.interface: "PlantUMLInterface" = interface_structure
        self.type_mapper: "TypeMapper" = type_mapper
        self.current_file_module_dot_path: str = current_file_module_dot_path

    def _generate_method_lines(self, met: "PlantUMLMetodo") -> List[str]:
        """
        Gera as linhas de código para um método da interface.

        Args:
            met: Método a ser gerado.

        Returns:
            Lista de linhas de código para o método.
        """
        method_lines: List[str] = []
        # A indentação aqui é relativa ao início da definição do método,
        # não ao início da classe. O MainCodeGenerator cuida da indentação da classe.
        
        method_decorators = []
        if not met.is_static: # Métodos de interface não estáticos são abstratos
            method_decorators.append("@abstractmethod")
        if met.is_static:
            method_decorators.append("@staticmethod")
        
        for decorator in method_decorators:
            method_lines.append("    " * 1 + decorator) # Indentação de 1 nível dentro da classe

        param_list_for_def = []
        if not met.is_static:
            param_list_for_def.append("self")
        
        for p_obj in met.parametros:
            p_name_py = sanitize_name_for_python_module(p_obj.nome)
            p_type_py, _s_imps, _t_imps = self.type_mapper.get_python_type_hint_and_imports(
                p_obj.tipo, self.current_file_module_dot_path
            )
            param_list_for_def.append(f"{p_name_py}: {p_type_py}")

        return_type_py, _s_imps, _t_imps = self.type_mapper.get_python_type_hint_and_imports(
            met.tipo_retorno, self.current_file_module_dot_path
        )
        return_annotation = f" -> {return_type_py}" if return_type_py != "None" else ""

        method_name_py = sanitize_name_for_python_module(met.nome)
        # Visibilidade em interfaces é sempre pública em Python, não aplicamos _ ou __

        method_lines.append("    " * 1 + f"def {method_name_py}({', '.join(param_list_for_def)}){return_annotation}:")
        method_lines.append("    " * 2 + f'"""Método {met.nome} da interface."""') # Sua docstring aqui
        method_lines.append("    " * 2 + "pass")
        method_lines.append("    " * 1 + "") # Linha em branco após o método
        return method_lines

    def generate_code_lines(self) -> List[str]:
        """
        Gera as linhas de código para o corpo completo da interface,
        incluindo atributos estáticos (constantes) e métodos.

        Retorna:
            Uma lista de strings representando o corpo da interface.
        """
        lines: List[str] = []
        indent_level = 1 # Dentro da classe

        def add_line(text: str):
            lines.append("    " * indent_level + text)
        
        static_attributes = [attr for attr in self.interface.atributos if attr.is_static]
        if static_attributes:
            for attr in static_attributes:
                py_type_hint, _s_imps, _t_imps = self.type_mapper.get_python_type_hint_and_imports(
                    attr.tipo, self.current_file_module_dot_path
                )
                attr_name_py = sanitize_name_for_python_module(attr.nome).upper()
                default_val_str = ""
                if attr.default_value is not None:
                    default_val_str = f" = {attr.default_value}"
                elif py_type_hint != "Any" and py_type_hint != "None":
                    # Interfaces geralmente não inicializam, apenas declaram tipo para constantes
                    default_val_str = f": {py_type_hint} = ..." 
                elif py_type_hint == "Any":
                     default_val_str = f": {py_type_hint} = ..."
                else: # None
                     default_val_str = " = ..." # Ou apenas o nome se for uma constante sem tipo explícito
                add_line(f"{attr_name_py}{default_val_str}")
            add_line("")
            
        if not self.interface.metodos and not static_attributes:
            add_line("pass")
        else:
            for met in self.interface.metodos:
                lines.extend(self._generate_method_lines(met))
        
        return lines