"""
Geração do corpo de classes Python a partir de estruturas PlantUMLClasse.
"""
from typing import List, Set, TYPE_CHECKING
from ..utils import sanitize_name_for_python_module, to_pascal_case # Usando .. para subir um nível

if TYPE_CHECKING:
    # Importa estruturas de data_structures para type hinting
    from back_end.plantuml_parser.data_structures import PlantUMLClasse, PlantUMLAtributo, PlantUMLMetodo
    # Importa TypeMapper para type hinting
    from ..type_mapper import TypeMapper

class ClassGenerator:
    """
    Gera o corpo de uma classe Python, incluindo atributos, construtor e métodos.
    """
    def __init__(self, 
                 class_structure: "PlantUMLClasse", 
                 type_mapper: "TypeMapper", 
                 current_file_module_dot_path: str):
        """
        Inicializa uma nova instância do ClassGenerator.

        Args:
            class_structure: O objeto PlantUMLClasse parseado.
            type_mapper: Uma instância de TypeMapper para converter tipos PlantUML
                         para type hints Python.
            current_file_module_dot_path: O caminho pontilhado do módulo Python
                                          que está sendo gerado.
        """
        self.classe: "PlantUMLClasse" = class_structure
        self.type_mapper: "TypeMapper" = type_mapper
        self.current_file_module_dot_path: str = current_file_module_dot_path

    def _generate_static_attribute_lines(self) -> List[str]:
        """
        Gera as linhas de código para os atributos estáticos (de classe).

        Returns:
            Uma lista de strings, cada uma representando uma linha de código
            para a declaração de um atributo estático.
        """
        lines: List[str] = []
        indent_level = 1 # Dentro da classe
        def add_s_line(text: str): lines.append("    " * indent_level + text)

        static_attributes = [attr for attr in self.classe.atributos if attr.is_static]
        if static_attributes:
            for attr in static_attributes:
                py_type_hint, _s_imps, _t_imps = self.type_mapper.get_python_type_hint_and_imports(
                    attr.tipo, self.current_file_module_dot_path
                )
                attr_name_py = sanitize_name_for_python_module(attr.nome).upper()
                default_val_str = ""
                if attr.default_value is not None:
                    default_val_str = f" = {attr.default_value}" # Assume que o valor default é uma string Python válida
                elif py_type_hint != "Any" and py_type_hint != "None":
                    default_val_str = f": {py_type_hint} = None"
                elif py_type_hint == "Any":
                     default_val_str = f": {py_type_hint} = None"
                else: # None
                     default_val_str = " = None"
                add_s_line(f"{attr_name_py}{default_val_str}")
            add_s_line("")
        return lines

    def _generate_init_lines(self) -> List[str]:
        """
        Gera as linhas de código para o método __init__ da classe,
        incluindo parâmetros para atributos de instância e a chamada super().

        Returns:
            Uma lista de strings, cada uma representando uma linha de código
            para o método __init__.
        """
        lines: List[str] = []
        base_indent_level = 1
        body_indent_level = 2

        # Detecta parâmetros obrigatórios da superclasse
        parent_required_params = []
        parent_required_args = []
        if self.classe.classe_pai == "Pessoa do Sistema":
            parent_required_params = ["nome: str", "id: str"]
            parent_required_args = ["nome", "id"]

        instance_attributes = [attr for attr in self.classe.atributos if not attr.is_static]
        if not instance_attributes and not self.classe.classe_pai:
            return []

        # Separe obrigatórios e opcionais
        required_params = []
        optional_params = []
        init_body_lines: List[str] = []

        # Chama super().__init__ com os argumentos adequados
        if self.classe.classe_pai:
            if parent_required_args:
                init_body_lines.append(f"super().__init__({', '.join(parent_required_args)})")
            else:
                init_body_lines.append("super().__init__()")

        for attr in instance_attributes:
            param_name_py = sanitize_name_for_python_module(attr.nome)
            # Não adicione parâmetros duplicados que já estão nos parent_required_args
            if param_name_py in parent_required_args:
                continue
                
            attr_name_in_class = param_name_py
            if attr.visibilidade == "-": attr_name_in_class = f"__{param_name_py}"
            elif attr.visibilidade == "#": attr_name_in_class = f"_{param_name_py}"

            py_type_hint, _s_imps, t_imps = self.type_mapper.get_python_type_hint_and_imports(
                attr.tipo, self.current_file_module_dot_path
            )
            param_type_str = self._get_type_hint_str(py_type_hint)

            default_assignment_for_param = ""
            is_optional = False
            if attr.default_value is not None:
                param_type_str = f"Optional[{self._get_type_hint_str(py_type_hint)}]"
                default_assignment_for_param = f" = {attr.default_value}"
                is_optional = True
            elif py_type_hint not in ["str", "int", "float", "bool", "Any", "None", "datetime.date"] and not py_type_hint.startswith("'"):
                param_type_str = f"Optional[{self._get_type_hint_str(py_type_hint)}]"
                default_assignment_for_param = " = None"
                is_optional = True

            param_str = f"{param_name_py}: {param_type_str}{default_assignment_for_param}"
            if is_optional:
                optional_params.append(param_str)
            else:
                required_params.append(param_str)

            init_body_lines.append(f"self.{attr_name_in_class}: {self._get_type_hint_str(py_type_hint)} = {param_name_py}")

        # Parâmetros obrigatórios primeiro, depois opcionais
        init_params_list = ["self"] + parent_required_params + required_params + optional_params

        lines.append("    " * base_indent_level + f"def __init__({', '.join(init_params_list)}):")
        lines.append("    " * body_indent_level + f'"""Construtor para {to_pascal_case(self.classe.nome)}."""')
        if not init_body_lines:
            lines.append("    " * body_indent_level + "pass")
        else:
            for line_code in init_body_lines:
                lines.append("    " * body_indent_level + line_code)
        lines.append("    " * base_indent_level + "")
        return lines

    def _generate_method_lines(self, met: "PlantUMLMetodo") -> List[str]:
        """
        Gera as linhas de código para um método da classe.

        Args:
            met: Método a ser gerado.

        Returns:
            Lista de linhas de código para o método.
        """
        method_lines: List[str] = []
        base_indent_level = 1 # Indentação para 'def nome(...):'
        body_indent_level = 2 # Indentação para o corpo do método
        
        method_decorators = []
        if met.is_static: method_decorators.append("@staticmethod")
        if met.is_abstract: method_decorators.append("@abstractmethod")
        for decorator in method_decorators: 
            method_lines.append("    " * base_indent_level + decorator)

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
        if met.visibilidade == "-": method_name_py = f"__{method_name_py}"
        elif met.visibilidade == "#": method_name_py = f"_{method_name_py}"

        method_lines.append("    " * base_indent_level + f"def {method_name_py}({', '.join(param_list_for_def)}){return_annotation}:")
        method_lines.append("    " * body_indent_level + f'"""Método {met.nome}."""') # Sua docstring aqui
        method_lines.append("    " * body_indent_level + "pass")
        method_lines.append("    " * base_indent_level + "") # Linha em branco após o método
        return method_lines

    def _get_type_hint_str(self, type_hint: str) -> str:
        """
        Retorna o type hint correto para uso no código Python.
        Corrige casos de Optional[List[Classe]] para Optional['List[Classe]'].
        Corrige casos de List[Classe] para 'List[Classe]'.
        Corrige casos de tipos forward reference para sempre usar aspas simples apenas onde necessário.
        """
        if not type_hint:
            return "Any"
        type_hint = type_hint.replace("'", "").replace('"', "").strip()
        import re
        # Corrige Optional[List[Classe]] e similares
        optional_match = re.match(r"Optional\[(.+)\]", type_hint)
        if optional_match:
            inner = optional_match.group(1)
            inner = inner.replace("'", "").replace('"', "")
            # Se for um tipo genérico, também coloca aspas corretamente
            generic_match = re.match(r"(List|Dict|Set|Tuple)\[(.+)\]", inner)
            if generic_match:
                outer = generic_match.group(1)
                inner2 = generic_match.group(2).replace("'", "").replace('"', "")
                return f"Optional['{outer}[{inner2}]']"
            # Se for tipo customizado, coloca aspas
            if inner not in ["str", "int", "float", "bool", "Any", "None", "datetime.date"]:
                return f"Optional['{inner}']"
            return f"Optional[{inner}]"
        # Corrige List[Classe], Dict[Chave, Valor], etc.
        generic_match = re.match(r"(List|Dict|Set|Tuple)\[(.+)\]", type_hint)
        if generic_match:
            outer = generic_match.group(1)
            inner = generic_match.group(2)
            inner = inner.replace("'", "").replace('"', "")
            # Se for tipo customizado, coloca aspas
            if inner not in ["str", "int", "float", "bool", "Any", "None", "datetime.date"]:
                return f"'{outer}[{inner}]'"
            return f"{outer}[{inner}]"
        # Se não for tipo built-in, retorna com aspas simples
        if type_hint not in ["str", "int", "float", "bool", "Any", "None", "datetime.date"]:
            return f"'{type_hint}'"
        return type_hint

    def generate_code_lines(self) -> List[str]:
        """
        Gera as linhas de código para o corpo completo da classe,
        incluindo atributos estáticos, construtor e métodos.

        Retorna:
            Uma lista de strings representando o corpo da classe.
        """
        lines: List[str] = []
        
        lines.extend(self._generate_static_attribute_lines())
        lines.extend(self._generate_init_lines())
        
        for met in self.classe.metodos:
            lines.extend(self._generate_method_lines(met))
            
        # Adicionar um 'pass' se a classe estiver completamente vazia após todas as gerações
        # (sem atributos estáticos, sem __init__ gerado, sem métodos)
        instance_attributes = [attr for attr in self.classe.atributos if not attr.is_static]
        if not self.classe.atributos and not self.classe.metodos and not \
           (instance_attributes or self.classe.classe_pai) : # Se __init__ não foi gerado
            lines.append("    pass") # Adiciona 'pass' com indentação de classe
        elif not lines: # Se por algum motivo a lista de linhas ainda estiver vazia.
            lines.append("    pass")

        return lines