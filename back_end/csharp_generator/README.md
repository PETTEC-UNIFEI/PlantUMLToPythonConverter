# Gerador de Código C#

Este módulo é responsável por gerar código C# a partir de diagramas PlantUML parseados.

## Estrutura do Módulo

```
csharp_generator/
├── __init__.py                 # Inicialização do módulo
├── main_generator.py          # Orquestrador principal
├── type_mapper.py             # Mapeamento de tipos PlantUML → C#
├── using_manager.py           # Gerenciamento de using statements
└── structure_generators/      # Geradores específicos por estrutura
    ├── __init__.py
    ├── class_generator.py     # Geração de classes
    ├── enum_generator.py      # Geração de enums
    └── interface_generator.py # Geração de interfaces
```

## Funcionalidades Implementadas

### ClassGenerator (`class_generator.py`)

Gera classes C# completas a partir de estruturas `PlantUMLClasse`, incluindo:

- **Propriedades estáticas** com inicialização adequada
- **Propriedades de instância** com getters/setters automáticos
- **Construtores** com:
  - Parâmetros obrigatórios e opcionais
  - Chamadas ao construtor base (`: base(...)`)
  - Inicialização de propriedades
- **Métodos** com:
  - Modificadores de visibilidade (public, private, protected, internal)
  - Métodos estáticos e abstratos
  - Parâmetros tipados
  - Tipos de retorno apropriados
  - Implementação padrão com `NotImplementedException`

#### Conversões de Nomenclatura

- **Propriedades**: Convertidas para PascalCase (ex: `nome` → `Nome`)
- **Parâmetros**: Convertidos para camelCase (ex: `nome` → `nome`)
- **Métodos**: Convertidos para PascalCase (ex: `obterNome` → `ObterNome`)

#### Mapeamento de Visibilidade

| PlantUML | C# |
|----------|-----|
| `+` | `public` |
| `-` | `private` |
| `#` | `protected` |
| `~` | `internal` |

### EnumGenerator (`enum_generator.py`)

Gera enumerações C# a partir de estruturas `PlantUMLEnum`, incluindo:

- **Valores simples** (C# atribui números automaticamente)
- **Valores com números explícitos** (ex: `CONCLUIDO = 5`)
- **Detecção automática do tipo subjacente** baseado nos valores:
  - `byte` para valores 0-255
  - `short` para valores -32,768 a 32,767
  - `int` para valores maiores (padrão)
  - `long` para valores muito grandes
- **Conversão de nomenclatura** para PascalCase
- **Sanitização de nomes** (remove acentos e caracteres especiais)

#### Exemplo de Enum Gerado
```csharp
public enum StatusPedido : byte
{
    Pendente,
    Processando,
    Concluido = 5,
    Cancelado
}
```

### InterfaceGenerator (`interface_generator.py`)

Gera interfaces C# a partir de estruturas `PlantUMLInterface`, incluindo:

- **Propriedades de instância** com get/set automáticos
- **Propriedades estáticas** (C# 8.0+) com:
  - Implementação padrão para valores constantes
  - Declaração abstrata para propriedades que devem ser implementadas
- **Métodos de instância** (apenas assinatura, sem implementação)
- **Métodos estáticos** (C# 8.0+) com implementação padrão
- **Herança de interfaces** (`: IInterfacePai`)
- **Conversão de nomenclatura** para PascalCase

#### Exemplo de Interface Gerada
```csharp
public interface IProcessador : IDisposable
{
    static int TimeoutPadrao { get; } = 30;
    
    string Versao { get; set; }
    
    bool Processar(string dados);
    
    static Dictionary<string, object> ObterConfiguracaoPadrao()
    {
        throw new NotImplementedException();
    }
}
```

### TypeMapper (`type_mapper.py`)

Mapeia tipos PlantUML para tipos C# equivalentes:

#### Tipos Primitivos
- `String`, `str` → `string`
- `int`, `Integer` → `int`
- `float`, `Float` → `float`
- `double`, `Double` → `double`
- `bool`, `Boolean` → `bool`
- `Date`, `DateTime` → `DateTime`

#### Tipos Genéricos
- `List<T>` → `List<T>`
- `Map<K,V>`, `Dictionary<K,V>` → `Dictionary<K,V>`
- `Set<T>` → `HashSet<T>`

#### Using Statements Automáticos
Detecta automaticamente quando tipos precisam de using statements:
- `DateTime` → `using System;`
- `List<T>` → `using System.Collections.Generic;`

### UsingManager (`using_manager.py`)

Gerencia using statements de forma inteligente:

- **Coleta automática**: Analisa todas as estruturas e detecta using statements necessários
- **Deduplicação**: Remove duplicatas e using statements desnecessários
- **Formatação**: Ordena alfabeticamente e formata corretamente
- **Namespace relativo**: Evita using statements para o próprio namespace

### MainCodeGenerator (`main_generator.py`)

Orquestrador principal que:

- **Cria estrutura de diretórios** baseada em pacotes PlantUML
- **Gera arquivos .cs** individuais para cada estrutura
- **Calcula namespaces** automaticamente baseados na hierarquia de pacotes
- **Cria arquivo .csproj** básico para o projeto
- **Mantém manifesto** de arquivos gerados

## Exemplo de Uso

```python
from back_end.plantuml_parser.data_structures import PlantUMLClasse, PlantUMLAtributo
from back_end.csharp_generator.structure_generators.class_generator import ClassGenerator
from back_end.csharp_generator.type_mapper import TypeMapper
from back_end.csharp_generator.using_manager import UsingManager

# Cria uma classe de exemplo
classe = PlantUMLClasse(
    nome="Pessoa",
    atributos=[
        PlantUMLAtributo(nome="nome", tipo="String", visibilidade="+"),
        PlantUMLAtributo(nome="idade", tipo="int", visibilidade="+")
    ]
)

# Configura geradores
type_mapper = TypeMapper()
using_manager = UsingManager()
namespace = "MinhaAplicacao.Modelos"

# Gera código
generator = ClassGenerator(classe, type_mapper, using_manager, namespace)
code_lines = generator.generate_code_lines()

# Resultado será algo como:
# public string Nome { get; set; }
# public int Idade { get; set; }
# 
# public Pessoa(string nome, int idade)
# {
#     Nome = nome;
#     Idade = idade;
# }
```

## Código Gerado - Características

### Estrutura de Arquivo C#

```csharp
using System;
using System.Collections.Generic;

namespace MinhaAplicacao.Modelos
{
    public class MinhaClasse : ClassePai, IMinhaInterface
    {
        // Propriedades estáticas
        public static int Contador { get; set; } = 0;
        
        // Propriedades de instância
        public string Nome { get; set; }
        public int Idade { get; set; }
        
        // Construtor
        public MinhaClasse(string nome, int idade) : base()
        {
            Nome = nome;
            Idade = idade;
        }
        
        // Métodos
        public void MeuMetodo(string parametro)
        {
            throw new NotImplementedException();
        }
    }
}
```

#### Enum Completo

```csharp
using System;

namespace MinhaAplicacao.Enums
{
    public enum StatusPedido : byte
    {
        Pendente,
        Processando,
        Concluido = 5,
        Cancelado
    }
}
```

#### Interface Completa

```csharp
using System;
using System.Collections.Generic;

namespace MinhaAplicacao.Interfaces
{
    public interface IProcessador : IDisposable
    {
        static int TimeoutPadrao { get; } = 30;
        
        string Versao { get; set; }
        
        bool Processar(string dados);
        
        static Dictionary<string, object> ObterConfiguracaoPadrao()
        {
            throw new NotImplementedException();
        }
    }
}
```

### Características do Código

- **Compatível com .NET 8.0**
- **Nullable reference types habilitados**
- **Convenções C# padrão**
- **Properties auto-implementadas**
- **Construtores com parâmetros opcionais**
- **Herança e implementação de interfaces**
- **Métodos com implementação padrão**
- **Enums com tipos subjacentes otimizados**
- **Interfaces com recursos modernos do C# 8.0+**
