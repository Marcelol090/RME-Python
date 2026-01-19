# Quality Pipeline - Plano de Melhorias Completo

**Status Atual:** Pipeline funcional, mas com oportunidades de otimizacao  
**Objetivo:** Melhorar performance, manutenibilidade e confiabilidade  
**Timeline:** 4-6 semanas (progresso incremental)

---

## Fase 1: Quick Wins (Semana 1-2)

### Prioridade CRITICA - Refatorar Python Embarcado

**Problema:** 200+ linhas de Python em heredocs sao dificeis de testar e manter.

**Solucao:**

#### Passo 1.1: Criar estrutura de scripts

```bash
# Criar diretorios
mkdir -p tools/quality_scripts
touch tools/quality_scripts/__init__.py
```

#### Passo 1.2: Extrair index_symbols

Criar arquivo `tools/quality_scripts/index_symbols.py`:

```python
#!/usr/bin/env python3
"""
Symbol indexer - Extrai funcoes/classes de todos arquivos Python.
"""
import ast
import json
from pathlib import Path
import sys
from typing import Any


def should_skip(path: Path) -> bool:
    """Verifica se arquivo deve ser ignorado."""
    skip_patterns = (".venv", "__pycache__", "site-packages", ".tox", "build", "dist")
    return any(p in str(path) for p in skip_patterns)


def extract_symbols(path: Path) -> list[dict[str, Any]]:
    """Extrai simbolos de um arquivo Python."""
    symbols = []
    
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as e:
        return [{"error": str(e), "file": str(path)}]
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append({
                "type": node.__class__.__name__,
                "name": node.name,
                "file": str(path),
                "line": node.lineno,
                "decorators": [
                    d.id if isinstance(d, ast.Name) else str(d)
                    for d in getattr(node, 'decorator_list', [])
                ]
            })
    
    return symbols


def index_all_symbols(root: Path = Path(".")) -> dict[str, Any]:
    """Indexa todos os simbolos do projeto."""
    all_symbols = []
    errors = []
    
    for path in root.rglob("*.py"):
        if should_skip(path):
            continue
        
        symbols = extract_symbols(path)
        for symbol in symbols:
            if "error" in symbol:
                errors.append(symbol)
            else:
                all_symbols.append(symbol)
    
    return {
        "symbols": all_symbols,
        "errors": errors,
        "total_files": len(all_symbols),
    }


def main() -> int:
    """Entry point."""
    if len(sys.argv) < 2:
        print("Usage: index_symbols.py <output_file.json>", file=sys.stderr)
        return 1
    
    output_path = Path(sys.argv[1])
    
    print(f"Indexando simbolos...")
    result = index_all_symbols()
    
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    
    print(f"âœ“ {len(result['symbols'])} simbolos indexados")
    if result['errors']:
        print(f"âš  {len(result['errors'])} arquivo(s) com erro", file=sys.stderr)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

#### Passo 1.3: Extrair normalize_issues

Criar arquivo `tools/quality_scripts/normalize_issues.py`:

```python
#!/usr/bin/env python3
"""
Issue normalizer - Consolida issues de multiplas ferramentas.
"""
import json
from pathlib import Path
import sys
from typing import Any


def safe_load_json(path: Path | str) -> Any:
    """Carrega JSON com fallback para erro."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def normalize_ruff_issues(ruff_data: list[dict]) -> list[dict]:
    """Normaliza issues do Ruff."""
    issues = []
    
    if not ruff_data:
        return issues
    
    for issue in ruff_data:
        issues.append({
            "tool": "ruff",
            "code": issue.get("code"),
            "message": issue.get("message"),
            "file": issue.get("filename"),
            "line": issue.get("location", {}).get("row"),
            "column": issue.get("location", {}).get("column"),
            "severity": "high" if issue.get("code", "").startswith("S") else "medium",
        })
    
    return issues


def normalize_radon_issues(radon_data: Any) -> list[dict]:
    """Normaliza metricas do Radon."""
    issues = []
    
    if not radon_data:
        return issues
    
    # Radon pode retornar dict de listas ou lista direta
    radon_entries = []
    
    if isinstance(radon_data, dict):
        for file_entries in radon_data.values():
            if isinstance(file_entries, list):
                radon_entries.extend(file_entries)
    elif isinstance(radon_data, list):
        radon_entries = radon_data
    
    for entry in radon_entries:
        if not isinstance(entry, dict):
            continue
        
        complexity = entry.get("complexity", 0)
        
        issues.append({
            "tool": "radon",
            "function": entry.get("name"),
            "complexity": complexity,
            "file": entry.get("filename"),
            "line": entry.get("lineno"),
            "severity": "high" if complexity > 10 else "medium",
        })
    
    return issues


def normalize_astgrep_issues(astgrep_data: Any) -> list[dict]:
    """Normaliza resultados do ast-grep."""
    issues = []
    
    if not astgrep_data:
        return issues
    
    # ast-grep pode retornar dict ou lista
    astgrep_iter = []
    
    if isinstance(astgrep_data, dict):
        astgrep_iter = [astgrep_data]
    elif isinstance(astgrep_data, list):
        astgrep_iter = astgrep_data
    
    for file_matches in astgrep_iter:
        if not isinstance(file_matches, dict):
            continue
        
        for match in file_matches.get("matches", []):
            issues.append({
                "tool": "ast-grep",
                "file": file_matches.get("file"),
                "line": match.get("range", {}).get("start", {}).get("line"),
                "pattern": match.get("text"),
                "rule": match.get("rule_id"),
                "severity": "medium",
            })
    
    return issues


def normalize_all_issues() -> dict[str, Any]:
    """Normaliza issues de todas as ferramentas."""
    all_issues = []
    
    # Ruff
    ruff_data = safe_load_json(".ruff.json")
    all_issues.extend(normalize_ruff_issues(ruff_data or []))
    
    # Radon
    radon_data = safe_load_json(".radon.json")
    all_issues.extend(normalize_radon_issues(radon_data))
    
    # ast-grep
    astgrep_data = safe_load_json(".quality_reports/astgrep_results.json")
    all_issues.extend(normalize_astgrep_issues(astgrep_data))
    
    return {
        "issues": all_issues,
        "total": len(all_issues),
        "by_tool": {
            "ruff": len([i for i in all_issues if i["tool"] == "ruff"]),
            "radon": len([i for i in all_issues if i["tool"] == "radon"]),
            "ast-grep": len([i for i in all_issues if i["tool"] == "ast-grep"]),
        },
        "by_severity": {
            "high": len([i for i in all_issues if i["severity"] == "high"]),
            "medium": len([i for i in all_issues if i["severity"] == "medium"]),
        },
    }


def main() -> int:
    """Entry point."""
    if len(sys.argv) < 2:
        print("Usage: normalize_issues.py <output_file.json>", file=sys.stderr)
        return 1
    
    output_path = Path(sys.argv[1])
    
    print("Normalizando issues...")
    result = normalize_all_issues()
    
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    
    print(f"âœ“ {result['total']} issues normalizados")
    print(f"  - Ruff: {result['by_tool']['ruff']}")
    print(f"  - Radon: {result['by_tool']['radon']}")
    print(f"  - ast-grep: {result['by_tool']['ast-grep']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

#### Passo 1.4: Atualizar quality.sh

Substituir heredocs por chamadas aos scripts:

```bash
# ANTES (heredoc):
index_symbols() {
  local output="$1"
  "$PYTHON_BIN" - "$output" <<'PYTHON'
  import ast
  # ... 50+ linhas ...
  PYTHON
}

# DEPOIS (script externo):
index_symbols() {
  local output="$1"
  log INFO "Indexando simbolos -> $output"
  
  "$PYTHON_BIN" tools/quality_scripts/index_symbols.py "$output" || {
    log ERROR "Falha ao indexar simbolos"
    return 1
  }
}

normalize_issues() {
  log INFO "Normalizando issues..."
  
  "$PYTHON_BIN" tools/quality_scripts/normalize_issues.py "$ISSUES_NORMALIZED" || {
    log ERROR "Falha ao normalizar issues"
    return 1
  }
}
```

**Tempo estimado:** 2-3 horas  
**Beneficio:** Codigo testavel, debugavel, reutilizavel

---

### Prioridade ALTA - Adicionar pre-commit

**Problema:** Commits ruins entram no repositorio antes das validacoes.

**Solucao:**

#### Passo 2.1: Instalar pre-commit

```bash
# Via pip
pip install pre-commit

# Ou via uv (mais rapido)
uv pip install pre-commit
```

#### Passo 2.2: Criar configuracao

Criar arquivo `.pre-commit-config.yaml`:

```yaml
# See https://pre-commit.com for more information
repos:
  # Ruff - Linter + Formatter
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.2.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
  
  # Mypy - Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-PyQt6]
        args: [--config-file=pyproject.toml]
        files: ^(py_rme_canary/core|py_rme_canary/logic_layer)/.*\.py$
  
  # Radon - Complexity check
  - repo: local
    hooks:
      - id: radon-cc
        name: Radon Cyclomatic Complexity
        entry: radon cc --min B --total-average
        language: system
        types: [python]
        pass_filenames: false
  
  # ShellCheck - Bash linting
  - repo: https://github.com/shellcheck-py/shellcheck-py
    rev: v0.9.0.6
    hooks:
      - id: shellcheck
        args: [-x]  # Follow source
  
  # Trailing whitespace, EOF, YAML
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: [--maxkb=1000]
      - id: check-merge-conflict
```

#### Passo 2.3: Instalar hooks

```bash
# Instala hooks do git
pre-commit install

# Testa em todos os arquivos (primeira vez)
pre-commit run --all-files

# De agora em diante, roda automaticamente antes de cada commit!
```

**Tempo estimado:** 30 minutos  
**Beneficio:** Previne 90% dos erros de qualidade antes do commit

---

### Prioridade ALTA - Migrar para uv

**Problema:** pip e lento (30-60 segundos para install).

**Solucao:**

#### Passo 3.1: Instalar uv

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex

# Adicionar ao PATH (se necessario)
export PATH="$HOME/.cargo/bin:$PATH"
```

#### Passo 3.2: Migrar requirements

```bash
# Criar requirements.txt (se nao existe)
pip freeze > requirements.txt

# Testar instalacao com uv
uv pip install -r requirements.txt

# Criar venv com uv
uv venv

# Ativar
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

#### Passo 3.3: Atualizar quality.sh

```bash
# Adicionar no inicio do quality.sh
if command -v uv &>/dev/null; then
  PYTHON_INSTALL_CMD="uv pip install"
  log INFO "Usando uv (fast mode)"
else
  PYTHON_INSTALL_CMD="pip install"
  log WARN "uv nao encontrado - usando pip (slow mode)"
fi
```

**Tempo estimado:** 15 minutos  
**Beneficio:** 10-100x speedup em instalacao de dependencias

---

## Fase 2: Paralelizacao (Semana 3-4)

### Prioridade MEDIA - GNU Parallel

**Problema:** Ferramentas rodam sequencialmente (90+ segundos).

**Solucao:**

#### Passo 4.1: Instalar GNU Parallel

```bash
# Ubuntu/Debian
sudo apt install parallel

# macOS
brew install parallel

# Primeira execucao (aceitar licenca)
parallel --citation
```

#### Passo 4.2: Modificar quality.sh

Adicionar funcao de paralelizacao:

```bash
# Funcao auxiliar para exports
export_functions() {
  export -f log
  export -f run_ruff
  export -f run_mypy
  export -f run_radon
  export -f run_astgrep
  
  # Exportar variaveis necessarias
  export PYTHON_BIN
  export REPORT_DIR
  export MODE
  export VERBOSE
}

# Fase 1 com paralelizacao
run_baseline_parallel() {
  log INFO "=== FASE 1: BASELINE (PARALELO) ==="
  
  export_functions
  
  # Rodar em paralelo (3 jobs simultaneos)
  parallel --tag --halt now,fail=1 --jobs 3 ::: \
    "run_ruff .ruff.json" \
    "run_mypy .mypy_baseline.log" \
    "run_radon .radon.json"
  
  log SUCCESS "Baseline concluido em paralelo"
}
```

#### Passo 4.3: Testar

```bash
# Antes (sequencial):
time ./quality.sh --dry-run
# real    1m32.456s

# Depois (paralelo):
time ./quality.sh --dry-run
# real    0m48.123s

# Speedup: ~2x
```

**Tempo estimado:** 1-2 horas  
**Beneficio:** 2-3x reducao no tempo de execucao

---

### Prioridade MEDIA - Adicionar Cache Inteligente

**Problema:** Re-executa tudo mesmo quando codigo nao mudou.

**Solucao:**

#### Passo 5.1: Criar funcao de cache

Adicionar em quality.sh:

```bash
# Calcula hash do conteudo Python
get_python_hash() {
  find . -name "*.py" -type f \
    ! -path "./.venv/*" \
    ! -path "./__pycache__/*" \
    -exec sha256sum {} \; \
    | sha256sum \
    | cut -d' ' -f1
}

# Executa comando com cache
run_with_cache() {
  local cache_key="$1"
  local output_file="$2"
  local command="$3"
  
  local cache_file="$CACHE_DIR/${cache_key}.cache"
  
  if [[ -f "$cache_file" ]]; then
    local cached_hash
    cached_hash=$(cat "$cache_file")
    
    local current_hash
    current_hash=$(get_python_hash)
    
    if [[ "$cached_hash" == "$current_hash" ]]; then
      log INFO "Cache HIT para $cache_key"
      return 0
    fi
  fi
  
  log INFO "Cache MISS para $cache_key - executando..."
  eval "$command"
  
  # Salva hash no cache
  get_python_hash > "$cache_file"
}

# Uso
run_ruff_cached() {
  run_with_cache "ruff" ".ruff.json" "run_ruff .ruff.json"
}
```

**Tempo estimado:** 2 horas  
**Beneficio:** Pula execucoes desnecessarias (speedup 10x quando cache hit)

---

## Fase 3: Task Migration (Semana 5-6)

### Prioridade BAIXA - Migrar para Task

**Problema:** Bash fica complexo para orquestracao.

**Solucao:**

#### Passo 6.1: Instalar Task

```bash
# Go 1.19+ necessario
go install github.com/go-task/task/v3/cmd/task@latest

# Verificar instalacao
task --version
```

#### Passo 6.2: Criar Taskfile.yml

Criar arquivo `Taskfile.yml`:

```yaml
version: '3'

vars:
  PYTHON: python
  REPORT_DIR: .quality_reports
  CACHE_DIR: .quality_cache

tasks:
  # Setup
  setup:
    desc: Install all dependencies
    cmds:
      - uv pip install -r requirements.txt
      - pre-commit install
  
  # Quality checks (parallel by default!)
  quality:check:
    desc: Run all quality checks
    deps:
      - ruff:check
      - mypy:check
      - radon:check
  
  quality:fix:
    desc: Apply auto-fixes
    deps: [snapshot]
    cmds:
      - task: ruff:fix
      - task: tests
  
  # Ruff
  ruff:check:
    desc: Check code with Ruff
    sources:
      - '**/*.py'
    generates:
      - '{{.REPORT_DIR}}/ruff.json'
    cmds:
      - mkdir -p {{.REPORT_DIR}}
      - ruff check . --output-format=json > {{.REPORT_DIR}}/ruff.json
  
  ruff:fix:
    desc: Auto-fix with Ruff
    cmds:
      - ruff check --fix .
      - ruff format .
  
  # Mypy
  mypy:check:
    desc: Type check with Mypy
    sources:
      - 'py_rme_canary/core/**/*.py'
      - 'py_rme_canary/logic_layer/**/*.py'
    generates:
      - '{{.REPORT_DIR}}/mypy.log'
    cmds:
      - mkdir -p {{.CACHE_DIR}}/mypy_cache
      - |
        mypy py_rme_canary/core py_rme_canary/logic_layer \
          --config-file=pyproject.toml \
          --cache-dir={{.CACHE_DIR}}/mypy_cache \
          > {{.REPORT_DIR}}/mypy.log 2>&1 || true
  
  # Radon
  radon:check:
    desc: Check complexity with Radon
    sources:
      - '**/*.py'
    generates:
      - '{{.REPORT_DIR}}/radon.json'
    cmds:
      - mkdir -p {{.REPORT_DIR}}
      - radon cc . --min B --json > {{.REPORT_DIR}}/radon.json
  
  # Tests
  tests:
    desc: Run all tests
    cmds:
      - pytest tests/ -v --cov=py_rme_canary --cov-report=term-missing
  
  tests:unit:
    desc: Run unit tests only
    cmds:
      - pytest tests/unit/ -v
  
  tests:ui:
    desc: Run UI tests (headless)
    env:
      QT_QPA_PLATFORM: offscreen
    cmds:
      - pytest tests/ui/ -v --qt-no-window-capture
  
  # Utilities
  snapshot:
    desc: Create git snapshot for rollback
    cmds:
      - git add -A
      - git stash push -u -m "quality-snapshot-$(date +%s)"
  
  clean:
    desc: Clean all generated files
    cmds:
      - rm -rf {{.REPORT_DIR}} {{.CACHE_DIR}}
      - rm -f .ruff*.json .radon*.json .mypy*.log
  
  # Full pipeline
  pipeline:
    desc: Run full quality pipeline
    cmds:
      - task: quality:check
      - task: tests
      - echo "âœ“ Pipeline completo!"
```

#### Passo 6.3: Testar Task

```bash
# Rodar quality check (paralelo automatico!)
task quality:check

# Aplicar fixes
task quality:fix

# Pipeline completo
task pipeline

# Ver todas as tasks disponiveis
task --list
```

**Tempo estimado:** 4-6 horas  
**Beneficio:** YAML legivel, cache automatico, paralelizacao nativa

---

## Fase 4: Ferramentas Adicionais (Opcional)

### Watchexec - Auto-run em mudancas

```bash
# Instalar
cargo install watchexec-cli

# Usar
watchexec -e py -- task quality:check

# Agora salva .py -> roda checks automaticamente!
```

### Hyperfine - Benchmark

```bash
# Instalar
cargo install hyperfine

# Comparar quality.sh vs Task
hyperfine --warmup 2 \
  './quality.sh --dry-run' \
  'task quality:check'
```

### Earthly - CI/CD Reproduzivel

Criar `Earthfile`:

```Dockerfile
VERSION 0.7

quality:
    FROM python:3.12-slim
    WORKDIR /app
    
    COPY requirements.txt .
    RUN pip install -r requirements.txt
    
    COPY . .
    
    RUN ruff check . --output-format=json > ruff.json
    RUN mypy . --config-file=pyproject.toml
    
    SAVE ARTIFACT ruff.json AS LOCAL .quality_reports/ruff.json
```

```bash
# Rodar (identico localmente e no CI!)
earthly +quality
```

---

## Checklist de Implementacao

### Semana 1-2: Quick Wins
- [ ] Criar `tools/quality_scripts/`
- [ ] Extrair `index_symbols.py`
- [ ] Extrair `normalize_issues.py`
- [ ] Atualizar `quality.sh` para usar scripts externos
- [ ] Testar: `./quality.sh --dry-run --verbose`
- [ ] Instalar pre-commit
- [ ] Criar `.pre-commit-config.yaml`
- [ ] Rodar: `pre-commit run --all-files`
- [ ] Instalar uv
- [ ] Testar: `uv pip install -r requirements.txt`
- [ ] Atualizar quality.sh para detectar uv

### Semana 3-4: Paralelizacao
- [ ] Instalar GNU Parallel
- [ ] Adicionar `export_functions()` em quality.sh
- [ ] Modificar baseline para rodar em paralelo
- [ ] Testar: `time ./quality.sh --dry-run`
- [ ] Adicionar funcao `get_python_hash()`
- [ ] Adicionar funcao `run_with_cache()`
- [ ] Modificar run_ruff/mypy/radon para usar cache
- [ ] Testar cache: rodar 2x seguidas e verificar speedup

### Semana 5-6: Task Migration
- [ ] Instalar Task (Go 1.19+ requerido)
- [ ] Criar `Taskfile.yml` inicial
- [ ] Migrar task: ruff:check
- [ ] Migrar task: mypy:check
- [ ] Migrar task: radon:check
- [ ] Migrar task: tests
- [ ] Testar: `task quality:check`
- [ ] Adicionar tasks de utilidade (clean, snapshot)
- [ ] Documentar uso de Task no README

### Opcional: Ferramentas Avancadas
- [ ] Instalar watchexec
- [ ] Testar: `watchexec -e py -- task quality:check`
- [ ] Instalar hyperfine
- [ ] Benchmark quality.sh vs Task
- [ ] Avaliar Earthly para CI/CD

---

## Metricas de Sucesso

| Metrica | Antes | Meta | Como Medir |
|---------|-------|------|------------|
| **Tempo de execucao (dry-run)** | 90s | 45s | `time ./quality.sh --dry-run` |
| **Cache hit rate** | 0% | 80% | Log mostra "Cache HIT" |
| **Codigo Python testavel** | 0 linhas | 100% | Scripts em `tools/` |
| **Pre-commit adoption** | Nao | Sim | `.pre-commit-config.yaml` existe |
| **Deps install time** | 45s | 5s | `time uv pip install -r requirements.txt` |

---

## Rollback Plan

Se algo der errado:

```bash
# Rollback completo (Git)
git stash pop  # Se usou snapshot()
git reset --hard HEAD~1

# Rollback parcial (desinstalar ferramenta)
pre-commit uninstall
pip uninstall pre-commit

# Reverter para quality.sh original
git checkout main -- quality.sh
```

---

## Proximos Passos Apos Conclusao

1. **Documentar no README.md**
   - Como usar Task
   - Como usar pre-commit
   - Exemplos de workflow

2. **Adicionar ao CI/CD**
   ```yaml
   # .github/workflows/quality.yml
   - name: Run quality checks
     run: task quality:check
   ```

3. **Treinar equipe**
   - Workshop sobre pre-commit
   - Documentacao de Task
   - Best practices

4. **Monitorar metricas**
   - Tempo de execucao
   - Taxa de cache hit
   - Cobertura de testes

---

## Status Atual (2026-01-19)

- Taskfile criado para setup, quality:check, quality:fix, testes e utilitários.
- Próximo passo: instalar 	ask (Go 1.19+) e executar 	ask quality:check; documentar uso no README finaliza a migração.

---

## Contatos e Suporte

**Duvidas?**
- Revisar documentacao: `quality_pipeline_guide.md`
- Testar em ambiente isolado primeiro
- Fazer backup antes de mudancas grandes

**Recursos:**
- Task: https://taskfile.dev/
- pre-commit: https://pre-commit.com/
- uv: https://github.com/astral-sh/uv
- GNU Parallel: https://www.gnu.org/software/parallel/
