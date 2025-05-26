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