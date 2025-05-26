"""
Parser para diagramas PlantUML focado em diagramas de classe.

Transforma o código PlantUML em estruturas Python para posterior geração de código.
"""
from typing import List, Any, Optional
from .data_structures import (
    PlantUMLDiagrama, PlantUMLClasse, PlantUMLAtributo, PlantUMLMetodo,
    PlantUMLParametro, PlantUMLPacote, PlantUMLEnum, PlantUMLInterface,
    PlantUMLRelacionamento
)
from .lexer import lexer 
import ply.lex as lex 
import re


class PlantUMLParser:
    """
    Faz o parsing dos tokens do PlantUML e monta o objeto PlantUMLDiagrama.
    """
    
    def __init__(self):
        """
        Inicializa uma nova instância do PlantUMLParser.
        """
        self.tokens: List[lex.LexToken] = []
        self.token_idx: int = 0
        self.diagrama: PlantUMLDiagrama = PlantUMLDiagrama()
        self.contexto_atual_pilha: List[Any] = []

    def _peek_token(self, offset: int = 0) -> Optional[lex.LexToken]:
        """Espia o token atual ou um token futuro sem consumi-lo."""
        idx = self.token_idx + offset
        if 0 <= idx < len(self.tokens):
            return self.tokens[idx]
        return None

    def _consume_token(self, expected_type: Optional[str] = None) -> lex.LexToken:
        """Consome o token atual e avança. Levanta erro se não for o tipo esperado."""
        if self.token_idx < len(self.tokens):
            token = self.tokens[self.token_idx]
            if expected_type and token.type != expected_type:
                self._parse_error(f"Esperado token {expected_type}, mas encontrou {token.type} ('{token.value}')")
            self.token_idx += 1
            return token
        self._parse_error("Fim inesperado da entrada de tokens.")
        raise RuntimeError("Esta linha não deveria ser alcançada.")


    def _parse_error(self, message: str):
        """Lança um erro de sintaxe com informações da linha atual."""
        token_para_linha = self._peek_token() or (self.tokens[self.token_idx -1] if self.token_idx > 0 and self.tokens else None)
        line = token_para_linha.lineno if token_para_linha else self.tokens[0].lineno if self.tokens else 'desconhecida'
        val = token_para_linha.value if token_para_linha else "EOF"
        raise SyntaxError(f"Erro de sintaxe na linha {line} perto de '{val}': {message}")

    def _obter_contexto_atual(self) -> Any:
        """Retorna o topo da pilha de contexto, se houver."""
        if self.contexto_atual_pilha:
            return self.contexto_atual_pilha[-1]
        return None

    def _adicionar_elemento_ao_contexto_ou_diagrama(self, elemento: Any):
        """Adiciona um elemento ao contexto atual (pacote) ou ao diagrama principal."""
        contexto = self._obter_contexto_atual()
        if contexto and isinstance(contexto, PlantUMLPacote):
            contexto.adicionar_elemento(elemento)
        else:
            self.diagrama.adicionar_elemento(elemento)
    
    def _traduzir_seta_para_tipo_relacionamento(self, seta_token_type: str, seta_value: str) -> str:
        """
        Traduz o TIPO e VALOR do token da seta para um tipo de relacionamento textual.
        Ajustado para dar prioridade e corrigir mapeamentos.
        """
        # Prioridade para setas mais específicas baseadas no valor e depois no tipo
        if seta_token_type == 'ARROW_INHERITANCE_LEFT' or seta_value == "<|--": return "heranca"
        if seta_token_type == 'ARROW_INHERITANCE_RIGHT' or seta_value == "--|>": return "heranca"
        
        if seta_token_type == 'ARROW_IMPLEMENTATION_LEFT_STRONG' or seta_value == "<|..": return "implementacao"
        if seta_token_type == 'ARROW_IMPLEMENTATION_RIGHT_STRONG' or seta_value == "..|>": return "implementacao"
        
        if seta_token_type == 'ARROW_COMPOSITION_LEFT' or seta_value == "*--": return "composicao"
        if seta_token_type == 'ARROW_COMPOSITION_RIGHT' or seta_value == "--*": return "composicao"
        
        if seta_token_type == 'ARROW_AGGREGATION_LEFT' or seta_value == "o--": return "agregacao"
        if seta_token_type == 'ARROW_AGGREGATION_RIGHT' or seta_value == "--o": return "agregacao"

        # Dependências (pontilhadas)
        if seta_token_type == 'ARROW_DIRECTED_DEPENDENCY_LEFT' or seta_value == "<..": return "dependencia"
        if seta_token_type == 'ARROW_DIRECTED_DEPENDENCY_RIGHT' or seta_value == "..>": return "dependencia"
        if seta_token_type == 'ARROW_DEPENDENCY_LINE' or seta_value == "..": return "dependencia"
        
        # Associações (linhas contínuas) - por último como fallback para linhas
        if seta_token_type == 'ARROW_DIRECTED_ASSOCIATION_RIGHT' or seta_value == "-->": return "associacao"
        if seta_token_type == 'ARROW_DIRECTED_ASSOCIATION_LEFT' or seta_value == "<--": return "associacao"
        if seta_token_type == 'ARROW_ASSOCIATION_LINE' or seta_value == "--": return "associacao"
        
        return "associacao_desconhecida"


    def _parse_parametros_metodo(self) -> List[PlantUMLParametro]:
        """Parseia a lista de parâmetros de um método: (param1: Tipo1, param2: Tipo2)."""
        params = []
        self._consume_token('LPAREN')
        while self._peek_token() and self._peek_token().type != 'RPAREN':
            # Nome do parâmetro
            if self._peek_token().type not in ['ID', 'QUOTED_STRING']:
                 self._parse_error(f"Esperado nome de parâmetro (ID ou QUOTED_STRING), encontrou {self._peek_token().type}")
            nome_param_token = self._consume_token()
            nome_param = nome_param_token.value
            tipo_param = None
            # Tipo do parâmetro (opcional)
            if self._peek_token() and self._peek_token().type == 'COLON':
                self._consume_token('COLON')
                if not self._peek_token() or self._peek_token().type not in ['ID', 'QUOTED_STRING']:
                    self._parse_error(f"Esperado tipo para o parametro {nome_param}")
                tipo_param_token = self._consume_token()
                tipo_param = tipo_param_token.value # Pode ser ID (TipoSimples) ou QUOTED_STRING (List<Tipo>)
                # Se o tipo for um ID e o próximo for '<', é um tipo genérico que o lexer pegou como ID.
                # Ex: ID<ID> -> ID('<') ID('>')
                # Esta lógica de genéricos no tipo de parâmetro precisa ser melhorada se o lexer não os tratar como um token único.
                # Por agora, o lexer t_ID tenta pegar 'Nome<Generico>' como um único ID.
            params.append(PlantUMLParametro(nome=nome_param, tipo=tipo_param))
            
            if self._peek_token() and self._peek_token().type == 'COMMA':
                self._consume_token('COMMA')
            elif self._peek_token() and self._peek_token().type != 'RPAREN':
                self._parse_error("Esperado ',' ou ')' na lista de parâmetros.")
        self._consume_token('RPAREN')
        return params

    def _parse_atributo_ou_metodo(self, estrutura_pai: Any):
        """Parseia um atributo ou um método."""
        visibilidade = None
        is_static = False
        is_abstract = False

        # 1. Visibilidade (opcional)
        if self._peek_token() and self._peek_token().type == 'VISIBILITY':
            visibilidade = self._consume_token('VISIBILITY').value
        
        # 2. Modificadores {static} ou {abstract} (opcionais)
        if self._peek_token() and self._peek_token().type == 'STATIC_MODIFIER':
            self._consume_token('STATIC_MODIFIER')
            is_static = True
        # {abstract} pode ser para método ou para classe/interface.
        # Se for seguido por 'class' ou 'interface', não é um modificador de membro.
        elif self._peek_token() and self._peek_token().type == 'ABSTRACT_MODIFIER':
            # Verifique se o próximo token NÃO é CLASS ou INTERFACE
            # Se for, este {abstract} pertence à declaração da estrutura, não a um membro.
            prox_token_apos_abstract_modifier = self._peek_token(1) # Olhamos um token à frente do {abstract}
            if not (prox_token_apos_abstract_modifier and prox_token_apos_abstract_modifier.type in ['CLASS', 'INTERFACE']):
                self._consume_token('ABSTRACT_MODIFIER')
                is_abstract = True
        
        # 3. Nome do membro (ID ou QUOTED_STRING)
        if not self._peek_token() or self._peek_token().type not in ['ID', 'QUOTED_STRING']:
            # Se o que veio antes foi um modificador e não há nome, é um erro.
            if is_static or is_abstract or visibilidade:
                 self._parse_error(f"Esperado nome para atributo/método após modificadores/visibilidade, encontrou {self._peek_token().type if self._peek_token() else 'EOF'}")
            else: # Pode não ser um membro, então apenas retorna para o loop principal do parse tentar outras regras
                return False # Indica que não parseou um membro

        nome_membro_token = self._consume_token()
        nome_membro = nome_membro_token.value

        # 4. Determinar se é método (tem parênteses) ou atributo
        if self._peek_token() and self._peek_token().type == 'LPAREN': # É um método
            parametros = self._parse_parametros_metodo()
            tipo_retorno = None
            if self._peek_token() and self._peek_token().type == 'COLON':
                self._consume_token('COLON')
                if not self._peek_token() or self._peek_token().type not in ['ID', 'QUOTED_STRING']:
                     self._parse_error(f"Esperado tipo de retorno para o metodo {nome_membro}")
                tipo_retorno_token = self._consume_token()
                tipo_retorno = tipo_retorno_token.value # Pode ser ID (TipoSimples) ou QUOTED_STRING (List<Tipo>)
            
            if visibilidade is None: visibilidade = "+" 
            metodo = PlantUMLMetodo(nome=nome_membro, parametros=parametros, tipo_retorno=tipo_retorno,
                                    visibilidade=visibilidade, is_static=is_static, is_abstract=is_abstract)
            if hasattr(estrutura_pai, 'metodos'):
                estrutura_pai.metodos.append(metodo)
            return True
        else: # É um atributo
            tipo_atributo = None
            valor_default = None
            if self._peek_token() and self._peek_token().type == 'COLON':
                self._consume_token('COLON')
                if not self._peek_token() or self._peek_token().type not in ['ID', 'QUOTED_STRING']:
                    self._parse_error(f"Esperado tipo para o atributo {nome_membro}")
                tipo_atributo_token = self._consume_token()
                tipo_atributo = tipo_atributo_token.value # Pode ser ID (TipoSimples) ou QUOTED_STRING (List<Tipo>)
            
            if self._peek_token() and self._peek_token().type == 'EQUALS':
                self._consume_token('EQUALS')
                if not self._peek_token() or self._peek_token().type not in ['ID', 'QUOTED_STRING']: 
                     self._parse_error(f"Esperado valor default para o atributo {nome_membro}")
                valor_default_token = self._consume_token() 
                valor_default = valor_default_token.value

            if visibilidade is None: visibilidade = "+"
            # CORREÇÃO BUG ESTATICO: is_static só deve ser True se {static} ou {classifier} foi explicitamente encontrado ANTES deste atributo.
            # A flag is_static que pegamos no início da função era para este membro.
            atributo = PlantUMLAtributo(nome=nome_membro, tipo=tipo_atributo, visibilidade=visibilidade,
                                        default_value=valor_default, is_static=is_static) # Usar o is_static correto
            if hasattr(estrutura_pai, 'atributos'):
                estrutura_pai.atributos.append(atributo)
            return True
        return False # Se não conseguiu parsear como atributo ou método


    def _parse_membros_estrutura(self, estrutura_atual: Any):
        """Parseia os membros (atributos, métodos, valores de enum) dentro de um bloco {}."""
        while self._peek_token() and self._peek_token().type != 'RBRACE':
            token_membro_inicio = self._peek_token()
            if isinstance(estrutura_atual, PlantUMLEnum):
                if token_membro_inicio.type == 'ID':
                    valor_enum = self._consume_token('ID').value
                    if hasattr(estrutura_atual, 'valores_enum'): 
                        estrutura_atual.valores_enum.append(valor_enum)
                        estrutura_atual.atributos.append(PlantUMLAtributo(nome=valor_enum, visibilidade="+"))
                elif token_membro_inicio.type == 'RBRACE': 
                    break
                else:
                    self._parse_error(f"Esperado ID para valor de enum ou '}}', encontrou {token_membro_inicio.type}")
            elif isinstance(estrutura_atual, (PlantUMLClasse, PlantUMLInterface)):
                if token_membro_inicio.type in ['VISIBILITY', 'STATIC_MODIFIER', 'ABSTRACT_MODIFIER', 'ID', 'QUOTED_STRING']:
                    if not self._parse_atributo_ou_metodo(estrutura_atual):
                        # Se _parse_atributo_ou_metodo retornar False, significa que não consumiu o token
                        # e não era um membro válido. Pode ser um erro ou algo inesperado.
                        self._parse_error(f"Sintaxe de membro inválida ou token inesperado '{token_membro_inicio.value}' ({token_membro_inicio.type}) em {type(estrutura_atual).__name__} {estrutura_atual.nome}")
                else: # Se não começar com um token esperado para membro
                    self._parse_error(f"Início de membro inesperado '{token_membro_inicio.value}' ({token_membro_inicio.type}) em {type(estrutura_atual).__name__} {estrutura_atual.nome}")
            else: # Não deveria acontecer se o contexto está correto
                self._parse_error(f"Tentando parsear membros em um contexto inesperado: {type(estrutura_atual)}")
        
        # Não consumir '}' aqui, o loop principal do parse ou _parse_declaracao_estrutura (se for bloco) o fará.

    def _parse_declaracao_estrutura(self):
        """Parseia uma declaração de classe, interface ou enum."""
        is_abstract_structure = False
        if self._peek_token() and self._peek_token().type == 'ABSTRACT':
            if self._peek_token(1) and self._peek_token(1).type in ['CLASS', 'INTERFACE']:
                self._consume_token('ABSTRACT')
                is_abstract_structure = True

        tipo_estrutura_token = self._peek_token()
        if not tipo_estrutura_token: self._parse_error("Esperada declaração de estrutura.")

        nome_estrutura: str = "_NomePadrao" # Default
        elemento_novo: Any = None
        
        if tipo_estrutura_token.type == 'CLASS':
            self._consume_token('CLASS')
            nome_token = self._consume_token()
            if nome_token.type not in ['ID', 'QUOTED_STRING']: self._parse_error(f"Esperado nome para CLASS, encontrou {nome_token.type}")
            nome_estrutura = nome_token.value
            
            pai = None
            interfaces = []
            if self._peek_token() and self._peek_token().type == 'EXTENDS':
                self._consume_token('EXTENDS')
                pai_token = self._consume_token()
                if pai_token.type not in ['ID', 'QUOTED_STRING']: self._parse_error("Nome inválido para classe pai.")
                pai = pai_token.value
            
            if self._peek_token() and self._peek_token().type == 'IMPLEMENTS':
                self._consume_token('IMPLEMENTS')
                while self._peek_token() and self._peek_token().type in ['ID', 'QUOTED_STRING']:
                    iface_token = self._consume_token()
                    interfaces.append(iface_token.value)
                    if self._peek_token() and self._peek_token().type == 'COMMA':
                        self._consume_token('COMMA')
                    elif self._peek_token() and self._peek_token().type not in ['ID', 'QUOTED_STRING', 'LBRACE']:
                        break 
                    elif not (self._peek_token() and self._peek_token().type in ['ID', 'QUOTED_STRING']):
                        break
            elemento_novo = PlantUMLClasse(nome=nome_estrutura, is_abstract=is_abstract_structure, classe_pai=pai, interfaces_implementadas=interfaces)
        
        elif tipo_estrutura_token.type == 'INTERFACE':
            self._consume_token('INTERFACE')
            nome_token = self._consume_token()
            if nome_token.type not in ['ID', 'QUOTED_STRING']: self._parse_error(f"Nome inválido para interface.")
            nome_estrutura = nome_token.value
            interfaces_pai = []
            if self._peek_token() and self._peek_token().type == 'EXTENDS':
                self._consume_token('EXTENDS')
                while self._peek_token() and self._peek_token().type in ['ID', 'QUOTED_STRING']:
                    iface_pai_token = self._consume_token()
                    interfaces_pai.append(iface_pai_token.value)
                    if self._peek_token() and self._peek_token().type == 'COMMA':
                        self._consume_token('COMMA')
                    elif self._peek_token() and self._peek_token().type not in ['ID', 'QUOTED_STRING', 'LBRACE']:
                        break
                    elif not (self._peek_token() and self._peek_token().type in ['ID', 'QUOTED_STRING']):
                        break
            elemento_novo = PlantUMLInterface(nome=nome_estrutura, interfaces_pai=interfaces_pai)

        elif tipo_estrutura_token.type == 'ENUM':
            self._consume_token('ENUM')
            nome_token = self._consume_token()
            if nome_token.type not in ['ID', 'QUOTED_STRING']: self._parse_error(f"Nome inválido para enum.")
            nome_estrutura = nome_token.value
            elemento_novo = PlantUMLEnum(nome=nome_estrutura)
        else:
            if is_abstract_structure: 
                self._parse_error(f"Esperado CLASS ou INTERFACE após ABSTRACT, mas encontrou {tipo_estrutura_token.type if tipo_estrutura_token else 'EOF'}")
            else:
                self._parse_error(f"Tipo de estrutura desconhecido ou inesperado: {tipo_estrutura_token.type if tipo_estrutura_token else 'EOF'}")

        if elemento_novo:
            self._adicionar_elemento_ao_contexto_ou_diagrama(elemento_novo)
            if self._peek_token() and self._peek_token().type == 'LBRACE':
                self._consume_token('LBRACE')
                self.contexto_atual_pilha.append(elemento_novo)
                self._parse_membros_estrutura(elemento_novo) 
                # O '}' que fecha o bloco da estrutura deve ser consumido pelo loop principal do parse,
                # que então desempilhará o contexto.
            # Se não houver LBRACE, a estrutura é declarada e considerada fechada (sem corpo de membros aqui).

    def _parse_declaracao_pacote(self):
        """Parseia uma declaração de pacote."""
        self._consume_token('PACKAGE')
        nome_token = self._consume_token()
        if nome_token.type not in ['ID', 'QUOTED_STRING']: self._parse_error(f"Nome inválido para pacote.")
        nome_pacote = nome_token.value
        
        novo_pacote = PlantUMLPacote(nome=nome_pacote)
        self._adicionar_elemento_ao_contexto_ou_diagrama(novo_pacote)
        
        if self._peek_token() and self._peek_token().type == 'LBRACE':
            self._consume_token('LBRACE')
            self.contexto_atual_pilha.append(novo_pacote)
        # '}' será tratado pelo loop principal do parse

    def _parse_relacionamento(self):
        """Parseia uma linha de relacionamento."""
        # print(f"DEBUG: Iniciando _parse_relacionamento. Próximo token: {self._peek_token()}")
        
        origem_token = self._consume_token() 
        if origem_token.type not in ['ID', 'QUOTED_STRING']: 
            self._parse_error(f"Nome de origem inválido para relacionamento, esperava ID ou QUOTED_STRING, pegou {origem_token.type}")
        origem = origem_token.value
        # print(f"DEBUG: Origem consumida: {origem_token}")
        card_origem = None
        
        if self._peek_token() and self._peek_token().type == 'QUOTED_STRING':
            # Verificar se o próximo token é uma seta para não confundir label de associação de classe
            # Esta é uma heurística. Se a string entre aspas for seguida por uma seta, é cardinalidade.
            if self._peek_token(1) and self._peek_token(1).type.startswith('ARROW_'):
                card_origem_token = self._consume_token('QUOTED_STRING')
                card_origem = card_origem_token.value
                # print(f"DEBUG: Card_origem consumido: {card_origem_token}")
            
        seta_token = self._peek_token()
        if not seta_token or not seta_token.type.startswith('ARROW_'):
            self._parse_error(f"Esperada seta de relacionamento, encontrou {seta_token.type if seta_token else 'EOF'}")
        self._consume_token(seta_token.type) 
        # print(f"DEBUG: Seta consumida: {seta_token}")
        
        card_destino = None
        if self._peek_token() and self._peek_token().type == 'QUOTED_STRING':
            card_destino_token = self._consume_token('QUOTED_STRING')
            card_destino = card_destino_token.value
            # print(f"DEBUG: Card_destino consumido: {card_destino_token}")
            
        if not self._peek_token(): self._parse_error("Esperado nome de destino para relacionamento, encontrou EOF.")
        destino_token = self._consume_token()
        # print(f"DEBUG: Tentativa de destino consumida: {destino_token}") 
        if destino_token.type not in ['ID', 'QUOTED_STRING']: 
            self._parse_error(f"Nome de destino inválido para relacionamento, esperava ID ou QUOTED_STRING, pegou {destino_token.type}")
        destino = destino_token.value
        
        label = None
        if self._peek_token() and self._peek_token().type == 'COLON':
            self._consume_token('COLON')
            # print("DEBUG: COLON para label consumido.")
            if self._peek_token() and self._peek_token().type in ['ID', 'QUOTED_STRING']: # Label pode ser ID ou String
                label_token = self._consume_token()
                label = label_token.value
                # print(f"DEBUG: Label consumido: {label_token}")
            # PlantUML permite label vazio após ':', nosso lexer não gera token.
            # Se não for ID ou QUOTED_STRING, assumimos que não há label após ':' ou o lexer não pegou.

        tipo_rel = self._traduzir_seta_para_tipo_relacionamento(seta_token.type, seta_token.value)
        
        # Ajustar origem/destino para herança/implementação com base na direção da seta PlantUML
        if tipo_rel == "heranca" and seta_token.type == 'ARROW_INHERITANCE_RIGHT':
             origem, destino = destino, origem
        elif tipo_rel == "implementacao":
            if seta_token.type == 'ARROW_IMPLEMENTATION_RIGHT_STRONG' or \
               (seta_token.type == 'ARROW_DIRECTED_DEPENDENCY_RIGHT' and ".." in seta_token.value and "|" in seta_token.value): # ..|>
                 origem, destino = destino, origem
            # Para <|.. e <.., a origem já é a interface/pai pela definição do token do lexer

        novo_relacionamento = PlantUMLRelacionamento(
            origem=origem, destino=destino, tipo=tipo_rel, label=label,
            cardinalidade_origem=card_origem, cardinalidade_destino=card_destino
        )
        self.diagrama.adicionar_relacionamento(novo_relacionamento)
        # print(f"DEBUG: Relacionamento ADICIONADO: {novo_relacionamento}")

    def parse(self, plantuml_code: Optional[str] = None) -> PlantUMLDiagrama:
        """
        Executa o processo completo de análise do código PlantUML.
        """
        if plantuml_code:
            lexer.lineno = 1
            lexer.input(plantuml_code)
            self.tokens = []
            while True:
                tok = lexer.token()
                if not tok: break
                self.tokens.append(tok)
        
        self.token_idx = 0
        self.diagrama = PlantUMLDiagrama()
        self.contexto_atual_pilha = []

        while self.token_idx < len(self.tokens):
            token = self._peek_token()
            if not token: break

            if token.type in ['AT_STARTUML', 'AT_ENDUML', 'SKINPARAM_DIRECTIVE']:
                self._consume_token()
                if token.type == 'AT_STARTUML' and self._peek_token() and self._peek_token().type in ['ID', 'QUOTED_STRING']:
                     self._consume_token() 
                elif token.type == 'SKINPARAM_DIRECTIVE' and token.value.startswith("!"): 
                     if self._peek_token() and self._peek_token().type in ['ID', 'QUOTED_STRING']:
                        self._consume_token() 
                continue
            
            if token.type == 'RBRACE': 
                if self.contexto_atual_pilha:
                    self.contexto_atual_pilha.pop()
                self._consume_token()
                continue
            
            contexto_ativo = self._obter_contexto_atual()
            
            # Se estamos dentro de um contexto que espera membros (classe, interface, enum com corpo aberto)
            if contexto_ativo and token.type != 'PACKAGE' and \
               not (token.type in ['ID', 'QUOTED_STRING'] and self._peek_token(1) and self._peek_token(1).type.startswith('ARROW_')) and \
               not (token.type in ['ID', 'QUOTED_STRING'] and self._peek_token(1) and self._peek_token(1).type == 'QUOTED_STRING' and self._peek_token(2) and self._peek_token(2).type.startswith('ARROW_')) : # Se não for início de relacionamento
                if isinstance(contexto_ativo, (PlantUMLClasse, PlantUMLInterface, PlantUMLEnum)):
                    # Se a linha de declaração da estrutura não abriu com LBRACE,
                    # mas estamos no contexto dela, esta linha DEVE ser um membro ou RBRACE.
                    # A chamada a _parse_membros_estrutura é feita quando LBRACE é encontrado.
                    # Aqui, lidamos com membros de linha única ou caso o RBRACE seja o próximo.
                    if token.type in ['VISIBILITY', 'STATIC_MODIFIER', 'ABSTRACT_MODIFIER', 'ID', 'QUOTED_STRING']:
                        self._parse_atributo_ou_metodo(contexto_ativo) # Para classes/interfaces
                        if isinstance(contexto_ativo, PlantUMLEnum) and token.type == 'ID': # Para valores de Enum
                            self._parse_membros_estrutura(contexto_ativo) # Chama para pegar valor de enum
                    else:
                        self._parse_error(f"Token inesperado '{token.value}' ({token.type}) dentro da estrutura '{contexto_ativo.nome}'")
                    continue # Após processar membro ou erro, pular para próximo token

            # Se não estamos em um contexto de membro, ou o token não indica um membro,
            # então deve ser uma declaração de estrutura, pacote, ou relacionamento.
            if token.type == 'PACKAGE':
                self._parse_declaracao_pacote()
            elif token.type in ['ABSTRACT', 'CLASS', 'INTERFACE', 'ENUM']:
                self._parse_declaracao_estrutura()
            elif token.type in ['ID', 'QUOTED_STRING']: # Potencial início de relacionamento
                # Heurística mais forte para relacionamento
                is_relationship_candidate = False
                # ID/QS ["card"] ARROW ...
                if self._peek_token(1) and self._peek_token(1).type.startswith('ARROW_'): is_relationship_candidate = True
                elif self._peek_token(1) and self._peek_token(1).type == 'QUOTED_STRING' and \
                     self._peek_token(2) and self._peek_token(2).type.startswith('ARROW_'):
                    is_relationship_candidate = True
                
                if is_relationship_candidate:
                    self._parse_relacionamento()
                else:
                    self._parse_error(f"Token ID/QUOTED_STRING inesperado ('{token.value}') no escopo principal ou de pacote.")
            else:
                self._parse_error(f"Token desconhecido/inesperado no início da linha: {token.type} ('{token.value}')")
                
        return self.diagrama


if __name__ == '__main__':
    with open("diagramas/exemplo_diagrama.plantuml", "r", encoding="utf-8") as f:
        plantuml_code = f.read()
    parser = PlantUMLParser()
    diagrama_resultante = parser.parse(plantuml_code)

    print("\n--- Diagrama Resultante (Representação) ---")
    print(diagrama_resultante)

    print("\n--- Elementos do Diagrama (e seus conteúdos) ---")
    if not diagrama_resultante.elementos:
        print("Nenhum elemento principal foi parseado.")
    
    def imprimir_estrutura(elemento, indentacao=""):
        print(f"{indentacao}Elemento: {elemento}")
        if isinstance(elemento, (PlantUMLClasse, PlantUMLInterface)):
            if hasattr(elemento, 'is_abstract') and elemento.is_abstract and isinstance(elemento, PlantUMLClasse):
                print(f"{indentacao}  (Classe Abstrata)")
            if isinstance(elemento, PlantUMLClasse) and hasattr(elemento, 'classe_pai') and elemento.classe_pai:
                print(f"{indentacao}  Herda de Classe: {elemento.classe_pai}")
            if isinstance(elemento, PlantUMLClasse) and hasattr(elemento, 'interfaces_implementadas') and elemento.interfaces_implementadas:
                print(f"{indentacao}  Implementa Interface(s): {elemento.interfaces_implementadas}")
            if isinstance(elemento, PlantUMLInterface) and hasattr(elemento, 'interfaces_pai') and elemento.interfaces_pai:
                print(f"{indentacao}  Herda de Interface(s): {elemento.interfaces_pai}")

            if elemento.atributos:
                print(f"{indentacao}  Atributos:")
                for attr in elemento.atributos:
                    print(f"{indentacao}    - {attr}")
            else:
                print(f"{indentacao}  (Sem atributos parseados para esta estrutura)")
            
            if elemento.metodos:
                print(f"{indentacao}  Métodos:")
                for met in elemento.metodos:
                    print(f"{indentacao}    - {met}")
                    if met.parametros:
                        print(f"{indentacao}      Parâmetros do método:")
                        for param in met.parametros:
                            print(f"{indentacao}        * {param}")
            else:
                print(f"{indentacao}  (Sem métodos parseados para esta estrutura)")
        
        elif isinstance(elemento, PlantUMLEnum):
            if hasattr(elemento, 'valores_enum') and elemento.valores_enum:
                print(f"{indentacao}  Valores do Enum:")
                for val in elemento.valores_enum:
                    print(f"{indentacao}    - {val}")
            elif elemento.atributos: 
                print(f"{indentacao}  Valores do Enum (como atributos):")
                for attr in elemento.atributos:
                    print(f"{indentacao}    - {attr.nome}")
            else:
                print(f"{indentacao}  (Sem valores de enum parseados)")
        
        elif isinstance(elemento, PlantUMLPacote):
            print(f"{indentacao}  Conteúdo do Pacote '{elemento.nome}':")
            if not elemento.elementos:
                print(f"{indentacao}    (Pacote Vazio)")
            for sub_elemento in elemento.elementos:
                imprimir_estrutura(sub_elemento, indentacao + "    ")

    for elemento_raiz in diagrama_resultante.elementos:
        print("") 
        imprimir_estrutura(elemento_raiz)
    
    if not diagrama_resultante.relacionamentos:
        print("\nNenhum relacionamento foi parseado.")
    else:
        print("\n--- Relacionamentos do Diagrama ---")
        for rel in diagrama_resultante.relacionamentos:
            print(rel)
    
    print("\n--- Teste Concluído ---")