"""
Teste básico do gerador de classes C#.
"""
from back_end.plantuml_parser.data_structures import (
    PlantUMLClasse, PlantUMLAtributo, PlantUMLMetodo, PlantUMLParametro
)
from back_end.csharp_generator.structure_generators.class_generator import ClassGenerator
from back_end.csharp_generator.type_mapper import TypeMapper
from back_end.csharp_generator.using_manager import UsingManager

def test_simple_class_generation():
    """Testa a geração de uma classe simples."""
    
    # Cria atributos de teste
    atributos = [
        PlantUMLAtributo(
            nome="nome", 
            tipo="String", 
            visibilidade="+",
            default_value=None,
            is_static=False
        ),
        PlantUMLAtributo(
            nome="idade", 
            tipo="int", 
            visibilidade="+",
            default_value=None,
            is_static=False
        ),
        PlantUMLAtributo(
            nome="contador", 
            tipo="int", 
            visibilidade="+",
            default_value="0",
            is_static=True
        )
    ]
    
    # Cria métodos de teste
    metodos = [
        PlantUMLMetodo(
            nome="obterNome",
            parametros=[],
            tipo_retorno="String",
            visibilidade="+",
            is_static=False,
            is_abstract=False
        ),
        PlantUMLMetodo(
            nome="definirIdade",
            parametros=[
                PlantUMLParametro(nome="novaIdade", tipo="int")
            ],
            tipo_retorno="void",
            visibilidade="+",
            is_static=False,
            is_abstract=False
        ),
        PlantUMLMetodo(
            nome="incrementarContador",
            parametros=[],
            tipo_retorno="void",
            visibilidade="+",
            is_static=True,
            is_abstract=False
        )
    ]
    
    # Cria a classe de teste
    classe_teste = PlantUMLClasse(
        nome="Pessoa",
        atributos=atributos,
        metodos=metodos,
        classe_pai=None,
        interfaces_implementadas=[],
        is_abstract=False
    )
    
    # Configura os geradores
    type_mapper = TypeMapper()
    using_manager = UsingManager()
    current_namespace = "TestNamespace"
    
    # Gera o código
    generator = ClassGenerator(classe_teste, type_mapper, using_manager, current_namespace)
    code_lines = generator.generate_code_lines()
    
    # Imprime o resultado
    print("=== Classe C# Gerada ===")
    print(f"namespace {current_namespace}")
    print("{")
    print("    public class Pessoa")
    print("    {")
    
    for line in code_lines:
        print(line)
    
    print("    }")
    print("}")
    print("\n=== Using Statements ===")
    
    # Gera using statements
    usings = using_manager.collect_usings_for_structure(classe_teste, current_namespace, type_mapper)
    using_statements = using_manager.format_using_statements(usings)
    
    for using_stmt in using_statements:
        print(using_stmt)

def test_inheritance_class():
    """Testa a geração de uma classe com herança."""
    
    # Classe filha
    atributos = [
        PlantUMLAtributo(
            nome="departamento", 
            tipo="String", 
            visibilidade="-",
            default_value=None,
            is_static=False
        ),
        PlantUMLAtributo(
            nome="disciplinas", 
            tipo="List<Disciplina>", 
            visibilidade="+",
            default_value=None,
            is_static=False
        )
    ]
    
    metodos = [
        PlantUMLMetodo(
            nome="lecionar",
            parametros=[
                PlantUMLParametro(nome="disciplina", tipo="Disciplina")
            ],
            tipo_retorno="void",
            visibilidade="+",
            is_static=False,
            is_abstract=False
        )
    ]
    
    classe_professor = PlantUMLClasse(
        nome="Professor",
        atributos=atributos,
        metodos=metodos,
        classe_pai="Pessoa do Sistema",
        interfaces_implementadas=["Autenticavel"],
        is_abstract=False
    )
    
    # Configura os geradores
    type_mapper = TypeMapper()
    using_manager = UsingManager()
    current_namespace = "TestNamespace.Pessoas"
    
    # Gera o código
    generator = ClassGenerator(classe_professor, type_mapper, using_manager, current_namespace)
    code_lines = generator.generate_code_lines()
    
    # Imprime o resultado
    print("\n=== Classe Professor C# Gerada ===")
    print(f"namespace {current_namespace}")
    print("{")
    print("    public class Professor : PessoaDoSistema, Autenticavel")
    print("    {")
    
    for line in code_lines:
        print(line)
    
    print("    }")
    print("}")

if __name__ == "__main__":
    test_simple_class_generation()
    test_inheritance_class()
