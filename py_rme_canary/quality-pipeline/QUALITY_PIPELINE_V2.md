# Quality Pipeline v2.0 - Documentação

## Visão Geral

O Quality Pipeline v2.0 é uma solução de análise de código para **projetos locais**, sem dependência de SonarQube Server. Ele integra múltiplas ferramentas de análise estática, segurança e qualidade de código.

## Decisões de Arquitetura

### ❌ SonarQube Server - NÃO Utilizado

**Motivo**: O projeto é desenvolvido localmente e o SonarQube Server:
- Requer infraestrutura de servidor
- Certas vulnerabilidades só são detectadas no servidor (não no CLI)
- Complexidade desnecessária para desenvolvimento local

**Alternativa**: SonarLint CLI para análise local.

### ✅ Ferramentas Utilizadas

| Ferramenta | Propósito | Instalação |
|------------|-----------|------------|
| **Ruff** | Linter + Formatter (substitui flake8, black, isort) | `pip install ruff` |
| **Mypy** | Type checking estático | `pip install mypy` |
| **Radon** | Métricas de complexidade ciclomática | `pip install radon` |
| **Bandit** | Análise de segurança Python | `pip install bandit` |
| **Safety** | Vulnerabilidades em dependências | `pip install safety` |
| **Pylint** | Análise complementar (naming, dead code) | `pip install pylint` |
| **SonarLint CLI** | Análise local de segurança | Ver instalação abaixo |
| **ast-grep** | Análise estrutural e rewrites | `cargo install ast-grep` |

## Instalação

### Dependências Obrigatórias

```bash
pip install ruff mypy radon bandit safety pylint
```

### SonarLint CLI (Opcional)

O SonarLint CLI permite análise local sem servidor. **Nota**: Esta não é uma solução oficialmente suportada pela SonarSource.

#### Opção 1: sonarlint-ls-cli (Python)

```bash
pip install sonarlint-ls-cli
```

#### Opção 2: Docker

```bash
docker pull sonarsource/sonarlint-cli
docker run --rm -v $(pwd):/src sonarsource/sonarlint-cli
```

#### Opção 3: Java CLI

Requer Java 11+:

```bash
# Download do JAR
curl -LO https://repo1.maven.org/maven2/org/sonarsource/sonarlint/core/sonarlint-cli/...

# Executar
java -jar sonarlint-cli.jar --src py_rme_canary
```

### Pre-commit

```bash
pip install pre-commit
pre-commit install
```

## Uso

### Modo Dry-Run (Apenas Análise)

```bash
./quality_lf.sh --dry-run --verbose
```

### Modo Apply (Aplica Correções)

```bash
./quality_lf.sh --apply --skip-tests
```

### Opções Disponíveis

| Flag | Descrição |
|------|-----------|
| `--apply` | Aplica correções automáticas |
| `--dry-run` | Apenas analisa (padrão) |
| `--skip-tests` | Pula execução de testes |
| `--skip-security` | Pula Bandit e Safety |
| `--skip-sonarlint` | Pula SonarLint CLI |
| `--skip-libcst` | Pula transformações LibCST |
| `--verbose` | Saída detalhada |

## Fases do Pipeline

### Fase 1: Baseline
- Indexação de símbolos
- Ruff (linting)
- Mypy (type checking)
- Radon (complexidade)

### Fase 2: Refatoração (se --apply)
- ast-grep transformações
- LibCST transformações
- Re-execução de Ruff e Mypy
- Testes automatizados

### Fase 3: Análise Complementar
- Pylint (regras adicionais)

### Fase 4: Segurança
- Bandit (vulnerabilidades no código)
- Safety (vulnerabilidades em dependências)
- SonarLint CLI (análise local)

### Fase 5: Consolidação
- Normalização de issues
- Comparação de símbolos
- Relatório final

## Pre-commit Hooks

O pipeline configura automaticamente o `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy

  - repo: https://github.com/PyCQA/bandit
    hooks:
      - id: bandit

  - repo: local
    hooks:
      - id: radon-cc
        name: Radon Cyclomatic Complexity
```

## Relatórios Gerados

Todos os relatórios são salvos em `.quality_reports/`:

| Arquivo | Conteúdo |
|---------|----------|
| `refactor_summary.md` | Relatório consolidado |
| `bandit.json` | Vulnerabilidades de segurança |
| `safety.json` | Vulnerabilidades em dependências |
| `pylint.json` | Issues do Pylint |
| `sonarlint.json` | Issues do SonarLint |
| `symbols_*.json` | Índice de símbolos |
| `quality_*.log` | Log de execução |

## Ferramentas Complementares (Futuro)

### OSV-Scanner

Para verificar vulnerabilidades conhecidas:

```bash
# Instalação
go install github.com/google/osv-scanner/cmd/osv-scanner@latest

# Uso
osv-scanner --lockfile requirements.txt
```

### Pyright

Para análise estática avançada:

```bash
pip install pyright
pyright py_rme_canary
```

### Dependabot

Configure no repositório GitHub para alertas de segurança automáticos.

## Limitações Conhecidas

1. **SonarLint CLI**: Não oficialmente suportado pela SonarSource. Use com cautela.
2. **Vulnerabilidades avançadas**: Algumas só são detectadas pelo SonarQube Server.
3. **Cache de hashes**: Depende de scripts auxiliares em `tools/quality_scripts/`.

## Troubleshooting

### Erro: "Dependência ausente"

```bash
pip install ruff mypy radon bandit safety pylint
```

### Erro: "SonarLint não disponível"

O SonarLint CLI é opcional. Use `--skip-sonarlint` para pular.

### Erro: "CRLF no script"

```bash
# Converter para LF
sed -i 's/\r$//' quality_lf.sh
```

## Changelog

### v2.0 (2026-01-30)
- ❌ Removido: SonarQube Server (não adequado para projeto local)
- ✅ Adicionado: SonarLint CLI local
- ✅ Adicionado: Safety para vulnerabilidades em dependências
- ✅ Adicionado: Pylint para análise complementar
- ✅ Adicionado: Configuração automática de pre-commit
- ✅ Melhorado: Tratamento de erros e fallbacks
- ✅ Melhorado: Documentação e mensagens de ajuda
