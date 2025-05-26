"""
Módulo Lexer para o PlantUML Parser.
"""
import ply.lex as lex

tokens = (
    'AT_STARTUML', 'AT_ENDUML',
    'PACKAGE', 'CLASS', 'ABSTRACT', 'INTERFACE', 'ENUM',
    'EXTENDS', 'IMPLEMENTS',
    'ID',
    'QUOTED_STRING',
    'LBRACE', 'RBRACE', 
    'LPAREN', 'RPAREN', 
    'COLON', 'COMMA', 'EQUALS',
    'LINE_COMMENT',
    'SKINPARAM_DIRECTIVE', 
    'STATIC_MODIFIER', 
    'ABSTRACT_MODIFIER',
    'ARROW_INHERITANCE_LEFT',
    'ARROW_INHERITANCE_RIGHT',
    'ARROW_IMPLEMENTATION_LEFT_STRONG',
    'ARROW_IMPLEMENTATION_RIGHT_STRONG',
    'ARROW_COMPOSITION_LEFT',
    'ARROW_COMPOSITION_RIGHT',
    'ARROW_AGGREGATION_LEFT',
    'ARROW_AGGREGATION_RIGHT',
    'ARROW_DIRECTED_ASSOCIATION_RIGHT',
    'ARROW_DIRECTED_ASSOCIATION_LEFT',
    'ARROW_DIRECTED_DEPENDENCY_RIGHT',
    'ARROW_DIRECTED_DEPENDENCY_LEFT',
    'ARROW_ASSOCIATION_LINE',
    'ARROW_DEPENDENCY_LINE',
    'VISIBILITY',
)

t_ignore = ' \t'

# --- FUNÇÕES DE TOKENS ---

def t_AT_STARTUML(t):
    r'@startuml'
    return t

def t_AT_ENDUML(t):
    r'@enduml'
    return t

def t_PACKAGE(t):
    r'package'
    return t

def t_ABSTRACT(t):
    r'abstract'
    return t

def t_CLASS(t):
    r'class'
    return t

def t_INTERFACE(t):
    r'interface'
    return t

def t_ENUM(t):
    r'enum'
    return t

def t_EXTENDS(t):
    r'extends'
    return t

def t_IMPLEMENTS(t):
    r'implements'
    return t

def t_SKINPARAM_DIRECTIVE(t):
    r'(!\w+|hide\s+\w+|skinparam\s+[\w.]+\s+[\w#]+)'
    return t

def t_LINE_COMMENT(t):
    r"'.*"
    pass

def t_STATIC_MODIFIER(t):
    r'\{(static|classifier)\}'
    t.value = t.value[1:-1]
    return t

def t_ABSTRACT_MODIFIER(t):
    r'\{abstract\}'
    t.value = t.value[1:-1]
    return t

def t_ARROW_INHERITANCE_LEFT(t):
    r'<\|--'
    return t

def t_ARROW_INHERITANCE_RIGHT(t):
    r'--\|>'
    return t

def t_ARROW_IMPLEMENTATION_LEFT_STRONG(t):
    r'<\|\.\.'
    return t

def t_ARROW_IMPLEMENTATION_RIGHT_STRONG(t):
    r'\.\.\|>'
    return t
    
def t_ARROW_COMPOSITION_LEFT(t):
    r'\*--'
    return t

def t_ARROW_COMPOSITION_RIGHT(t):
    r'--\*'
    return t

def t_ARROW_AGGREGATION_LEFT(t):
    r'o--'
    return t

def t_ARROW_AGGREGATION_RIGHT(t):
    r'--o'
    return t

def t_ARROW_DIRECTED_ASSOCIATION_RIGHT(t):
    r'-->'
    return t

def t_ARROW_DIRECTED_ASSOCIATION_LEFT(t):
    r'<--'
    return t

def t_ARROW_DIRECTED_DEPENDENCY_RIGHT(t):
    r'\.\.>'
    return t
    
def t_ARROW_DIRECTED_DEPENDENCY_LEFT(t):
    r'<\.\.'
    return t

def t_ARROW_ASSOCIATION_LINE(t):
    r'--'
    return t

def t_ARROW_DEPENDENCY_LINE(t):
    r'\.\.'
    return t

def t_VISIBILITY(t):
    r'[+\#~-]'
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9<>]*'
    return t

def t_QUOTED_STRING(t):
    r'\"([^\\\"]|(\\.))*\"'
    t.value = str(t.value[1:-1])
    return t

t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COLON = r':'
t_COMMA = r','
t_EQUALS = r'='

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Lexer: Caractere ilegal '{t.value[0]}' na linha {t.lexer.lineno} posicao {t.lexpos}")
    t.lexer.skip(1)

lexer = lex.lex()

PLANTUML_EXEMPLO_TESTE_LEXER = """
@startuml TestLexerLexerV4
' Teste de lexer
package "Meu Pacote" {
    abstract class "Classe Abstrata" {
        + {static} atributoEstatico: String
        - {abstract} metodoAbstrato(): TipoRetorno
    }
}
ClasseA --|> ClasseB : heranca_label
ClasseC *-- ClasseD : composicao_label
ClasseE o-- ClasseF : agregacao_label
ClasseG ..> ClasseH : depende_label
ClasseX -- ClasseY : associacao_normal
ClasseM <.. ClasseN : dep_esquerda_label
ClasseP <|.. ClasseQ : impl_esquerda_label
@enduml
"""

if __name__ == '__main__':
    lexer.input(PLANTUML_EXEMPLO_TESTE_LEXER)
    print("--- Testando Lexer Isoladamente (REGRAS DE SETA COMO FUNÇÕES E REORDENADAS) ---")
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(tok)
    print("--- Fim Teste Lexer ---")