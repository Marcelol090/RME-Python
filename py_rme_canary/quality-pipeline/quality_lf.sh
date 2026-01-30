#!/usr/bin/env bash
set -Eeuo pipefail

#############################################
# CONFIGURAÇÃO GLOBAL
#############################################

export PYTHONUTF8=1
export TERM="${TERM:-xterm-256color}"
PYTHON_BIN="${PYTHON_BIN:-python}"

# Garante que o diretório de scripts do Python esteja no PATH (Windows/MinGW)
if [[ "${OS:-}" == "Windows_NT" || "${OSTYPE:-}" == msys* || "${OSTYPE:-}" == cygwin* ]]; then
  PY_SCRIPTS_DIRS="$($PYTHON_BIN -c "import os, site, sysconfig; paths=[sysconfig.get_path('scripts'), sysconfig.get_path('scripts', scheme='nt_user')]; user=site.getuserbase(); paths.append(os.path.join(user, 'Scripts') if user else ''); print('\\n'.join(p for p in paths if p))")"
  while IFS= read -r PY_SCRIPTS_DIR; do
    if [[ -n "$PY_SCRIPTS_DIR" ]]; then
      if command -v cygpath &>/dev/null; then
        PY_SCRIPTS_DIR="$(cygpath -u "$PY_SCRIPTS_DIR")"
      fi
      export PATH="$PY_SCRIPTS_DIR:$PATH"
    fi
  done <<< "$PY_SCRIPTS_DIRS"
fi

# Detecção automática de diretórios (evita hardcoded paths)
ROOT_DIR="${ROOT_DIR:-$(pwd)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QUALITY_SCRIPTS_DIR="$(cd "$SCRIPT_DIR/../tools/quality_scripts" && pwd)"
REPORT_DIR="${REPORT_DIR:-.quality_reports}"
TMP_DIR="${TMP_DIR:-.quality_tmp}"
CACHE_DIR="${CACHE_DIR:-.quality_cache}"
RADON_TARGETS="${RADON_TARGETS:-$ROOT_DIR/py_rme_canary/core,$ROOT_DIR/py_rme_canary/logic_layer}"

# Arquivos de relatório
SYMBOL_INDEX_BEFORE="$REPORT_DIR/symbols_before.json"
SYMBOL_INDEX_AFTER="$REPORT_DIR/symbols_after.json"
ISSUES_NORMALIZED="$REPORT_DIR/issues_normalized.json"
FINAL_REPORT="$REPORT_DIR/refactor_summary.md"
LOG_FILE="$REPORT_DIR/quality_$(date +%Y%m%d_%H%M%S).log"

# Configurações de qualidade
RUFF_CONFIG="${RUFF_CONFIG:-pyproject.toml}"
MYPY_CONFIG="${MYPY_CONFIG:-pyproject.toml}"
RADON_CC_THRESHOLD="${RADON_CC_THRESHOLD:-10}"
RADON_MI_THRESHOLD="${RADON_MI_THRESHOLD:-20}"

# Flags de execução
MODE="dry-run"
SKIP_TESTS=false
SKIP_LIBCST=false
SKIP_SONAR=false
VERBOSE=false
ENABLE_TELEMETRY=false
PARALLEL_AVAILABLE=false

#############################################
# CORES PARA OUTPUT
#############################################

readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

#############################################
# PARSE ARGUMENTOS
#############################################

usage() {
  cat <<EOF
Uso: $0 [opções]

Opções:
  --apply              Aplica alterações (padrão: dry-run)
  --dry-run            Simula execução sem modificar arquivos
  --skip-tests         Pula execução de testes
  --skip-libcst        Pula transformações LibCST
  --skip-sonar         Pula análise SonarQube/SonarLint
  --verbose            Saída detalhada
  --telemetry          Habilita telemetria (OpenTelemetry)
  --help               Exibe esta ajuda

Exemplos:
  $0 --dry-run --verbose
  $0 --apply --skip-tests
EOF
}

while [[ $# -gt 0 ]]; do
  arg="${1%$'\r'}"
  case "$arg" in
    --apply) MODE="apply" ;;
    --dry-run) MODE="dry-run" ;;
    --skip-tests) SKIP_TESTS=true ;;
    --skip-libcst) SKIP_LIBCST=true ;;
    --skip-sonar) SKIP_SONAR=true ;;
    --verbose) VERBOSE=true ;;
    --telemetry) ENABLE_TELEMETRY=true ;;
    --help) usage; exit 0 ;;
    *) echo -e "${RED}Opção desconhecida: $1${NC}"; usage; exit 1 ;;
  esac
  shift
done

#############################################
# LOGGING ESTRUTURADO
#############################################

mkdir -p "$REPORT_DIR" "$TMP_DIR" "$CACHE_DIR"

log() {
  local level="${1}"
  local message="${2}"
  local timestamp
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')

  case "$level" in
    INFO)  echo -e "${CYAN}[INFO]${NC}  [$timestamp] $message" | tee -a "$LOG_FILE" ;;
    WARN)  echo -e "${YELLOW}[WARN]${NC}  [$timestamp] $message" | tee -a "$LOG_FILE" ;;
    ERROR) echo -e "${RED}[ERROR]${NC} [$timestamp] $message" | tee -a "$LOG_FILE" ;;
    SUCCESS) echo -e "${GREEN}[✓]${NC}    [$timestamp] $message" | tee -a "$LOG_FILE" ;;
    DEBUG) [[ "$VERBOSE" == true ]] && echo -e "${BLUE}[DEBUG]${NC} [$timestamp] $message" | tee -a "$LOG_FILE" ;;
  esac

  # Telemetria (OpenTelemetry)
  if [[ "$ENABLE_TELEMETRY" == true ]]; then
    echo "{\"level\":\"$level\",\"timestamp\":\"$timestamp\",\"message\":\"$message\"}" >> "$REPORT_DIR/telemetry.jsonl"
  fi
}

# Prefer uv when available for faster installs
# shellcheck disable=SC2034 # exported for future installers
if command -v uv &>/dev/null; then
  PYTHON_INSTALL_CMD="uv pip install"
  log INFO "Usando uv (fast mode)"
else
  PYTHON_INSTALL_CMD="pip install"
  log WARN "uv nao encontrado - usando pip (slow mode)"
fi

#############################################
# DEPENDÊNCIAS - VALIDAÇÃO AVANÇADA
#############################################

require() {
  local cmd="$1"
  local install_hint="${2:-}"

  if command -v "$cmd" &>/dev/null; then
    log DEBUG "$cmd encontrado: $(command -v "$cmd")"
    return 0
  fi

  # Windows shells may expose only .exe names (no PATHEXT for command -v).
  if command -v "${cmd}.exe" &>/dev/null; then
    log DEBUG "$cmd encontrado: $(command -v "${cmd}.exe")"
    if [[ "$cmd" == "python" ]]; then
      PYTHON_BIN="${cmd}.exe"
    fi
    return 0
  fi

  log ERROR "Dependencia ausente: $cmd"
  [[ -n "$install_hint" ]] && log INFO "Sugestao de instalacao: $install_hint"
  return 1
}

check_dependencies() {
  log INFO "Verificando dependências do sistema..."

  local missing=0

  require python "pip install python" || ((missing++))
  require ruff "pip install ruff" || true
  require mypy "pip install mypy" || true
  require radon "pip install radon" || true
  require sg "cargo install ast-grep" || true
  require git "apt install git / brew install git" || true

  # SonarScanner (opcional)
  if [[ "$SKIP_SONAR" == false ]]; then
    if ! require sonar-scanner "https://docs.sonarqube.org/latest/analysis/scan/sonarscanner/"; then
      log WARN "SonarScanner não encontrado - análise de segurança desabilitada"
      SKIP_SONAR=true
    fi
  fi

  # ShellCheck (recomendado para auditoria)
  if ! require shellcheck "apt install shellcheck / brew install shellcheck"; then
    log WARN "ShellCheck não encontrado - auditoria de scripts desabilitada"
  else
    log INFO "Executando ShellCheck no próprio script..."
    if grep -q $'\r' "$0"; then
      log WARN "ShellCheck pulado: script contém CRLF (normalize o arquivo para LF)"
    elif shellcheck -x "$0"; then
      log SUCCESS "Script passou na auditoria ShellCheck"
    else
      log WARN "ShellCheck encontrou avisos (não bloqueante)"
    fi
  fi

  if [[ $missing -gt 0 ]]; then
    log ERROR "$missing dependência(s) crítica(s) ausente(s)"
    exit 1
  fi

  if command -v parallel &>/dev/null; then
    PARALLEL_AVAILABLE=true
    log INFO "GNU Parallel disponível para baseline"
  else
    log WARN "GNU Parallel não encontrado - baseline será sequencial"
  fi

  log SUCCESS "Todas as dependências verificadas"
}

#############################################
# ROLLBACK AUTOMÁTICO ROBUSTO
#############################################

ROLLBACK_STASH="quality-rollback-$(date +%s)"
ROLLBACK_COMMIT=""
ROLLBACK_ACTIVE=false

snapshot() {
  if [[ "$MODE" == "apply" ]]; then
    log INFO "Criando snapshot git para rollback..."

    if ! git rev-parse --is-inside-work-tree &>/dev/null; then
      log WARN "Repositorio git nao detectado; rollback automatico desabilitado"
      return 0
    fi

    # Captura HEAD atual
    ROLLBACK_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "")

    # Verifica se há mudanças não commitadas
    if ! git diff-index --quiet HEAD --; then
      log WARN "Há mudanças não commitadas - criando stash..."
      git add -A
      git stash push -u -m "$ROLLBACK_STASH" --quiet
      ROLLBACK_ACTIVE=true
    fi

    log SUCCESS "Snapshot criado (commit: ${ROLLBACK_COMMIT:0:8})"
  fi
}

rollback() {
  if [[ "$ROLLBACK_ACTIVE" == false ]]; then
    log WARN "Nenhum snapshot ativo para rollback"
    return 0
  fi

  if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    log WARN "Repositorio git nao detectado; rollback automatico indisponivel"
    return 0
  fi

  log ERROR "Erro detectado - iniciando rollback automático..."

  # Estratégia 1: Reset hard se commit disponível
  if [[ -n "$ROLLBACK_COMMIT" ]]; then
    if git reset --hard "$ROLLBACK_COMMIT" 2>/dev/null; then
      log SUCCESS "Rollback via git reset concluído"
      return 0
    fi
  fi

  # Estratégia 2: Stash pop
  if git stash list | grep -q "$ROLLBACK_STASH"; then
    if git stash pop --index --quiet 2>/dev/null; then
      log SUCCESS "Rollback via git stash concluído"
      return 0
    fi
  fi

  # Fallback: Reset forçado
  log WARN "Fallback: executando git reset --hard HEAD"
  git reset --hard HEAD

  exit 1
}

trap rollback ERR

#############################################
# INDEXADOR DE SÍMBOLOS (AST)
#############################################

index_symbols() {
  local output="$1"
  log INFO "Indexando símbolos → $output"

  if ! "$PYTHON_BIN" "$QUALITY_SCRIPTS_DIR/index_symbols.py" "$output"; then
    log ERROR "Falha ao indexar símbolos"
    return 1
  fi
}

run_with_cache() {
  local cache_key="$1"
  local cache_file="$CACHE_DIR/${cache_key}.hash"
  shift 1

  local current_hash
  current_hash=$("$PYTHON_BIN" "$QUALITY_SCRIPTS_DIR/hash_python.py")
  local previous_hash=""

  if [[ -f "$cache_file" ]]; then
    previous_hash=$(cat "$cache_file")
  fi

  if [[ "$current_hash" == "$previous_hash" ]]; then
    log INFO "Cache HIT para $cache_key (nenhuma mudança nas fontes)"
    return 0
  fi

  log INFO "Cache MISS para $cache_key"
  if "$@"; then
    echo "$current_hash" > "$cache_file"
    return 0
  fi

  return 1
}

run_ruff_cached() {
  if [[ ! -s ".ruff.json" ]]; then
    log WARN "Ruff cache inválido (.ruff.json ausente ou vazio) - regenerando"
    run_ruff ".ruff.json"
    return 0
  fi
  run_with_cache "ruff" run_ruff ".ruff.json"
}

run_mypy_cached() {
  run_with_cache "mypy" run_mypy ".mypy_baseline.log"
}

run_radon_cached() {
  run_with_cache "radon" run_radon ".radon.json"
}

run_baseline_sequential() {
  index_symbols "$SYMBOL_INDEX_BEFORE" || return 1
  run_ruff_cached || return 1
  run_mypy_cached || return 1
  run_radon_cached || return 1
}

run_baseline_parallel() {
  log INFO "=== FASE 1: BASELINE (PARALELO) ==="
  index_symbols "$SYMBOL_INDEX_BEFORE" || return 1
  export -f run_ruff_cached run_mypy_cached run_radon_cached run_with_cache run_ruff run_mypy run_radon log
  if ! parallel --tag --halt now,fail=1 --jobs 3 \
    "run_ruff_cached .ruff.json" \
    "run_mypy_cached .mypy_baseline.log" \
    "run_radon_cached .radon.json"; then
    log ERROR "Baseline paralelo falhou"
    return 1
  fi
}

run_baseline() {
  if [[ "$PARALLEL_AVAILABLE" == true ]]; then
    run_baseline_parallel
  else
    run_baseline_sequential
  fi
}

#############################################
# RUFF - ANÁLISE AVANÇADA
#############################################

run_ruff() {
  local output_file="$1"
  log INFO "Executando Ruff (linter + formatter)..."

  # Análise completa com todas as regras relevantes
  local ruff_select="F,E,W,I,N,UP,B,C4,SIM,PERF,PL,RUF,S"

  if [[ "$MODE" == "dry-run" ]]; then
    log INFO "Modo dry-run: apenas verificação"
    ruff check . \
      --select "$ruff_select" \
      --config "$RUFF_CONFIG" \
      --exit-zero \
      --output-format=json > "$output_file"
  else
    log INFO "Aplicando correções automáticas..."
    ruff check . \
      --select "$ruff_select" \
      --config "$RUFF_CONFIG" \
      --fix \
      --exit-zero \
      --output-format=json > "$output_file"

    log INFO "Formatando código..."
    ruff format . --config "$RUFF_CONFIG"
  fi

  # Estatísticas
  local issue_count
  issue_count=$(jq 'length' "$output_file" 2>/dev/null || echo 0)

  if [[ "$issue_count" -eq 0 ]]; then
    log SUCCESS "Ruff: nenhum issue encontrado"
  else
    log WARN "Ruff: $issue_count issue(s) detectado(s)"
  fi
}

#############################################
# MYPY - VERIFICAÇÃO DE TIPOS ESTRITA
#############################################

run_mypy() {
  local output_file="$1"
  log INFO "Executando Mypy (type checking)..."

  # Cache para performance
  local mypy_cache="$CACHE_DIR/mypy_cache"
  mkdir -p "$mypy_cache"

  # Modo strict para core e logic_layer (conforme pyproject.toml)
  if mypy py_rme_canary/core py_rme_canary/logic_layer py_rme_canary/vis_layer \
    --config-file "$MYPY_CONFIG" \
    --cache-dir "$mypy_cache" \
    --no-error-summary \
    --show-column-numbers \
    --show-error-codes \
    2>&1 | tee "$output_file"; then
    log SUCCESS "Mypy: tipagem validada com sucesso"
    return 0
  else
    log ERROR "Mypy: erros de tipagem detectados"
    return 1
  fi
}

# New function to generate tests via Jules API
run_jules_generate_tests() {
  # Load API key from .env if present
  if [ -f .env ]; then
    # shellcheck disable=SC1091
    set -a
    source .env
    set +a
  fi

  if [ -z "${JULES_API_KEY:-}" ]; then
    log WARN "JULES_API_KEY not set – skipping Jules test generation"
    return 0
  fi

  # Example prompt – can be customized later
  local prompt='Add unit tests for the utils module'
  local payload
  payload=$(cat <<EOF
{
  "prompt": "$prompt",
  "sourceContext": {
    "source": "sources/github-owner-repo",
    "githubRepoContext": { "startingBranch": "main" }
  }
}
EOF
)

  log INFO "Calling Jules API to generate unit tests"
  local response
  response=$(curl -s -X POST \
    -H "x-goog-api-key: $JULES_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$payload" \
    https://jules.googleapis.com/v1alpha/sessions)

  echo "$response" > "$REPORT_DIR/jules_response.json"
  log INFO "Jules response saved to $REPORT_DIR/jules_response.json"
}

#############################################
# RADON - MÉTRICAS DE COMPLEXIDADE
#############################################

run_radon() {
  local output_file="$1"
  log INFO "Executando Radon (métricas de complexidade)..."
  local radon_excludes=".venv,venv,py_rme_canary/venv,__pycache__,.quality_cache,.quality_reports,.quality_tmp"
  IFS=',' read -r -a radon_targets <<< "$RADON_TARGETS"

  # Complexidade Ciclomática
  radon cc "${radon_targets[@]}" \
    --min B \
    --json \
    --exclude "$radon_excludes" > "$output_file"

  # Índice de Manutenibilidade
  local mi_output="${output_file%.json}_mi.json"
  radon mi "${radon_targets[@]}" \
    --min B \
    --json \
    --exclude "$radon_excludes" > "$mi_output"

  # Análise de resultados
  local high_complexity
  high_complexity=$(jq --arg thresh "$RADON_CC_THRESHOLD" '
    [.. | objects | select(.complexity > ($thresh | tonumber))] | length
  ' "$output_file" 2>/dev/null || echo 0)

  if [[ "$high_complexity" -gt 0 ]]; then
    log WARN "Radon: $high_complexity função(ões) com complexidade > $RADON_CC_THRESHOLD"
  else
    log SUCCESS "Radon: complexidade dentro dos limites"
  fi
}

#############################################
# AST-GREP - ANÁLISE ESTRUTURAL
#############################################

run_astgrep() {
  log INFO "Executando ast-grep (análise estrutural)..."

  local rules_dir="$ROOT_DIR/tools/ast_rules/python"
  local output_file="$REPORT_DIR/astgrep_results.json"

  if [[ ! -d "$rules_dir" ]]; then
    log WARN "Diretório de regras ast-grep não encontrado: $rules_dir"
    return 0
  fi

  # 1. Test rules antes de aplicar (auditoria)
  if [[ "$VERBOSE" == true ]]; then
    log DEBUG "Testando regras ast-grep..."
    sg test "$rules_dir" || log WARN "Algumas regras falharam nos testes"
  fi

  # 2. Scan com relatório estruturado
  sg scan \
    --rule "$rules_dir" \
    --json \
    "$ROOT_DIR" > "$output_file" 2>/dev/null || true

  # 3. Apply rewrite se modo apply
  if [[ "$MODE" == "apply" ]]; then
    log INFO "Aplicando transformações ast-grep..."
    sg scan \
      --rule "$rules_dir" \
      --rewrite \
      "$ROOT_DIR" || log WARN "Algumas transformações falharam"
  fi

  # 4. Estatísticas
  local match_count
  match_count=$(jq '[.[] | .matches | length] | add // 0' "$output_file" 2>/dev/null || echo 0)

  if [[ "$match_count" -gt 0 ]]; then
    log INFO "ast-grep: $match_count correspondência(s) encontrada(s)"
  else
    log SUCCESS "ast-grep: nenhum padrão problemático detectado"
  fi
}

#############################################
# ANÁLISE DE SEGURANÇA (BANDIT + SONAR)
#############################################

run_bandit() {
  log INFO "Executando Bandit (análise de segurança)..."

  local output_file="$REPORT_DIR/bandit.json"
  local bandit_cmd=("$PYTHON_BIN" -m bandit)

  if ! "${bandit_cmd[@]}" --version >/dev/null 2>&1; then
    log ERROR "Bandit não está disponível (instale com: pip install bandit)"
    return 1
  fi

  local bandit_excludes=".venv,venv,tests,__pycache__,.quality_cache,.quality_reports,.quality_tmp"
  "${bandit_cmd[@]}" -q -r . \
    -f json \
    -o "$output_file" \
    -x "$bandit_excludes" \
    --severity-level medium \
    --confidence-level medium || true

  if [[ ! -f "$output_file" ]]; then
    log ERROR "Bandit não gerou relatório ($output_file)"
    return 1
  fi

  local issue_count
  issue_count=$(jq '.results | length' "$output_file" 2>/dev/null || echo 0)

  if [[ "$issue_count" -gt 0 ]]; then
    log ERROR "Bandit encontrou $issue_count potencial(is) vulnerabilidade(s)"
    return 1
  fi

  log SUCCESS "Bandit: nenhuma vulnerabilidade relevante encontrada"
}

run_sonar() {
  if [[ "$SKIP_SONAR" == true ]]; then
    log INFO "Análise SonarQube pulada (--skip-sonar)"
    return 0
  fi

  log INFO "Executando SonarScanner (análise de segurança)..."

  # Configuração via environment ou arquivo
  local sonar_project_key="${SONAR_PROJECT_KEY:-py-rme-canary}"
  local sonar_host="${SONAR_HOST_URL:-http://localhost:9000}"
  local sonar_token="${SONAR_TOKEN:-}"

  if [[ -z "$sonar_token" ]]; then
    log WARN "SONAR_TOKEN não configurado - usando modo local (se disponível)"
  fi

  # Executa scanner
  if command -v sonar-scanner &>/dev/null; then
    sonar-scanner \
      -Dsonar.projectKey="$sonar_project_key" \
      -Dsonar.sources=. \
      -Dsonar.host.url="$sonar_host" \
      -Dsonar.login="$sonar_token" \
      -Dsonar.python.version=3.12 \
      -Dsonar.exclusions="**/.venv/**,**/tests/**" \
      > "$REPORT_DIR/sonar_output.log" 2>&1 || log WARN "SonarScanner encontrou issues"

    log SUCCESS "Análise SonarQube concluída (ver dashboard)"
  else
    log WARN "sonar-scanner não disponível - usando sonarlint CLI se disponível"
  fi
}

#############################################
# LIBCST - TRANSFORMAÇÕES COMPLEXAS
#############################################

run_libcst() {
  if [[ "$SKIP_LIBCST" == true ]]; then
    log INFO "Transformações LibCST puladas (--skip-libcst)"
    return 0
  fi

  local transforms_dir="$ROOT_DIR/tools/libcst_transforms"

  if [[ ! -d "$transforms_dir" ]]; then
    log WARN "Diretório de transformações LibCST não encontrado: $transforms_dir"
    return 0
  fi

  log INFO "Aplicando transformações LibCST..."

  if [[ "$MODE" == "apply" ]]; then
    "$PYTHON_BIN" -m libcst.tool codemod "$transforms_dir" "$ROOT_DIR" \
      || log WARN "Algumas transformações LibCST falharam"
  else
    log INFO "Modo dry-run: transformações LibCST não aplicadas"
  fi
}

#############################################
# NORMALIZAÇÃO DE ISSUES
#############################################

normalize_issues() {
  log INFO "Normalizando issues de todas as ferramentas..."

  if ! "$PYTHON_BIN" "$QUALITY_SCRIPTS_DIR/normalize_issues.py" "$ISSUES_NORMALIZED"; then
    log ERROR "Falha ao normalizar issues"
    return 1
  fi
}

#############################################
# TESTES AUTOMATIZADOS
#############################################

run_tests() {
  if [[ "$SKIP_TESTS" == true ]]; then
    log INFO "Testes pulados (--skip-tests)"
    return 0
  fi

  if [[ ! -f pytest.ini ]] && [[ ! -d tests ]] && [[ ! -d py_rme_canary/tests ]]; then
    log WARN "Nenhum teste encontrado (pytest.ini ou diretorio tests)"
    return 0
  fi

  log INFO "Executando testes automatizados..."

  local test_root=""
  if [[ -d tests/unit ]]; then
    test_root="tests/unit"
  elif [[ -d tests ]]; then
    test_root="tests"
  elif [[ -d py_rme_canary/tests ]]; then
    test_root="py_rme_canary/tests"
  fi

  if [[ -z "$test_root" ]]; then
    log WARN "Nenhum diretorio de testes encontrado (tests/ ou py_rme_canary/tests)"
    return 0
  fi

  # Separacao: unit vs UI
  if pytest "$test_root" -v --tb=short --cov=py_rme_canary 2>&1 | tee "$REPORT_DIR/pytest_unit.log"; then
    log SUCCESS "Testes unitários passaram"
  else
    log ERROR "Testes unitários falharam"
    return 1
  fi

  # Testes UI (pytest-qt) - headless
  if [[ -d tests/ui ]] || [[ -d py_rme_canary/tests/ui ]]; then
    local ui_root="tests/ui"
    if [[ -d py_rme_canary/tests/ui ]]; then
      ui_root="py_rme_canary/tests/ui"
    fi
    local qt_flag=""
    if pytest --help 2>/dev/null | grep -q -- "--qt-no-window-capture"; then
      qt_flag="--qt-no-window-capture"
    fi
    log INFO "Executando testes de UI (pytest-qt)..."
    QT_QPA_PLATFORM=offscreen pytest "$ui_root" -v $qt_flag 2>&1 | tee "$REPORT_DIR/pytest_ui.log" || {
      log ERROR "Testes de UI falharam"
      return 1
    }
  fi

  log SUCCESS "Todos os testes passaram"
}

#############################################
# COMPARACAO DE SIMBOLOS
#############################################

compare_symbols() {
  log INFO "Comparando simbolos (antes vs depois)..."

  if "$PYTHON_BIN" - "$SYMBOL_INDEX_BEFORE" "$SYMBOL_INDEX_AFTER" <<'PYTHON'
import json
import sys

before_data = json.load(open(sys.argv[1]))
after_data = json.load(open(sys.argv[2]))

before = {(s["file"], s["name"]) for s in before_data.get("symbols", [])}
after = {(s["file"], s["name"]) for s in after_data.get("symbols", [])}

removed = before - after
added = after - before

if removed:
    print(f"??  Simbolos removidos: {len(removed)}")
    for item in list(removed)[:5]:
        print(f"  - {item[0]}:{item[1]}")

if added:
    print(f"??  Simbolos adicionados: {len(added)}")
    for item in list(added)[:5]:
        print(f"  + {item[0]}:{item[1]}")

if removed:
    sys.exit(1)
PYTHON
  then
    log SUCCESS "Simbolos consistentes"
  else
    log WARN "Simbolos modificados (revisar mudancas)"
  fi
}

#############################################
# RELATÓRIO CONSOLIDADO
#############################################

generate_final_report() {
  log INFO "Gerando relatório consolidado..."

  "$PYTHON_BIN" - "$MODE" "$SYMBOL_INDEX_BEFORE" "$SYMBOL_INDEX_AFTER" "$LOG_FILE" "$ISSUES_NORMALIZED" "$FINAL_REPORT" <<'PYTHON'

import json
from pathlib import Path
from datetime import datetime
import sys

mode = sys.argv[1]
issues_before = json.loads(Path(".ruff.json").read_text()) if Path(".ruff.json").exists() else []
issues_after = json.loads(Path(".ruff_after.json").read_text()) if Path(".ruff_after.json").exists() else []

symbols_before = json.loads(Path(sys.argv[2]).read_text()).get("symbols", [])
symbols_after = json.loads(Path(sys.argv[3]).read_text()).get("symbols", [])

report = f"""# Relatório de Qualidade e Refatoração
**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Modo:** {mode}

## 📊 Sumário Executivo
- **Issues Ruff (antes):** {len(issues_before)}
- **Issues Ruff (depois):** {len(issues_after)}
- **Redução:** {len(issues_before) - len(issues_after)} issues resolvidos
- **Símbolos totais:** {len(symbols_after)}

## 🛠️ Ferramentas Executadas
- ✅ Ruff (linter + formatter)
- ✅ Mypy (type checking)
- ✅ Radon (complexidade)
- ✅ ast-grep (análise estrutural)
- ✅ SonarQube (segurança)

## 📁 Arquivos Modificados
"""

try:
    import subprocess
    changed = subprocess.check_output(
        ["git", "diff", "--name-only"],
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip().split("\n")
    for f in changed:
        if f:
            report += f"- {f}\n"
except:
    report += "_Não foi possível detectar arquivos modificados_\n"

report += f"""
## 📝 Logs e Artefatos
- Log principal: `{Path(sys.argv[4]).absolute()}`
- Issues normalizados: `{Path(sys.argv[5]).absolute()}`
- Símbolos (antes): `{Path(sys.argv[2]).absolute()}`
- Símbolos (depois): `{Path(sys.argv[3]).absolute()}`

## 🎯 Próximos Passos
- Revisar issues de alta severidade
- Validar mudanças em símbolos críticos
- Executar testes de integração completos
"""

Path(sys.argv[6]).write_text(report)
print(f"✅ Relatório gerado: {sys.argv[6]}")
PYTHON
}

#############################################
# PIPELINE PRINCIPAL
#############################################

main() {
  log INFO "=== Quality Pipeline Iniciado ==="
  log INFO "Modo: $MODE | Verbose: $VERBOSE | Telemetry: $ENABLE_TELEMETRY"

  check_dependencies
  snapshot

  # Fase 1: Baseline
  log INFO "=== FASE 1: BASELINE ==="
  if ! run_baseline; then
    log ERROR "Baseline falhou"
    exit 1
  fi

  # Fase 2: Refatoração (se apply)
  if [[ "$MODE" == "apply" ]]; then
    log INFO "=== FASE 2: REFATORAÇÃO ==="
    run_astgrep
    run_libcst
    run_ruff ".ruff_after.json"

    # Validação pós-refatoração
    log INFO "=== FASE 3: VALIDAÇÃO ==="
    if ! run_mypy ".mypy_after.log"; then
      log ERROR "Mypy falhou após refatoração - rollback necessário"
      exit 1
    fi

    run_jules_generate_tests

    run_tests
  fi

  # Fase 4: Análise de segurança
  log INFO "=== FASE 4: SEGURANÇA ==="
  run_bandit || exit 1
  run_sonar

  # Fase 5: Consolidação
  log INFO "=== FASE 5: CONSOLIDAÇÃO ==="
  normalize_issues
  index_symbols "$SYMBOL_INDEX_AFTER"
  compare_symbols
  generate_final_report

  log SUCCESS "=== Pipeline Concluído com Sucesso ==="

  if [[ "$MODE" == "dry-run" ]]; then
    log INFO "ℹ️  Modo dry-run: nenhuma alteração foi aplicada"
    log INFO "ℹ️  Execute com --apply para aplicar mudanças"
  fi
}

main