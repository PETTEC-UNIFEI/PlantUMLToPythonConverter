from typing import List, Optional
from .plantuml_parametro import PlantUMLParametro

class PlantUMLMetodo:
    """Representa um método definido em uma classe ou interface PlantUML."""

    def __init__(self,
                 nome: str,
                 parametros: Optional[List[PlantUMLParametro]] = None,
                 tipo_retorno: Optional[str] = None,
                 visibilidade: Optional[str] = None,
                 is_static: bool = False,
                 is_abstract: bool = False):
        """
        Inicializa uma nova instância de PlantUMLMetodo.

        Args:
            nome: O nome do método.
            parametros: Uma lista de objetos PlantUMLParametro representando os parâmetros do método.
                    Opcional, o padrão é uma lista vazia.
            tipo_retorno: O tipo de dado retornado pelo método.
                    Opcional, o padrão é None.
            visibilidade: A visibilidade do método (ex: "+", "-").
                    Opcional, o padrão é None.
            is_static: True se o método for estático, False caso contrário.
                    O padrão é False.
            is_abstract: True se o método for abstrato, False caso contrário.
                    O padrão é False.
        """
        
        self.nome: str = nome
        self.parametros: List[PlantUMLParametro] = parametros if parametros is not None else []
        self.tipo_retorno: Optional[str] = tipo_retorno
        self.visibilidade: Optional[str] = visibilidade
        self.is_static: bool = is_static
        self.is_abstract: bool = is_abstract

    def __repr__(self) -> str:
        """Retorna uma representação em string do objeto PlantUMLMetodo."""
        
        static_modifier = " static" if self.is_static else ""
        abstract_modifier = " abstract" if self.is_abstract else ""
        return (f"PlantUMLMetodo(nome='{self.nome}', parametros={len(self.parametros)}, "
                f"retorno='{self.tipo_retorno}', visibilidade='{self.visibilidade}'"
                f"{static_modifier}{abstract_modifier})")