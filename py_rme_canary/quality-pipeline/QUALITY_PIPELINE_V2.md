# Quality Pipeline v2.3 - Documentação

## Visão Geral

O Quality Pipeline v2.3 é uma solução completa de análise de código para **projetos locais**, integrando múltiplas ferramentas de análise estática, segurança, detecção de segredos, código morto/duplicado, documentação, testes e **automação de UI/UX** com testes visuais.

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
| **Complexipy** | Cognitive complexity (legibilidade) | `pip install complexipy` |
| **Lizard** | Complexidade ciclomática multi-linguagem | `pip install lizard` |

#### Fase 3: Análise Complementar (Dead Code, Duplication, Quality)
| Ferramenta | Propósito | Instalação |
|------------|-----------|------------|
| **Pylint** | Análise complementar (naming, dead code) | `pip install pylint` |
| **Prospector** | Agregador de linters | `pip install prospector` |
| **Vulture** | Detecção de código morto | `pip install vulture` |
| **Skylos** | Código morto + segurança + qualidade | `pip install skylos` |
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

#### Fase 5: Documentação e Testes
| Ferramenta | Propósito | Instalação |
|------------|-----------|------------|
| **Interrogate** | Cobertura de docstrings | `pip install interrogate` |
| **Pydocstyle** | Conformidade PEP 257 (docstrings) | `pip install pydocstyle` |
| **Mutmut** | Mutation testing (qualidade de testes) | `pip install mutmut` |

#### Fase 6: UI/UX Automation ✨ NEW
| Ferramenta | Propósito | Instalação |
|------------|-----------|------------|
| **PyAutoGUI** | Automação de mouse/teclado/screenshots | `pip install pyautogui` |
| **Pywinauto** | Automação de GUI Windows | `pip install pywinauto` (Windows) |
| **Lighthouse** | Auditorias de qualidade web (Performance, Accessibility, SEO) | `npm install -g lighthouse` |
| **Percy** | Testes de regressão visual | `npm install -g @percy/cli` |
| **Applitools** | Validação visual com IA | `pip install eyes-selenium` |

## Instalação

### Dependências Obrigatórias

```bash
pip install ruff mypy radon bandit safety pylint
```

### Ferramentas Adicionais Recomendadas

```bash
# Análise de complexidade
pip install complexipy lizard pyright

# Análise complementar
pip install vulture skylos prospector

# Documentação
pip install interrogate pydocstyle

# Testes
pip install mutmut pytest-randomly pytest-xdist

# Segurança avançada
pip install detect-secrets semgrep pip-audit

# UI/UX Automation
pip install pyautogui pillow opencv-python
pip install pywinauto  # Windows only
pip install eyes-selenium  # Applitools
npm install -g lighthouse @percy/cli

# Secret scanning alternativo
brew install gitleaks  # macOS
# ou: go install github.com/gitleaks/gitleaks/v8@latest

# Vulnerabilidades multi-ecossistema
go install github.com/google/osv-scanner/cmd/osv-scanner@latest

# Código duplicado
npm install -g jscpd
```

### PyAutoGUI (UI Automation)

```bash
# Instalação
pip install pyautogui pillow

# Usar em testes (exemplo)
import pyautogui

# Capturar screenshot
screenshot = pyautogui.screenshot()
screenshot.save('screenshot.png')

# Localizar imagem na tela
button_location = pyautogui.locateOnScreen('button.png')
if button_location:
    pyautogui.click(button_location)
```

### Lighthouse (Web Quality Audits)

```bash
# Instalação
npm install -g lighthouse

# Executar auditoria
lighthouse http://localhost:8000 \
    --output json \
    --output html \
    --chrome-flags="--headless"

# Variável de ambiente (opcional)
export LIGHTHOUSE_URL=http://localhost:8000
```

### Percy (Visual Regression Testing)

```bash
# Instalação
npm install -g @percy/cli
pip install percy-selenium  # ou percy-playwright

# Configurar token
export PERCY_TOKEN=your_token_here

# Executar com testes
percy exec -- pytest tests/visual/
```

### Applitools (AI Visual Validation)

```bash
# Instalação
pip install eyes-selenium

# Configurar API key
export APPLITOOLS_API_KEY=your_key_here

# Exemplo de uso
from applitools.selenium import Eyes, Target

eyes = Eyes()
eyes.api_key = os.getenv('APPLITOOLS_API_KEY')
eyes.check_window("Main Page")
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

### Skylos (Código Morto + Segurança)

```bash
# Instalação
pip install skylos

# Inicializar configuração
skylos init  # Adiciona [tool.skylos] no pyproject.toml

# Executar análise com trace (reduz falsos positivos)
skylos . --trace
```

### Mutmut (Mutation Testing)

```bash
# Instalação
pip install mutmut

# Executar mutation testing (computacionalmente intensivo)
mutmut run --paths-to-mutate=py_rme_canary

# Ver resultados
mutmut results

# Gerar relatório HTML
mutmut html
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

### v2.3 (2026-01-30)
- ✅ Adicionado: PyAutoGUI para automação de UI (mouse, teclado, screenshots)
- ✅ Adicionado: Pywinauto para automação de GUI Windows
- ✅ Adicionado: Lighthouse para auditorias web (Performance, Accessibility, SEO, PWA)
- ✅ Adicionado: Percy para testes de regressão visual
- ✅ Adicionado: Applitools para validação visual com IA
- ✅ Nova Fase 6: UI/UX Automation (5 ferramentas)
- ✅ Adicionado: Flag `--skip-ui-tests` para pular testes de UI/UX
- ✅ Reorganizado: Consolidação agora é Fase 7
- ✅ Total: 26 ferramentas, 7 fases

### v2.2 (2026-01-30)
- ✅ Adicionado: Complexipy para cognitive complexity (legibilidade)
- ✅ Adicionado: Skylos para código morto + segurança com taint analysis
- ✅ Adicionado: Lizard para complexidade ciclomática multi-linguagem
- ✅ Adicionado: Interrogate para cobertura de docstrings
- ✅ Adicionado: Pydocstyle para conformidade PEP 257 (docstrings)
- ✅ Adicionado: Mutmut para mutation testing (qualidade de testes)
- ✅ Adicionado: Prospector como agregador de linters
- ✅ Nova Fase 5: Documentação e Testes (Interrogate, Pydocstyle, Mutmut)
- ✅ Reorganizado: Fase 3 inclui Prospector e Skylos
- ✅ Reorganizado: Consolidação agora é Fase 6

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
