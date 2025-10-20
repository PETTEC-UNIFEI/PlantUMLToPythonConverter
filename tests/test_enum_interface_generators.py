"""
Teste dos geradores de enum e interface C#.
"""
from back_end.plantuml_parser.data_structures import (
    PlantUMLEnum, PlantUMLInterface, PlantUMLAtributo, PlantUMLMetodo, PlantUMLParametro
)
from back_end.csharp_generator.structure_generators.enum_generator import EnumGenerator
from back_end.csharp_generator.structure_generators.interface_generator import InterfaceGenerator
from back_end.csharp_generator.type_mapper import TypeMapper
from back_end.csharp_generator.using_manager import UsingManager

def test_enum_generation():
    """Testa a geração de um enum simples."""
    
    # Cria enum de teste
    enum_teste = PlantUMLEnum(
        nome="StatusPedido",
        valores_enum=["PENDENTE", "PROCESSANDO", "CONCLUIDO = 5", "CANCELADO"]
    )
    
    # Configura geradores
    type_mapper = TypeMapper()
    using_manager = UsingManager()
    current_namespace = "TestNamespace.Enums"
    
    # Gera o código
    generator = EnumGenerator(enum_teste, type_mapper, using_manager, current_namespace)
    code_lines = generator.generate_code_lines()
    underlying_type = generator.get_enum_underlying_type()
    
    # Imprime o resultado
    print("=== Enum C# Gerado ===")
    print(f"namespace {current_namespace}")
    print("{")
    print(f"    public enum StatusPedido : {underlying_type}")
    print("    {")
    
    for line in code_lines:
        print(line)
    
    print("    }")
    print("}")

def test_interface_generation():
    """Testa a geração de uma interface."""
    
    # Cria atributos de teste (constantes da interface)
    atributos = [
        PlantUMLAtributo(
            nome="TIMEOUT_PADRAO", 
            tipo="int", 
            visibilidade="+",
            default_value="30",
            is_static=True
        ),
        PlantUMLAtributo(
            nome="versao", 
            tipo="String", 
            visibilidade="+",
            default_value=None,
            is_static=False
        )
    ]
    
    # Cria métodos de teste
    metodos = [
        PlantUMLMetodo(
            nome="processar",
            parametros=[
                PlantUMLParametro(nome="dados", tipo="String")
            ],
            tipo_retorno="boolean",
            visibilidade="+",
            is_static=False,
            is_abstract=True
        ),
        PlantUMLMetodo(
            nome="obterConfiguracaoPadrao",
            parametros=[],
            tipo_retorno="Dictionary<String, Object>",
            visibilidade="+",
            is_static=True,
            is_abstract=False
        ),
        PlantUMLMetodo(
            nome="validar",
            parametros=[
                PlantUMLParametro(nome="entrada", tipo="Object")
            ],
            tipo_retorno="void",
            visibilidade="+",
            is_static=False,
            is_abstract=True
        )
    ]
    
    # Cria a interface de teste
    interface_teste = PlantUMLInterface(
        nome="IProcessador",
        atributos=atributos,
        metodos=metodos,
        interfaces_pai=["IDisposable"]
    )
    
    # Configura geradores
    type_mapper = TypeMapper()
    using_manager = UsingManager()
    current_namespace = "TestNamespace.Interfaces"
    
    # Gera o código
    generator = InterfaceGenerator(interface_teste, type_mapper, using_manager, current_namespace)
    code_lines = generator.generate_code_lines()
    
    # Imprime o resultado
    print("\n=== Interface C# Gerada ===")
    print(f"namespace {current_namespace}")
    print("{")
    print("    public interface IProcessador : IDisposable")
    print("    {")
    
    for line in code_lines:
        print(line)
    
    print("    }")
    print("}")
    
    # Testa using statements
    print("\n=== Using Statements ===")
    usings = using_manager.collect_usings_for_structure(interface_teste, current_namespace, type_mapper)
    using_statements = using_manager.format_using_statements(usings)
    
    for using_stmt in using_statements:
        print(using_stmt)

def test_simple_enum():
    """Testa um enum simples sem valores explícitos."""
    
    enum_simples = PlantUMLEnum(
        nome="DiaSemana",
        valores_enum=["SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO", "DOMINGO"]
    )
    
    type_mapper = TypeMapper()
    using_manager = UsingManager()
    current_namespace = "TestNamespace"
    
    generator = EnumGenerator(enum_simples, type_mapper, using_manager, current_namespace)
    code_lines = generator.generate_code_lines()
    
    print("\n=== Enum Simples C# ===")
    print(f"namespace {current_namespace}")
    print("{")
    print("    public enum DiaSemana")
    print("    {")
    
    for line in code_lines:
        print(line)
    
    print("    }")
    print("}")

if __name__ == "__main__":
    test_enum_generation()
    test_interface_generation()
    test_simple_enum()
