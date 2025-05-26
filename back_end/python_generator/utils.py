"""
Módulo de utilitários para o gerador de código Python.

Contém funções auxiliares para sanitizar e formatar nomes de acordo com
as convenções Python para módulos, classes e variáveis.
"""
import re
import unicodedata

def remove_accents_and_specials(name: str) -> str:
    """
    Remove acentos e substitui 'ç' por 'c' em uma string.

    Args:
        name: Nome original a ser convertido.

    Returns:
        Nome sem acentos e cedilha.
    """
    name = name.replace('ç', 'c').replace('Ç', 'C')
    nfkd = unicodedata.normalize('NFKD', name)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def sanitize_name_for_python_module(name: str) -> str:
    """
    Converte um nome genérico para snake_case, removendo caracteres inválidos,
    acentos e cedilha. Útil para nomes de arquivos e variáveis/funções.

    Args:
        name: Nome original a ser convertido.

    Returns:
        Nome em snake_case, pronto para uso como identificador Python.
    """
    name = remove_accents_and_specials(name)
    name = name.replace('"', '') # Remove aspas que podem vir de nomes PlantUML
    # Converte CamelCase/PascalCase para snake_case e lida com espaços
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    name = re.sub(r'\s+', '_', name) # Substitui espaços restantes por underscores
    name = re.sub(r'[^0-9a-zA-Z_]', '', name) # Remove caracteres não alfanuméricos exceto underscore
    name = re.sub(r'_+', '_', name)  # Remove duplo underline
    name = name.strip('_') # Remove underscores no início/fim
    if not name:
        return "_unnamed_module_or_variable"
    if name[0].isdigit():
        name = "_" + name
    return name

def to_pascal_case(name: str) -> str:
    """
    Converte um nome genérico para PascalCase, removendo acentos e cedilha,
    adequado para nomes de classes.

    Args:
        name: Nome original a ser convertido.

    Returns:
        Nome em PascalCase.
    """
    name = remove_accents_and_specials(name)
    name = name.strip().replace('"', '')
    # Divide por underline, espaço ou transição minúscula/maiúscula para melhor PascalCase
    parts = re.split(r'[_\s]+', name)
    if len(parts) == 1 and name: # Se não dividiu por _ ou espaço, tenta por CamelCase
        parts = re.findall(r'[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])', name)
    
    capitalized_parts = [p.capitalize() for p in parts if p]
    pascal_case_name = "".join(capitalized_parts)
    
    if not pascal_case_name:
        return "_UnnamedClass" # Fallback se o nome original só tinha caracteres especiais
    if pascal_case_name[0].isdigit():
        return "_" + pascal_case_name
    return pascal_case_name