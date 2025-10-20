import re

class ImportManager:
    """
    Gerencia imports necessários para arquivos Java.
    """

    # Tipos que exigem import
    JAVA_IMPORTS = {
        "List": "java.util.List",
        "ArrayList": "java.util.ArrayList",
        "Set": "java.util.Set",
        "HashSet": "java.util.HashSet",
        "Map": "java.util.Map",
        "HashMap": "java.util.HashMap",
        "Queue": "java.util.Queue",
        "Deque": "java.util.Deque",
        "Stack": "java.util.Stack",
        "Collection": "java.util.Collection",
        "Date": "java.util.Date",
        "LocalDateTime": "java.time.LocalDateTime",
        "LocalTime": "java.time.LocalTime",
        "Duration": "java.time.Duration"
    }

    def collect_imports_for_structure(self, structure, package, type_mapper):
        """
        Coleta todos os imports necessários para uma estrutura Java (classe, enum, interface).
        """
        imports = set()

        # Verifica atributos
        for attr in getattr(structure, "atributos", []):
            imports.update(self._imports_from_type(attr.tipo, type_mapper))

        # Verifica métodos
        for metodo in getattr(structure, "metodos", []):
            # Retorno
            if hasattr(metodo, "tipo_retorno"):
                imports.update(self._imports_from_type(metodo.tipo_retorno, type_mapper))
            # Parâmetros
            for param in getattr(metodo, "parametros", []):
                imports.update(self._imports_from_type(param.tipo, type_mapper))

        # Remove imports do próprio pacote, se necessário
        imports = {imp for imp in imports if not imp.startswith(package)}
        return imports

    def _imports_from_type(self, tipo, type_mapper):
        """
        Retorna o conjunto de imports necessários para um tipo (inclui genéricos).
        """
        imports = set()
        # Remove genéricos, pega tipo base
        if not tipo:
            return imports
        # Se for genérico: ex: List<String>, Map<Integer, Object>
        match = re.match(r"(\w+)<(.+)>", tipo)
        if match:
            base = match.group(1)
            if base in self.JAVA_IMPORTS:
                imports.add(self.JAVA_IMPORTS[base])
            # Verifica os parâmetros genéricos
            params = [p.strip() for p in match.group(2).split(",")]
            for p in params:
                imports.update(self._imports_from_type(p, type_mapper))
        else:
            # Tipo simples
            if tipo in self.JAVA_IMPORTS:
                imports.add(self.JAVA_IMPORTS[tipo])
        return imports

    def format_import_statements(self, imports):
        """
        Formata os imports para linhas de código Java.
        """
        return [f"import {imp};" for imp in sorted(imports)]