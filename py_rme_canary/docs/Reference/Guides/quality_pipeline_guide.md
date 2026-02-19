# Guia do Pipeline de Qualidade - py_rme_canary

## Visão Geral

Este pipeline automatizado integra as melhores ferramentas de análise estática e refatoração para Python, seguindo as práticas de "Agentic Scripting" de 2025/2026.

### Ferramentas Integradas

| Ferramenta | Propósito | Saída |
|-----------|-----------|-------|
| **Ruff** | Linter ultrarrápido + formatter | `.ruff.json` |
| **Mypy** | Type checking estrito | `.mypy_*.log` |
| **Radon** | Métricas de complexidade | `.radon*.json` |
| **ast-grep** | Análise estrutural via AST | `astgrep_results.json` |
| **LibCST** | Transformações complexas | Modificações in-place |
| **Bandit** | Análise de segurança (SAST) | `bandit.json` |
| **SonarQube** | Análise de segurança | Dashboard web |
| **pytest** | Testes automatizados | `pytest_*.log` |

---

## Instalação

### 1. Dependências do Sistema

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip git shellcheck jq

# macOS
brew install python git shellcheck jq

# Rust (para ast-grep)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### 2. Ferramentas Python

```bash
pip install ruff mypy radon pytest pytest-cov pytest-qt libcst
# Segurança
pip install bandit
```

### 3. ast-grep

```bash
cargo install ast-grep --locked
```

### 4. SonarQube (Opcional)

**Docker (recomendado para dev):**
```bash
docker run -d --name sonarqube -p 9000:9000 sonarqube:community
```

**Scanner CLI:**
```bash
# Ubuntu/Debian
wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip
unzip sonar-scanner-cli-5.0.1.3006-linux.zip
export PATH="$PATH:$PWD/sonar-scanner-5.0.1.3006-linux/bin"
```

---

## Uso Básico

### Modo Dry-Run (Recomendado para primeira execução)

```bash
./py_rme_canary/quality-pipeline/quality_lf.sh --dry-run --verbose
```

**O que faz:**
- ✅ Executa todas as análises
- ✅ Gera relatórios detalhados
- ❌ **NÃO modifica** nenhum arquivo

### Modo Apply (Aplica correções)

```bash
./py_rme_canary/quality-pipeline/quality_lf.sh --apply
```

**O que faz:**
- ✅ Aplica correções do Ruff
- ✅ Aplica transformações ast-grep
- ✅ Aplica transformações LibCST
- ✅ Formata código
- ✅ Executa testes de validação
- ✅ Rollback automático em caso de falha

---

## Opções Avançadas

### Pular Testes (execução mais rápida)

```bash
./py_rme_canary/quality-pipeline/quality_lf.sh --apply --skip-tests
```

### Pular LibCST (transformações complexas)

```bash
./py_rme_canary/quality-pipeline/quality_lf.sh --apply --skip-libcst
```

### Pular SonarQube (sem análise de segurança)

```bash
./py_rme_canary/quality-pipeline/quality_lf.sh --apply --skip-sonarlint
```

### Habilitar Telemetria (debugging avançado)

```bash
./py_rme_canary/quality-pipeline/quality_lf.sh --apply --telemetry
```

Gera arquivo `.quality_reports/telemetry.jsonl` com eventos estruturados.

### Otimização de Performance (v2.3+)

O pipeline agora usa escopo de projeto + cache de baseline para reduzir tempo de reexecução:

```bash
# Escopo padrão já é py_rme_canary, mas pode ser sobrescrito:
PROJECT_DIR=py_rme_canary \
QUALITY_HASH_TARGETS=py_rme_canary/core,py_rme_canary/logic_layer,py_rme_canary/vis_layer \
./py_rme_canary/quality-pipeline/quality_lf.sh --dry-run --skip-tests --skip-libcst --skip-sonarlint --timeout 120
```

Notas:
- `PROJECT_DIR`: limita análise para o projeto alvo (evita varredura desnecessária do monorepo).
- `QUALITY_HASH_TARGETS`: controla quais caminhos entram no hash de cache.
- `QUALITY_FAST_HASH=true` (padrão): usa hash rápido baseado em `git HEAD + status` antes do hash completo.
- `--timeout`: limita execução de ferramentas lentas para evitar travamentos prolongados.
- `--no-cache`: força reexecução completa quando necessário.

### Ambiente Windows (PowerShell + Git Bash)

Em Windows, o `quality_lf.sh` pode resolver para um Python diferente (`/usr/bin/python3`) quando executado no Git Bash. Isso gera falsos avisos de ferramentas ausentes (`mypy`, `ruff`, etc.) mesmo com elas instaladas no Python do projeto.

Use explicitamente o binário correto:

```bash
PYTHON_BIN=python.exe ./py_rme_canary/quality-pipeline/quality_lf.sh --dry-run --verbose
```

Ou, no PowerShell:

```powershell
$env:PYTHON_BIN='python.exe'; bash py_rme_canary/quality-pipeline/quality_lf.sh --dry-run --verbose
```

Atualização recente do pipeline:
- `ruff`, `mypy` e `radon` são executados via `"$PYTHON_BIN" -m ...`.
- Isso reduz divergência entre ambiente de shell e ambiente de dependências Python do projeto.
- Se o interpretador resolvido for `<3.12`, o `mypy` é pulado com aviso técnico (sem falha falsa de sintaxe), e o log indica como forçar `PYTHON_BIN` para Python 3.12+.

### Integração Jules Local (v2.3+)

Fluxo operacional esperado:

```bash
quality_lf.sh (local) -> Jules API -> reports/jules/suggestions.*
```

Variáveis de ambiente usadas:

```bash
JULES_API_KEY=<secret>
JULES_SOURCE=sources/<owner-repo>
JULES_BRANCH=main
```

Comandos úteis:

```bash
# Verificar conectividade da API/local source
python py_rme_canary/scripts/jules_runner.py --project-root . check

# Gerar contrato de sugestões manualmente
python py_rme_canary/scripts/jules_runner.py --project-root . generate-suggestions \
  --quality-report .quality_reports/refactor_summary.md \
  --output-dir reports/jules \
  --schema .github/jules/suggestions.schema.json

# Auditar estrutura de personas (legacy vs packs atuais)
python py_rme_canary/scripts/jules_runner.py --project-root . audit-persona-structure \
  --json-out .quality_reports/jules_persona_audit.json

# Gerar snapshot local de contexto de PR do Jules (alinhado ao workflow Codex)
python py_rme_canary/scripts/build_jules_context.py \
  --owner <github-owner> \
  --repo <github-repo> \
  --pr-number <numero-pr>

# Operacao de sessoes Jules (monitoramento assíncrono)
python py_rme_canary/scripts/jules_runner.py --project-root . list-sources --page-size 50
python py_rme_canary/scripts/jules_runner.py --project-root . list-sessions --page-size 20
python py_rme_canary/scripts/jules_runner.py --project-root . session-status sessions/<id>
python py_rme_canary/scripts/jules_runner.py --project-root . approve-plan sessions/<id>
python py_rme_canary/scripts/jules_runner.py --project-root . send-message sessions/<id> "continue with small safe steps"
```

Operational notes:
- If `JULES_API_KEY`/`JULES_SOURCE` are not configured, the runner still emits schema-compatible artifacts with setup guidance and no secret leakage.
- The pipeline can skip Jules with `--skip-jules`.
- The runner reads `JULES_SOURCE`/`JULES_BRANCH` from `.env` by default and supports CLI overrides.
- Jules prompts are built with untrusted-context sanitization (control-char filtering and prompt-injection neutralization), while keeping a stable JSON contract for `reports/jules/suggestions.*`.
- O `quality_lf.sh` também executa auditoria de personas e gera `.quality_reports/jules_persona_audit.json` para detectar drift estrutural entre legado e estrutura atual.

### Selective Rust Acceleration (optional)

The editor remains **PyQt6-first**, with selective Rust/PyO3 acceleration for measured hot paths while preserving Python fallback behavior.

Current boundary:
- Python adapter: `py_rme_canary/logic_layer/rust_accel.py`
- Optional Rust module: `py_rme_canary/rust/py_rme_canary_rust`

Local build:
```bash
cd py_rme_canary/rust/py_rme_canary_rust
python -m pip install maturin
maturin develop --release
```

Acceptance criteria:
- Equivalent behavior with and without the Rust module.
- Test coverage for both fallback and backend execution paths.

---

## Estrutura de Diretórios

```
projeto/
├── py_rme_canary/quality-pipeline/quality_lf.sh   # Script principal
├── sonar-project.properties        # Config SonarQube
├── tools/
│   ├── ast_rules/
│   │   └── python/
│   │       ├── anti-patterns.yml   # Regras ast-grep
│   │       └── security.yml
│   └── libcst_transforms/
│       └── modernize_typing.py     # Transformações LibCST
├── .quality_reports/               # Relatórios gerados
│   ├── refactor_summary.md         # Relatório principal
│   ├── quality_*.log               # Logs timestamped
│   ├── symbols_*.json              # Índice de símbolos
│   └── issues_normalized.json      # Issues consolidados
└── .quality_cache/                 # Cache de ferramentas
    └── mypy_cache/                 # Cache do Mypy
```

---

## Fluxo de Execução

### Fase 1: Baseline (Sempre executada)

1. **Indexação de Símbolos**
   - Mapeia todas funções/classes do projeto
   - Gera `symbols_before.json`

2. **Ruff Check**
   - Executa linter completo
   - Categorias: F, E, W, I, N, UP, B, C4, SIM, PERF, PL, RUF, S
   - Salva `.ruff.json`

3. **Mypy Type Check**
   - Modo strict em `core` e `logic_layer`
   - Modo incremental em `vis_layer`
   - Salva `.mypy_baseline.log`

4. **Radon Metrics**
   - Complexidade Ciclomática (CC)
   - Índice de Manutenibilidade (MI)
   - Salva `.radon.json`

### Fase 2: Refatoração (Apenas com --apply)

5. **ast-grep Scan**
   - Aplica regras de `tools/ast_rules/python/*.yml`
   - Reescreve código automaticamente
   - Gera `astgrep_results.json`

6. **LibCST Transforms**
   - Executa transformações de `tools/libcst_transforms/`
   - Exemplo: `List[X]` → `list[X]`
   - Modificações in-place

7. **Ruff Fix + Format**
   - Aplica correções automáticas
   - Formata código com Ruff formatter
   - Salva `.ruff_after.json`

### Fase 3: Validação (Apenas com --apply)

8. **Mypy Re-check**
   - Valida que refatorações não quebraram tipos
   - Falha = Rollback automático
   - Salva `.mypy_after.log`

9. **Pytest**
   - Testes unitários (`tests/unit`)
   - Testes UI (`tests/ui` com pytest-qt)
   - Falha = Rollback automático

### Fase 4: Segurança

10. **SonarQube Scan**
    - Análise de segurança (Security Hotspots)
    - Code Smells e Bugs
    - Resultados no dashboard

### Fase 5: Consolidação

11. **Normalização de Issues**
    - Consolida issues de todas ferramentas
    - Formato padronizado JSON
    - Salva `issues_normalized.json`

12. **Comparação de Símbolos**
    - Compara `symbols_before` vs `symbols_after`
    - Detecta remoções inesperadas
    - Avisa sobre mudanças estruturais

13. **Relatório Final**
    - Markdown consolidado
    - Estatísticas de melhoria
    - Salva `refactor_summary.md`

---

## Criando Regras ast-grep Customizadas

### Exemplo: Detectar uso de `eval()`

```yaml
# tools/ast_rules/python/security.yml
rules:
  - id: no-eval
    message: "Nunca use eval() - risco de segurança crítico"
    severity: error
    language: python
    rule:
      pattern: eval($$$ARGS)
```

### Exemplo: Forçar docstrings em classes públicas

```yaml
rules:
  - id: require-class-docstring
    message: "Classes públicas devem ter docstrings"
    severity: warning
    language: python
    rule:
      pattern: |
        class $NAME:
            $$$BODY
    constraints:
      NAME:
        regex: "^[A-Z]"  # Começa com maiúscula = pública
      BODY:
        not:
          pattern: """$$$DOC"""
```

### Testando Regras Antes de Aplicar

```bash
# Testa uma regra específica
sg test tools/ast_rules/python/anti-patterns.yml

# Visualiza AST de um código
echo 'print("test")' | sg dump --lang python

# Busca sem rewrite (safe)
sg scan --rule tools/ast_rules/python/security.yml .
```

---

## Criando Transformações LibCST

### Template Básico

```python
# tools/libcst_transforms/my_transform.py
import libcst as cst
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand

class MyTransform(VisitorBasedCodemodCommand):
    DESCRIPTION = "Descrição da transformação"

    def leave_FunctionDef(
        self,
        original_node: cst.FunctionDef,
        updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        # Sua lógica aqui
        return updated_node
```

### Executando Manualmente

```bash
python -m libcst.tool codemod \
  tools/libcst_transforms/my_transform.py \
  py_rme_canary/
```

---

## Integração com CI/CD

### GitHub Actions

```yaml
name: Quality Pipeline

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install ruff mypy radon pytest libcst
          cargo install ast-grep

      - name: Run Quality Pipeline
        run: ./py_rme_canary/quality-pipeline/quality_lf.sh --dry-run --verbose

      - name: Upload Reports
        uses: actions/upload-artifact@v3
        with:
          name: quality-reports
          path: .quality_reports/
```

---

## Troubleshooting

### Erro: "ShellCheck falhou"

**Causa:** Script tem problemas de sintaxe ou boas práticas.

**Solução:**
```bash
shellcheck py_rme_canary/quality-pipeline/quality_lf.sh
# Corrija os warnings antes de executar
```

### Erro: "Mypy detectou novos erros após refatoração"

**Causa:** Transformações automáticas quebraram tipagem.

**Solução:**
1. Pipeline faz rollback automático
2. Revise manualmente o código problemático
3. Ajuste regras ast-grep ou LibCST

### Erro: "SonarScanner não encontrado"

**Causa:** SonarQube não instalado ou não no PATH.

**Solução:**
```bash
# Pula análise de segurança
./py_rme_canary/quality-pipeline/quality_lf.sh --apply --skip-sonarlint
```

### Performance lenta

**Causa:** Cache do Mypy inválido ou projeto muito grande.

**Solução:**
```bash
# Limpa cache
rm -rf .quality_cache/mypy_cache

# Pula testes para execução mais rápida
./py_rme_canary/quality-pipeline/quality_lf.sh --apply --skip-tests
```

---

## Métricas de Sucesso

Após executar o pipeline, verifique o `refactor_summary.md`:

| Métrica | Objetivo | Crítico se |
|---------|----------|-----------|
| Issues Ruff | Redução de 50%+ | Aumento |
| Complexidade Radon | Funções < 10 | Funções > 15 |
| Cobertura Mypy | 95%+ em core | < 80% em core |
| Símbolos removidos | 0 | > 5 |
| Testes falhando | 0 | > 0 |

---

## Manutenção

### Atualização de Ferramentas

```bash
# Atualiza tudo
pip install --upgrade ruff mypy radon pytest libcst
cargo install ast-grep --force
```

### Limpeza de Cache

```bash
# Remove arquivos temporários
rm -rf .quality_reports/ .quality_tmp/ .quality_cache/
```

### Auditoria do Script

```bash
# Valida o próprio quality_lf.sh
shellcheck py_rme_canary/quality-pipeline/quality_lf.sh

# Executa em modo verbose para debugging
./py_rme_canary/quality-pipeline/quality_lf.sh --dry-run --verbose --telemetry
```

---

## Referências

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Mypy Cheat Sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
- [ast-grep Guide](https://ast-grep.github.io/guide/introduction.html)
- [LibCST Tutorial](https://libcst.readthedocs.io/en/latest/tutorial.html)
- [SonarQube Python](https://docs.sonarqube.org/latest/analysis/languages/python/)

---

**Última atualização:** 2026-01-10
**Versão do Pipeline:** 2.0.0
