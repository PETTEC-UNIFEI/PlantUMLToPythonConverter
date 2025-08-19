"""
Geração do corpo de classes Python a partir de estruturas PlantUMLClasse.
"""
from typing import List, Set, TYPE_CHECKING
from ..utils import sanitize_name_for_python_module, to_pascal_case

if TYPE_CHECKING:
    from back_end.plantuml_parser.data_structures import PlantUMLClasse, PlantUMLAtributo, PlantUMLMetodo
    from ..type_mapper import TypeMapper

class ClassGenerator:
    """Gera o corpo de uma classe Python, incluindo atributos, construtor e métodos."""
    def __init__(self, 
                 class_structure: "PlantUMLClasse", 
                 type_mapper: "TypeMapper", 
                 current_file_module_dot_path: str,
                 relacionamentos: list = None,
                 parent_classes_from_relationships: list = None):
        self.classe: "PlantUMLClasse" = class_structure
        self.type_mapper: "TypeMapper" = type_mapper
        self.current_file_module_dot_path: str = current_file_module_dot_path
        self.relacionamentos: list = relacionamentos or []
        self.parent_classes_from_relationships: list = parent_classes_from_relationships or []

    def _generate_static_attribute_lines(self) -> List[str]:
        """Gera as linhas de código para os atributos estáticos (de classe)."""
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
                    # CORREÇÃO: Verificar se o valor padrão é string e adicionar aspas se necessário
                    default_value = attr.default_value
                    # BUG 1 CORREÇÃO: Converter valores booleanos do PlantUML para Python
                    if isinstance(default_value, str) and default_value.lower() == 'true':
                        default_val_str = " = True"
                    elif isinstance(default_value, str) and default_value.lower() == 'false':
                        default_val_str = " = False"
                    elif isinstance(default_value, str) and not default_value.isdigit() and default_value not in ['True', 'False', 'None']:
                        # É uma string que não é número nem booleano
                        default_val_str = f' = "{default_value}"'
                    else:
                        default_val_str = f" = {default_value}"
                elif py_type_hint != "Any" and py_type_hint != "None":
                    default_val_str = f" = None"
                elif py_type_hint == "Any":
                     default_val_str = f" = None"
                else: # None
                     default_val_str = " = None"
                
                # CORREÇÃO 5: Usar ClassVar para atributos estáticos
                add_s_line(f"{attr_name_py}: ClassVar[{py_type_hint}]{default_val_str}")
            add_s_line("")
        return lines

    def _generate_relationship_class_attributes(self) -> List[str]:
        """Relacionamentos não devem gerar atributos de classe - apenas de instância no __init__."""
        return []

    def _generate_init_lines(self) -> List[str]:
        """Gera as linhas de código para o método __init__ da classe."""
        lines: List[str] = []
        base_indent_level = 1
        body_indent_level = 2

        parent_required_params = []
        parent_required_args = []
        
        # BUGS 2 e 3 CORREÇÃO: Detectar dinamicamente parâmetros da classe pai baseado em seus atributos
        if self.classe.classe_pai or self.parent_classes_from_relationships:
            parent_name = self.classe.classe_pai or (self.parent_classes_from_relationships[0] if self.parent_classes_from_relationships else "")
            
            # Buscar a classe pai no diagrama para analisar seus atributos
            parent_class = None
            if hasattr(self.type_mapper, 'parsed_diagram') and self.type_mapper.parsed_diagram:
                for elemento in self.type_mapper.parsed_diagram.elementos:
                    if hasattr(elemento, 'nome') and elemento.nome == parent_name:
                        parent_class = elemento
                        break
            
            # Se encontrou a classe pai e é uma classe concreta (não interface)
            if parent_class and hasattr(parent_class, 'atributos') and not hasattr(parent_class, 'is_interface'):
                # Extrair TODOS os atributos não-estáticos da classe pai (com e sem valor padrão)
                for attr in parent_class.atributos:
                    if not attr.is_static:
                        param_name = sanitize_name_for_python_module(attr.nome)
                        py_type_hint, _, _ = self.type_mapper.get_python_type_hint_and_imports(
                            attr.tipo, self.current_file_module_dot_path
                        )
                        
                        # Se tem valor padrão, é opcional no construtor
                        if attr.default_value is not None:
                            # Converter valor padrão booleano
                            default_val = attr.default_value
                            if isinstance(default_val, str) and default_val.lower() == 'true':
                                default_val = 'True'
                            elif isinstance(default_val, str) and default_val.lower() == 'false':
                                default_val = 'False'
                            elif isinstance(default_val, str) and not default_val.isdigit() and default_val not in ['True', 'False', 'None']:
                                default_val = f'"{default_val}"'
                            
                            parent_required_params.append(f"{param_name}: {py_type_hint} = {default_val}")
                        else:
                            parent_required_params.append(f"{param_name}: {py_type_hint}")
                        
                        parent_required_args.append(param_name)
            # Para interfaces ou classes não encontradas, não gerar parâmetros

        instance_attributes = [attr for attr in self.classe.atributos if not attr.is_static]
        relationship_attributes = []
        used_names = set()
        
        # Consolida relacionamentos únicos por classe de destino
        consolidated_relationships = {}
        for rel in self.relacionamentos:
            dest_class = rel.destino
            if dest_class not in consolidated_relationships:
                consolidated_relationships[dest_class] = rel
            else:
                # Se já existe, mantém o que tem cardinalidade múltipla (*)
                existing = consolidated_relationships[dest_class]
                if rel.cardinalidade_destino and "*" in rel.cardinalidade_destino:
                    consolidated_relationships[dest_class] = rel
        
        for dest_class, rel in consolidated_relationships.items():
            # Usar o nome da classe de destino como base para o atributo
            base_name = sanitize_name_for_python_module(dest_class)
            
            # BUG 5 CORREÇÃO: Classes de associação devem ter relacionamentos singulares
            is_association_class = self._is_association_class()
            is_multiple = (not is_association_class and 
                          rel.cardinalidade_destino and 
                          ("*" in rel.cardinalidade_destino or rel.cardinalidade_destino.strip() in ["0..*", "1..*", "n"]))
            
            # Para relacionamentos múltiplos, usar plural
            if is_multiple:
                # Tentativa simples de pluralização
                if base_name.endswith('s'):
                    attr_name = base_name + "es"
                elif base_name.endswith('y'):
                    attr_name = base_name[:-1] + "ies"
                else:
                    attr_name = base_name + "s"
            else:
                attr_name = base_name
            
            # Garantir unicidade
            original_attr_name = attr_name
            counter = 1
            while attr_name in used_names:
                counter += 1
                attr_name = f"{original_attr_name}_{counter}"
            used_names.add(attr_name)
            
            tipo_destino = dest_class
            py_type_hint, _, _ = self.type_mapper.get_python_type_hint_and_imports(tipo_destino, self.current_file_module_dot_path)
            if is_multiple:
                py_type_hint = f"List[{py_type_hint}]"
            param_str = f"{attr_name}: Optional[{py_type_hint}] = None"
            relationship_attributes.append(param_str)
        if not instance_attributes and not self.classe.classe_pai and not relationship_attributes:
            return []

        required_params = []
        optional_params = []
        init_body_lines: List[str] = []

        # Verifica se há herança (seja na estrutura original ou por relacionamentos)
        has_parent = self.classe.classe_pai or self.parent_classes_from_relationships
        
        if has_parent:
            # CORREÇÃO: Usar dinamicamente os argumentos necessários da classe pai
            if parent_required_args:
                init_body_lines.append(f"super().__init__({', '.join(parent_required_args)})")
            else:
                init_body_lines.append("super().__init__()")

        for attr in instance_attributes:
            param_name_py = sanitize_name_for_python_module(attr.nome)
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
                # CORREÇÃO: Verificar se o valor padrão é string e adicionar aspas se necessário
                default_value = attr.default_value
                # BUG 1 CORREÇÃO: Converter valores booleanos do PlantUML para Python
                if isinstance(default_value, str) and default_value.lower() == 'true':
                    default_assignment_for_param = " = True"
                elif isinstance(default_value, str) and default_value.lower() == 'false':
                    default_assignment_for_param = " = False"
                elif isinstance(default_value, str) and not default_value.isdigit() and default_value not in ['True', 'False', 'None']:
                    default_assignment_for_param = f' = "{default_value}"'
                else:
                    default_assignment_for_param = f" = {default_value}"
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
        
        # Adiciona inicialização dos atributos de relacionamento (usando a mesma lógica consolidada)
        used_names = set()
        
        # Consolida relacionamentos únicos por classe de destino
        consolidated_relationships = {}
        for rel in self.relacionamentos:
            dest_class = rel.destino
            if dest_class not in consolidated_relationships:
                consolidated_relationships[dest_class] = rel
            else:
                # Se já existe, mantém o que tem cardinalidade múltipla (*)
                existing = consolidated_relationships[dest_class]
                if rel.cardinalidade_destino and "*" in rel.cardinalidade_destino:
                    consolidated_relationships[dest_class] = rel
        
        for dest_class, rel in consolidated_relationships.items():
            # Usar o nome da classe de destino como base para o atributo
            base_name = sanitize_name_for_python_module(dest_class)
            
            # BUG 5 CORREÇÃO: Classes de associação devem ter relacionamentos singulares
            is_association_class = self._is_association_class()
            is_multiple = (not is_association_class and 
                          rel.cardinalidade_destino and 
                          ("*" in rel.cardinalidade_destino or rel.cardinalidade_destino.strip() in ["0..*", "1..*", "n"]))
            
            # Para relacionamentos múltiplos, usar plural
            if is_multiple:
                # Tentativa simples de pluralização
                if base_name.endswith('s'):
                    attr_name = base_name + "es"
                elif base_name.endswith('y'):
                    attr_name = base_name[:-1] + "ies"
                else:
                    attr_name = base_name + "s"
            else:
                attr_name = base_name
            
            # Garantir unicidade
            original_attr_name = attr_name
            counter = 1
            while attr_name in used_names:
                counter += 1
                attr_name = f"{original_attr_name}_{counter}"
            used_names.add(attr_name)
            
            if is_multiple:
                init_body_lines.append(f"self.{attr_name}: List['{dest_class}'] = [] if {attr_name} is None else {attr_name}")
            else:
                init_body_lines.append(f"self.{attr_name}: '{dest_class}' = {attr_name}")

        init_params_list = ["self"] + parent_required_params + required_params + optional_params + relationship_attributes

        lines.append("    " * base_indent_level + f"def __init__({', '.join(init_params_list)}):")
        lines.append("    " * body_indent_level + f'"""Construtor para {to_pascal_case(self.classe.nome)}."""')
        if not init_body_lines:
            lines.append("    " * body_indent_level + "pass")
        else:
            for line_code in init_body_lines:
                lines.append("    " * body_indent_level + line_code)
        lines.append("    " * base_indent_level + "")
        return lines

    def _is_association_class(self) -> bool:
        """BUG 5 CORREÇÃO: Determina se esta classe é uma classe de associação."""
        # Uma classe de associação conecta exatamente 2 outras classes em relacionamentos many-to-many
        # É identificada por ter exatamente 2 relacionamentos de saída ou pelo nome típico
        
        outgoing_relationships = [rel for rel in self.relacionamentos if rel.origem == self.classe.nome]
        
        # Classes de associação típicas por nome
        name_suggests_association = self.classe.nome in ['Avaliacao', 'Participacao', 'Inscricao', 'Matricula', 'Associacao', 'Vinculo']
        
        # Se tem exatamente 2 relacionamentos de saída, é muito provável que seja classe de associação
        has_two_outgoing = len(outgoing_relationships) == 2
        
        # Se o nome sugere ser de associação, forçar detecção
        if name_suggests_association:
            return True
            
        # Se tem 2 relacionamentos de saída para classes diferentes, também é classe de associação
        if has_two_outgoing:
            target_classes = [rel.destino for rel in outgoing_relationships]
            if len(set(target_classes)) == 2:  # Duas classes diferentes
                return True
        
        return False

    def _generate_method_lines(self, met: "PlantUMLMetodo") -> List[str]:
        """Gera as linhas de código para um método da classe."""
        method_lines: List[str] = []
        base_indent_level = 1
        body_indent_level = 2
        
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
        method_lines.append("    " * body_indent_level + f'"""Método {met.nome}."""')
        method_lines.append("    " * body_indent_level + "pass")
        method_lines.append("    " * base_indent_level + "")
        return method_lines

    def _get_type_hint_str(self, type_hint: str) -> str:
        """Retorna o type hint formatado para uso no código."""
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
        """Gera as linhas de código para o corpo completo da classe, incluindo atributos de relacionamento."""
        lines: List[str] = []
        lines.extend(self._generate_static_attribute_lines())
        lines.extend(self._generate_relationship_class_attributes())
        lines.extend(self._generate_init_lines())
        for met in self.classe.metodos:
            lines.extend(self._generate_method_lines(met))
        instance_attributes = [attr for attr in self.classe.atributos if not attr.is_static]
        if not self.classe.atributos and not self.classe.metodos and not \
           (instance_attributes or self.classe.classe_pai or self.relacionamentos):
            lines.append("    pass")
        elif not lines:
            lines.append("    pass")
        return lines