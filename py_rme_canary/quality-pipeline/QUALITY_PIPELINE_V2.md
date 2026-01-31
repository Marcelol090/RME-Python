# Quality Pipeline v2.1 - Documentação

## Visão Geral

O Quality Pipeline v2.1 é uma solução completa de análise de código para **projetos locais**, integrando múltiplas ferramentas de análise estática, segurança, detecção de segredos, código morto/duplicado e vulnerabilidades em dependências.

## Decisões de Arquitetura

### ❌ SonarQube Server - NÃO Utilizado

**Motivo**: O projeto é desenvolvido localmente e o SonarQube Server:
- Requer infraestrutura de servidor
- Certas vulnerabilidades só são detectadas no servidor (não no CLI)
- Complexidade desnecessária para desenvolvimento local

**Alternativa**: SonarLint CLI + Semgrep + Bandit para análise local.

### ✅ Ferramentas Utilizadas

#### Fase 1: Baseline (Linting, Types, Complexity)
| Ferramenta | Propósito | Instalação |
|------------|-----------|------------|
| **Ruff** | Linter + Formatter (substitui flake8, black, isort) | `pip install ruff` |
| **Mypy** | Type checking estático | `pip install mypy` |
| **Radon** | Métricas de complexidade ciclomática | `pip install radon` |
| **Pyright** | Type checking avançado (complementar) | `pip install pyright` |

#### Fase 3: Análise Complementar (Dead Code, Duplication)
| Ferramenta | Propósito | Instalação |
|------------|-----------|------------|
| **Pylint** | Análise complementar (naming, dead code) | `pip install pylint` |
| **Vulture** | Detecção de código morto | `pip install vulture` |
| **jscpd** | Detecção de código duplicado | `npm install -g jscpd` |

#### Fase 4: Segurança (Multi-layer)
| Ferramenta | Propósito | Instalação |
|------------|-----------|------------|
| **detect-secrets** | Secret scanning (pre-commit) | `pip install detect-secrets` |
| **Gitleaks** | Secret scanning (alternativa) | `brew install gitleaks` |
| **Bandit** | Análise de segurança Python | `pip install bandit` |
| **Semgrep** | Análise de padrões (Django/Flask/FastAPI) | `pip install semgrep` |
| **SonarLint CLI** | Análise local de segurança | `pip install sonarlint-ls-cli` |
| **Safety** | Vulnerabilidades em dependências (pyup.io) | `pip install safety` |
| **pip-audit** | Vulnerabilidades (PyPI Advisory + OSV) | `pip install pip-audit` |
| **OSV-Scanner** | Vulnerabilidades multi-ecossistema | `go install github.com/google/osv-scanner/cmd/osv-scanner@latest` |

## Instalação

### Dependências Obrigatórias

```bash
pip install ruff mypy radon bandit safety pylint
```

### Ferramentas Adicionais Recomendadas

```bash
# Análise complementar
pip install vulture pyright

# Segurança avançada
pip install detect-secrets semgrep pip-audit

# Secret scanning alternativo
brew install gitleaks  # macOS
# ou: go install github.com/gitleaks/gitleaks/v8@latest

# Vulnerabilidades multi-ecossistema
go install github.com/google/osv-scanner/cmd/osv-scanner@latest

# Código duplicado
npm install -g jscpd
```

### detect-secrets (Secret Scanning)

```bash
# Instalação
pip install detect-secrets

# Criar baseline (ignorar segredos existentes já verificados)
detect-secrets scan > .secrets.baseline

# Auditar segredos detectados
detect-secrets audit .secrets.baseline
```

### Semgrep (Análise de Padrões)

```bash
# Instalação
pip install semgrep

# Executar com regras automáticas
semgrep scan --config auto py_rme_canary

# Criar regras customizadas em tools/semgrep_rules/
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
| `--skip-security` | Pula Bandit, Semgrep, pip-audit, OSV-Scanner |
| `--skip-sonarlint` | Pula SonarLint CLI |
| `--skip-secrets` | Pula detect-secrets e gitleaks |
| `--skip-deadcode` | Pula Vulture e jscpd |
| `--skip-libcst` | Pula transformações LibCST |
| `--verbose` | Saída detalhada |

## Fases do Pipeline

### Fase 1: Baseline (Linting, Types, Complexity)
- Indexação de símbolos
- Ruff (linting + formatting)
- Mypy (type checking)
- Radon (complexidade ciclomática)
- Pyright (type checking avançado)

### Fase 2: Refatoração (se --apply)
- ast-grep transformações
- LibCST transformações
- Re-execução de Ruff e Mypy
- Testes automatizados

### Fase 3: Análise Complementar (Dead Code, Duplication)
- Pylint (regras adicionais, naming conventions)
- Vulture (código morto não capturado por Radon)
- jscpd (código duplicado)

### Fase 4: Segurança (Multi-layer)
- **4.1 Secret Scanning**: detect-secrets ou gitleaks
- **4.2 Code Security**: Bandit, Semgrep, SonarLint
- **4.3 Dependencies**: Safety, pip-audit, OSV-Scanner

### Fase 5: Consolidação
- Normalização de issues
- Comparação de símbolos
- Relatório final

## Pre-commit Hooks

O pipeline configura automaticamente o `.pre-commit-config.yaml` com detect-secrets e outras ferramentas:

```yaml
repos:
  # Linting e Formatação
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  # Type Checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  # Segurança
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.8
    hooks:
      - id: bandit
        args: [-r, py_rme_canary, -x, tests]

  # Secret Scanning (RECOMENDADO)
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

  # Hooks básicos
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  # Complexidade
  - repo: local
    hooks:
      - id: radon-cc
        name: Radon Cyclomatic Complexity
        entry: bash -c 'radon cc py_rme_canary --min D --show-complexity'
        language: system
        pass_filenames: false
```

## Relatórios Gerados

Todos os relatórios são salvos em `.quality_reports/`:

| Arquivo | Conteúdo |
|---------|----------|
| `refactor_summary.md` | Relatório consolidado |
| `bandit.json` | Vulnerabilidades de segurança (código) |
| `semgrep.json` | Padrões problemáticos (framework-specific) |
| `secrets.json` | Segredos detectados |
| `safety.json` | Vulnerabilidades em dependências (pyup.io) |
| `pip_audit.json` | Vulnerabilidades em dependências (PyPI/OSV) |
| `osv_scanner.json` | Vulnerabilidades multi-ecossistema |
| `vulture.txt` | Código morto detectado |
| `jscpd.json` | Código duplicado |
| `pylint.json` | Issues do Pylint |
| `pyright.json` | Type checking avançado |
| `sonarlint.json` | Issues do SonarLint |
| `symbols_*.json` | Índice de símbolos |
| `quality_*.log` | Log de execução |

## Comparação de Ferramentas de Dependências

| Ferramenta | Banco de Dados | Auto-fix | SBOM | Multi-ecossistema |
|------------|---------------|----------|------|-------------------|
| **Safety** | pyup.io | ❌ | ❌ | ❌ |
| **pip-audit** | PyPI Advisory + OSV | ✅ | ✅ | ❌ |
| **OSV-Scanner** | OSV.dev | ❌ | ✅ | ✅ |

**Recomendação**: Use pip-audit como principal (suporta auto-fix) e OSV-Scanner para cobertura adicional.

## Comparação de Ferramentas de Secret Scanning

| Ferramenta | Plugins | Baseline | Validação | Enterprise |
|------------|---------|----------|-----------|------------|
| **detect-secrets** | ✅ Extensível | ✅ | ❌ | ❌ |
| **Gitleaks** | ✅ Regex | ❌ | ❌ | ❌ |
| **TruffleHog** | ✅ | ✅ | ✅ (verificação real) | ✅ |

**Recomendação**: Use detect-secrets para pre-commit. TruffleHog para monitoramento contínuo (enterprise).

## Regras Customizadas Semgrep

Crie regras em `tools/semgrep_rules/` para detectar padrões específicos do projeto:

```yaml
# tools/semgrep_rules/custom.yaml
rules:
  - id: no-hardcoded-tibia-version
    pattern: version = "$X"
    message: "Avoid hardcoded Tibia version, use config"
    languages: [python]
    severity: WARNING

  - id: use-type-hints
    pattern-either:
      - pattern: def $FUNC(...): ...
    pattern-not:
      - pattern: def $FUNC(...) -> $RET: ...
    message: "Add return type hint"
    languages: [python]
    severity: INFO
```

## Vulture Whitelist

Para ignorar falsos positivos do Vulture, crie `.vulture_whitelist.py`:

```python
# Falsos positivos conhecidos
from py_rme_canary.vis_layer.ui.main_window import MainWindow
MainWindow.closeEvent  # Qt override
MainWindow.keyPressEvent  # Qt override

# Entry points não detectados
from py_rme_canary.__main__ import main
main
```

## Dependabot

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

### v2.1 (2026-01-30)
- ✅ Adicionado: Pyright para type checking avançado (complementa Mypy)
- ✅ Adicionado: detect-secrets para scanning de segredos
- ✅ Adicionado: Gitleaks como fallback para secrets
- ✅ Adicionado: Semgrep para análise de padrões (Django, Flask, FastAPI)
- ✅ Adicionado: Vulture para detecção de código morto
- ✅ Adicionado: jscpd para detecção de código duplicado
- ✅ Adicionado: pip-audit para vulnerabilidades PyPI/OSV com auto-fix
- ✅ Adicionado: OSV-Scanner para vulnerabilidades multi-ecossistema
- ✅ Adicionado: Flag `--skip-secrets` para pular scanning de segredos
- ✅ Adicionado: Flag `--skip-deadcode` para pular análise de código morto
- ✅ Reorganizado: Fase 4 em subfases (4.1 Secrets, 4.2 Code Security, 4.3 Dependencies)

### v2.0 (2026-01-30)
- ❌ Removido: SonarQube Server (não adequado para projeto local)
- ✅ Adicionado: SonarLint CLI local
- ✅ Adicionado: Safety para vulnerabilidades em dependências
- ✅ Adicionado: Pylint para análise complementar
- ✅ Adicionado: Configuração automática de pre-commit
- ✅ Melhorado: Tratamento de erros e fallbacks
- ✅ Melhorado: Documentação e mensagens de ajuda
