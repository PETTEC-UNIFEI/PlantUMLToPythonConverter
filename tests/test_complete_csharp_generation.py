"""
Teste completo do sistema de geração C#.
"""
import tempfile
import os
from back_end.plantuml_parser.data_structures import (
    PlantUMLDiagrama, PlantUMLClasse, PlantUMLEnum, PlantUMLInterface, 
    PlantUMLAtributo, PlantUMLMetodo, PlantUMLParametro, PlantUMLPacote
)
from back_end.csharp_generator.main_generator import MainCodeGenerator

def test_complete_generation():
    """Testa a geração completa de um projeto C#."""
    
    # Cria um enum
    status_enum = PlantUMLEnum(
        nome="StatusPedido",
        valores_enum=["PENDENTE", "PROCESSANDO", "CONCLUIDO = 5", "CANCELADO"]
    )
    
    # Cria uma interface
    processador_interface = PlantUMLInterface(
        nome="IProcessador",
        atributos=[
            PlantUMLAtributo(
                nome="TIMEOUT_PADRAO", 
                tipo="int", 
                visibilidade="+",
                default_value="30",
                is_static=True
            )
        ],
        metodos=[
            PlantUMLMetodo(
                nome="processar",
                parametros=[PlantUMLParametro(nome="dados", tipo="String")],
                tipo_retorno="boolean",
                visibilidade="+",
                is_static=False,
                is_abstract=True
            )
        ],
        interfaces_pai=["IDisposable"]
    )
    
    # Cria uma classe
    pedido_classe = PlantUMLClasse(
        nome="Pedido",
        atributos=[
            PlantUMLAtributo(
                nome="id", 
                tipo="String", 
                visibilidade="+",
                default_value=None,
                is_static=False
            ),
            PlantUMLAtributo(
                nome="status", 
                tipo="StatusPedido", 
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
        ],
        metodos=[
            PlantUMLMetodo(
                nome="obterStatus",
                parametros=[],
                tipo_retorno="StatusPedido",
                visibilidade="+",
                is_static=False,
                is_abstract=False
            ),
            PlantUMLMetodo(
                nome="atualizarStatus",
                parametros=[PlantUMLParametro(nome="novoStatus", tipo="StatusPedido")],
                tipo_retorno="void",
                visibilidade="+",
                is_static=False,
                is_abstract=False
            )
        ],
        classe_pai=None,
        interfaces_implementadas=["IProcessador"],
        is_abstract=False
    )
    
    # Cria o diagrama
    diagrama = PlantUMLDiagrama()
    diagrama.adicionar_elemento(status_enum)
    diagrama.adicionar_elemento(processador_interface)
    diagrama.adicionar_elemento(pedido_classe)
    
    # Gera arquivos
    with tempfile.TemporaryDirectory() as temp_dir:
        generator = MainCodeGenerator(
            parsed_diagram=diagrama,
            output_base_dir=temp_dir,
            diagram_name="SistemaDevendas",
            base_namespace="SistemaVendas"
        )
        
        generated_files = generator.generate_files()
        
        print("=== Arquivos Gerados ===")
        for file_path in generated_files:
            print(f"- {os.path.basename(file_path)}")
        
        print(f"\nProjeto gerado em: {generator.output_base_dir}")
        
        # Mostra conteúdo dos arquivos gerados
        for file_path in generated_files:
            if file_path.endswith('.cs'):
                print(f"\n=== Conteúdo de {os.path.basename(file_path)} ===")
                with open(file_path, 'r', encoding='utf-8') as f:
                    print(f.read())
        
        return generator.output_base_dir

if __name__ == "__main__":
    test_complete_generation()
