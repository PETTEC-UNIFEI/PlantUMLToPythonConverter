# CLI do Conversor PlantUML

O arquivo `main_cli.py` é a interface de linha de comando para converter diagramas PlantUML em código Python ou C#.

## Uso

```bash
python back_end/main_cli.py [opções]
```

## Opções

- `--input, -i`: Arquivo PlantUML de entrada (.plantuml ou .puml)
- `--output, -o`: Diretório de saída (padrão: `output_generated_code`)
- `--diagram-name`: Nome do diagrama para a pasta de saída
- `--language, -l`: Linguagem de destino (`python` ou `csharp`, padrão: `python`)
- `--namespace, -n`: Namespace base para C# (padrão: `GeneratedCode`, ignorado para Python)
- `--help, -h`: Mostra ajuda

## Exemplos

### Gerar código Python (padrão)
```bash
python back_end/main_cli.py
python back_end/main_cli.py --language python
```

### Gerar código C#
```bash
python back_end/main_cli.py --language csharp
python back_end/main_cli.py --language csharp --namespace MinhaEmpresa.Sistemas
```

### Especificar arquivo de entrada
```bash
python back_end/main_cli.py --input meu_diagrama.plantuml --language csharp
```

### Especificar nome do projeto
```bash
python back_end/main_cli.py --language csharp --diagram-name SistemaVendas --namespace Vendas.Core
```

## Arquivos de Entrada

Se não for especificado um arquivo de entrada, o sistema tentará usar automaticamente:
- `data/diagramas/exemplo_diagrama.plantuml`
- `data/diagramas/exemplo_diagrama.puml`
- `diagramas/exemplo_diagrama.plantuml`
- `diagramas/exemplo_diagrama.puml`

## Saída

### Python
Gera uma estrutura de pastas Python com:
- Arquivos `.py` para cada classe, enum e interface
- Arquivos `__init__.py` para criar pacotes Python
- Estrutura de diretórios baseada nos pacotes PlantUML

### C#
Gera uma estrutura de projeto C# com:
- Arquivos `.cs` para cada classe, enum e interface
- Arquivo `.csproj` para o projeto
- Estrutura de diretórios baseada nos pacotes PlantUML
- Namespaces organizados hierarquicamente

## Exemplo Completo

```bash
# Gerar projeto C# completo
python back_end/main_cli.py \
  --input data/diagramas/SistemaAcademicoComplexo.plantuml \
  --language csharp \
  --namespace UniversidadeXYZ.Sistemas \
  --diagram-name SistemaAcademico \
  --output projetos_gerados
```

Isso criará um projeto C# em `projetos_gerados/SistemaAcademico/` com namespace base `UniversidadeXYZ.Sistemas`.
