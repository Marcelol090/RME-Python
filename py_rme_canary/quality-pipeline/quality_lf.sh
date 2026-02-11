#!/usr/bin/env bash
set -Eeuo pipefail

#############################################
# QUALITY PIPELINE v2.3
# Ferramentas Baseline: Ruff, Mypy, Radon, Pyright, Complexipy, Lizard
# Ferramentas Complementar: Pylint, Prospector, Vulture, Skylos, jscpd
# Ferramentas Segurança: Bandit, Semgrep, detect-secrets, Safety, pip-audit, OSV-Scanner
# Ferramentas Docs/Testes: Interrogate, Pydocstyle, Mutmut
# Ferramentas UI/UX: PyAutoGUI, Pywinauto, Lighthouse, Percy, Applitools
# Projeto Local - Sem dependência de SonarQube Server
#############################################

export PYTHONUTF8=1
export TERM="${TERM:-xterm-256color}"
if [[ -n "${PYTHON_BIN+x}" ]]; then
  PYTHON_BIN_USER_SET=true
else
  PYTHON_BIN_USER_SET=false
fi
PYTHON_BIN="${PYTHON_BIN:-python}"

# Windows PATH setup for Python scripts
if [[ "${OS:-}" == "Windows_NT" || "${OSTYPE:-}" == msys* || "${OSTYPE:-}" == cygwin* ]]; then
  PY_SCRIPTS_DIRS="$($PYTHON_BIN -c "import os, site, sysconfig; paths=[sysconfig.get_path('scripts'), sysconfig.get_path('scripts', scheme='nt_user')]; user=site.getuserbase(); paths.append(os.path.join(user, 'Scripts') if user else ''); print('\\n'.join(p for p in paths if p))" 2>/dev/null || echo "")"
  while IFS= read -r PY_SCRIPTS_DIR; do
    if [[ -n "$PY_SCRIPTS_DIR" ]]; then
      if command -v cygpath &>/dev/null; then
        PY_SCRIPTS_DIR="$(cygpath -u "$PY_SCRIPTS_DIR")"
      fi
      export PATH="$PY_SCRIPTS_DIR:$PATH"
    fi
  done <<< "$PY_SCRIPTS_DIRS"
fi

# Detecção automática de diretórios
ROOT_DIR="${ROOT_DIR:-$(pwd)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QUALITY_SCRIPTS_DIR="${QUALITY_SCRIPTS_DIR:-$SCRIPT_DIR/../tools/quality_scripts}"
REPORT_DIR="${REPORT_DIR:-.quality_reports}"
TMP_DIR="${TMP_DIR:-.quality_tmp}"
CACHE_DIR="${CACHE_DIR:-.quality_cache}"
RADON_TARGETS="${RADON_TARGETS:-$ROOT_DIR/py_rme_canary/core,$ROOT_DIR/py_rme_canary/logic_layer}"
PROJECT_DIR="${PROJECT_DIR:-py_rme_canary}"

if [[ ! -d "$PROJECT_DIR" ]]; then
  PROJECT_DIR="."
fi

PROJECT_CORE="${PROJECT_CORE:-$PROJECT_DIR/core}"
PROJECT_LOGIC="${PROJECT_LOGIC:-$PROJECT_DIR/logic_layer}"
PROJECT_VIS="${PROJECT_VIS:-$PROJECT_DIR/vis_layer}"
PROJECT_TESTS="${PROJECT_TESTS:-$PROJECT_DIR/tests}"
QUALITY_HASH_TARGETS="${QUALITY_HASH_TARGETS:-$PROJECT_CORE,$PROJECT_LOGIC,$PROJECT_VIS,$PROJECT_TESTS}"
QUALITY_FAST_HASH="${QUALITY_FAST_HASH:-true}"

SCAN_TARGETS=()
for scan_dir in "$PROJECT_CORE" "$PROJECT_LOGIC" "$PROJECT_VIS" "$PROJECT_TESTS"; do
  if [[ -d "$scan_dir" ]]; then
    SCAN_TARGETS+=("$scan_dir")
  fi
done
if [[ ${#SCAN_TARGETS[@]} -eq 0 ]]; then
  SCAN_TARGETS+=("$PROJECT_DIR")
fi

# Arquivos de relatório
SYMBOL_INDEX_BEFORE="$REPORT_DIR/symbols_before.json"
SYMBOL_INDEX_AFTER="$REPORT_DIR/symbols_after.json"
ISSUES_NORMALIZED="$REPORT_DIR/issues_normalized.json"
FINAL_REPORT="$REPORT_DIR/refactor_summary.md"
LOG_FILE="$REPORT_DIR/quality_$(date +%Y%m%d_%H%M%S).log"
RUN_START_EPOCH="$(date +%s)"

# Configurações de qualidade
RUFF_CONFIG="${RUFF_CONFIG:-pyproject.toml}"
MYPY_CONFIG="${MYPY_CONFIG:-pyproject.toml}"
RADON_CC_THRESHOLD="${RADON_CC_THRESHOLD:-10}"
RADON_MI_THRESHOLD="${RADON_MI_THRESHOLD:-20}"

# Flags de execução
MODE="dry-run"
SKIP_TESTS=false
SKIP_LIBCST=false
SKIP_SECURITY=false
SKIP_SONARLINT=false
SKIP_SECRETS=false
SKIP_DEADCODE=false
SKIP_UI_TESTS=false
SKIP_JULES=false
VERBOSE=false
NO_CACHE=false
PARALLEL_JOBS="$(nproc 2>/dev/null || echo 4)"
TOOL_TIMEOUT=3600
ENABLE_TELEMETRY=false

#############################################
# CORES PARA OUTPUT
#############################################

readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

#############################################
# PARSE ARGUMENTOS
#############################################

usage() {
  cat <<EOF
Uso: $0 [opções]

Quality Pipeline v2.3 - Análise de Código Completa + UI/UX Automation
Ferramentas: Ruff, Mypy, Radon, Pyright, Complexipy, Lizard, Bandit, Semgrep,
detect-secrets, Vulture, Skylos, jscpd, pip-audit, OSV-Scanner, Interrogate,
Pydocstyle, Mutmut, Prospector, PyAutoGUI, Pywinauto, Lighthouse, Percy, Applitools

Opções:
  --apply              Aplica alterações (padrão: dry-run)
  --dry-run            Simula execução sem modificar arquivos
  --skip-tests         Pula execução de testes
  --skip-libcst        Pula transformações LibCST
  --skip-security      Pula análise de segurança (Bandit, Semgrep, pip-audit, OSV-Scanner)
  --skip-sonarlint     Pula análise SonarLint CLI
  --skip-secrets       Pula secret scanning (detect-secrets, gitleaks)
  --skip-deadcode      Pula análise de código morto/duplicado (Vulture, Skylos, jscpd)
  --skip-ui-tests      Pula testes de UI/UX automation (PyAutoGUI, Lighthouse, Percy)
  --skip-jules         Pula integração local Jules (API + suggestions contract)
  --verbose            Saída detalhada
  --full               Executa todas as ferramentas no modo mais completo
  --no-cache           Desabilita cache de resultados
  --jobs N             Define número de jobs paralelos (padrão: nproc)
  --timeout N          Define timeout em segundos para cada ferramenta
  --telemetry          Habilita telemetria (OpenTelemetry)
  --help               Exibe esta ajuda

Exemplos:
  $0 --dry-run --verbose
  $0 --apply --skip-tests
  $0 --apply --skip-secrets --skip-deadcode
  $0 --skip-ui-tests
  $0 --dry-run --skip-ui-tests --skip-jules

Ferramentas por fase:
  Fase 1 (Baseline):     Ruff, Mypy, Radon, Pyright, Complexipy, Lizard
  Fase 2 (Refatoração):  ast-grep, LibCST
  Fase 3 (Complementar): Pylint, Prospector, Vulture, Skylos, jscpd
  Fase 4 (Segurança):    Bandit, Semgrep, detect-secrets, pip-audit, OSV-Scanner, Safety
  Fase 5 (Docs/Testes):  Interrogate, Pydocstyle, Mutmut
  Fase 6 (UI/UX):        PyAutoGUI, Pywinauto, Lighthouse, Percy, Applitools
  Fase 7 (Consolidação): Relatório final + Jules suggestions
EOF
}

while [[ $# -gt 0 ]]; do
  arg="${1%$'\r'}"
  case "$arg" in
    --apply) MODE="apply" ;;
    --dry-run) MODE="dry-run" ;;
    --skip-tests) SKIP_TESTS=true ;;
    --skip-libcst) SKIP_LIBCST=true ;;
    --skip-security) SKIP_SECURITY=true ;;
    --skip-sonarlint) SKIP_SONARLINT=true ;;
    --skip-secrets) SKIP_SECRETS=true ;;
    --skip-deadcode) SKIP_DEADCODE=true ;;
    --skip-ui-tests) SKIP_UI_TESTS=true ;;
    --skip-jules) SKIP_JULES=true ;;
    --verbose) VERBOSE=true ;;
    --full) : ;;
    --no-cache) NO_CACHE=true ;;
    --jobs) shift; PARALLEL_JOBS="$1" ;;
    --timeout) shift; TOOL_TIMEOUT="$1" ;;
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
    INFO)    echo -e "${CYAN}[INFO]${NC}    [$timestamp] $message" | tee -a "$LOG_FILE" ;;
    WARN)    echo -e "${YELLOW}[WARN]${NC}    [$timestamp] $message" | tee -a "$LOG_FILE" ;;
    ERROR)   echo -e "${RED}[ERROR]${NC}   [$timestamp] $message" | tee -a "$LOG_FILE" ;;
    SUCCESS) echo -e "${GREEN}[✓]${NC}       [$timestamp] $message" | tee -a "$LOG_FILE" ;;
    DEBUG)   [[ "$VERBOSE" == true ]] && echo -e "${BLUE}[DEBUG]${NC}   [$timestamp] $message" | tee -a "$LOG_FILE" ;;
  esac

  if [[ "$ENABLE_TELEMETRY" == true ]]; then
    echo "{\"level\":\"$level\",\"timestamp\":\"$timestamp\",\"message\":\"$message\"}" >> "$REPORT_DIR/telemetry.jsonl"
  fi
}

# Performance tracking
declare -A TOOL_TIMES
PERFORMANCE_LOG="$REPORT_DIR/performance.log"

start_timer() {
  local tool_name="$1"
  TOOL_TIMES["${tool_name}_start"]=$(date +%s)
  log DEBUG "⏱️  Iniciando $tool_name"
}

end_timer() {
  local tool_name="$1"
  local start_time="${TOOL_TIMES[${tool_name}_start]}"

  if [[ -n "$start_time" ]]; then
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))
    TOOL_TIMES["${tool_name}_duration"]=$duration

    # Log performance
    echo "$(date '+%Y-%m-%d %H:%M:%S') | $tool_name | ${duration}s" >> "$PERFORMANCE_LOG"

    if [[ $duration -lt 10 ]]; then
      log DEBUG "✓ $tool_name completou em ${duration}s"
    elif [[ $duration -lt 60 ]]; then
      log INFO "⏱️  $tool_name completou em ${duration}s"
    else
      local minutes=$((duration / 60))
      local seconds=$((duration % 60))
      log WARN "⏱️  $tool_name demorou ${minutes}m${seconds}s"
    fi
  fi
}

# Execute with timeout wrapper
run_with_timeout() {
  local timeout_duration="$1"
  shift
  local tool_name="$1"
  shift

  if command -v timeout &>/dev/null; then
    timeout "$timeout_duration" "$@" || {
      local exit_code=$?
      if [[ $exit_code -eq 124 ]]; then
        log ERROR "$tool_name excedeu timeout de ${timeout_duration}s"
        return 124
      fi
      return $exit_code
    }
  else
    # Fallback sem timeout
    "$@"
  fi
}

# Prefer uv when available for faster installs
if command -v uv &>/dev/null; then
  log INFO "Usando uv (fast mode)"
else
  log INFO "Usando pip (standard mode)"
fi

#############################################
# DEPENDÊNCIAS - VALIDAÇÃO AVANÇADA
#############################################

require() {
  local cmd="$1"
  local install_hint="${2:-}"

  if [[ "$cmd" == "python" ]]; then
    # In Git Bash/MSYS on Windows, prefer python.exe to avoid older /usr/bin/python3.
    if [[ "$PYTHON_BIN_USER_SET" != true ]] && [[ "${OS:-}" == "Windows_NT" || "${OSTYPE:-}" == msys* || "${OSTYPE:-}" == cygwin* ]]; then
      if command -v python.exe &>/dev/null; then
        PYTHON_BIN="python.exe"
        log DEBUG "python resolvido para: $(command -v python.exe)"
        return 0
      fi
    fi

    if command -v "$PYTHON_BIN" &>/dev/null; then
      log DEBUG "python resolvido para: $(command -v "$PYTHON_BIN")"
      return 0
    fi

    # Prefer python3 in Unix-like shells only when user did not explicitly choose PYTHON_BIN.
    if [[ "$PYTHON_BIN_USER_SET" != true ]] && command -v python3 &>/dev/null; then
      PYTHON_BIN="python3"
      log DEBUG "python resolvido para: $(command -v python3)"
      return 0
    fi
  fi

  if command -v "$cmd" &>/dev/null; then
    log DEBUG "$cmd encontrado: $(command -v "$cmd")"
    return 0
  fi

  if command -v "${cmd}.exe" &>/dev/null; then
    log DEBUG "$cmd encontrado: $(command -v "${cmd}.exe")"
    if [[ "$cmd" == "python" ]]; then
      # Only bind to *.exe in native Windows-like shells.
      if [[ "${OS:-}" == "Windows_NT" || "${OSTYPE:-}" == msys* || "${OSTYPE:-}" == cygwin* ]]; then
        PYTHON_BIN="${cmd}.exe"
      fi
    fi
    return 0
  fi

  log WARN "Dependência opcional ausente: $cmd"
  [[ -n "$install_hint" ]] && log INFO "  Instalação: $install_hint"
  return 1
}

check_dependencies() {
  log INFO "Verificando dependências do sistema..."

  local missing=0

  # Obrigatórias
  require python "https://python.org" || ((missing++))
  require git "apt install git / brew install git" || ((missing++))

  # Ferramentas de qualidade (preferir python -m para respeitar PYTHON_BIN)
  if ! "$PYTHON_BIN" -m ruff --version &>/dev/null 2>&1; then
    log WARN "Dependência opcional ausente: ruff"
    log INFO "  Instalação: pip install ruff"
  fi
  if ! "$PYTHON_BIN" -m mypy --version &>/dev/null 2>&1; then
    log WARN "Dependência opcional ausente: mypy"
    log INFO "  Instalação: pip install mypy"
  fi
  if ! "$PYTHON_BIN" -m radon --version &>/dev/null 2>&1; then
    log WARN "Dependência opcional ausente: radon"
    log INFO "  Instalação: pip install radon"
  fi

  # Ferramentas de segurança
  if [[ "$SKIP_SECURITY" == false ]]; then
    if ! "$PYTHON_BIN" -m bandit --version &>/dev/null 2>&1; then
      log WARN "Bandit não encontrado - análise de segurança parcial"
      log INFO "  Instalação: pip install bandit"
    fi

    # Safety para vulnerabilidades em dependências
    if ! "$PYTHON_BIN" -m safety --version &>/dev/null 2>&1; then
      log WARN "Safety não encontrado - instale com: pip install safety"
    else
      log DEBUG "Safety disponível para verificação de dependências"
    fi
  fi

  # SonarLint CLI (opcional - projeto local)
  if [[ "$SKIP_SONARLINT" == false ]]; then
    if command -v sonarlint &>/dev/null || command -v sonarlint-ls-cli &>/dev/null; then
      log INFO "SonarLint CLI disponível para análise local"
    else
      log WARN "SonarLint CLI não encontrado"
      log INFO "  Para instalar sonarlint-ls-cli:"
      log INFO "    pip install sonarlint-ls-cli"
      log INFO "  Ou via Docker:"
      log INFO "    docker run --rm -v \$(pwd):/src sonarsource/sonarlint-cli"
      SKIP_SONARLINT=true
    fi
  fi

  # Pylint (opcional - regras adicionais)
  if "$PYTHON_BIN" -m pylint --version &>/dev/null 2>&1; then
    log DEBUG "Pylint disponível para análise complementar"
  else
    log DEBUG "Pylint não encontrado (opcional)"
  fi

  # AST-Grep (opcional)
  require sg "cargo install ast-grep" || log DEBUG "ast-grep não disponível"

  if [[ $missing -gt 0 ]]; then
    log ERROR "$missing dependência(s) crítica(s) ausente(s)"
    exit 1
  fi

  # GNU Parallel para execução paralela
  if command -v parallel &>/dev/null; then
    log INFO "GNU Parallel disponível"
  else
    log DEBUG "GNU Parallel não encontrado - execução sequencial"
  fi

  log SUCCESS "Dependências verificadas"
}

#############################################
# ROLLBACK AUTOMÁTICO
#############################################

ROLLBACK_STASH="quality-rollback-$(date +%s)"
ROLLBACK_COMMIT=""
ROLLBACK_ACTIVE=false

snapshot() {
  if [[ "$MODE" == "apply" ]]; then
    log INFO "Criando snapshot git para rollback..."

    if ! git rev-parse --is-inside-work-tree &>/dev/null; then
      log WARN "Repositório git não detectado - rollback desabilitado"
      return 0
    fi

    ROLLBACK_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "")

    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
      log WARN "Mudanças não commitadas - criando stash..."
      git add -A
      git stash push -u -m "$ROLLBACK_STASH" --quiet
      ROLLBACK_ACTIVE=true
    fi

    log SUCCESS "Snapshot criado (commit: ${ROLLBACK_COMMIT:0:8})"
  fi
}

rollback() {
  if [[ "$ROLLBACK_ACTIVE" == false ]]; then
    return 0
  fi

  if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    return 0
  fi

  log ERROR "Erro detectado - iniciando rollback..."

  if [[ -n "$ROLLBACK_COMMIT" ]]; then
    git reset --hard "$ROLLBACK_COMMIT" 2>/dev/null && {
      log SUCCESS "Rollback via git reset concluído"
      return 0
    }
  fi

  if git stash list | grep -q "$ROLLBACK_STASH"; then
    git stash pop --index --quiet 2>/dev/null && {
      log SUCCESS "Rollback via git stash concluído"
      return 0
    }
  fi

  git reset --hard HEAD
  exit 1
}

trap rollback ERR

#############################################
# INDEXADOR DE SÍMBOLOS
#############################################

index_symbols() {
  local output="$1"
  log INFO "Indexando símbolos → $output"

  local symbols_cache_file="$CACHE_DIR/symbols_index.json"
  if cache_hit "symbols_index" "$symbols_cache_file"; then
    cp "$symbols_cache_file" "$output" 2>/dev/null || true
    log SUCCESS "Símbolos: cache hit"
    return 0
  fi

  if [[ -d "$QUALITY_SCRIPTS_DIR" ]] && [[ -f "$QUALITY_SCRIPTS_DIR/index_symbols.py" ]]; then
    if ! "$PYTHON_BIN" "$QUALITY_SCRIPTS_DIR/index_symbols.py" "$output" "${SCAN_TARGETS[@]}" 2>/dev/null; then
      log WARN "Falha ao indexar símbolos - continuando..."
      echo '{"symbols":[]}' > "$output"
    else
      cp "$output" "$symbols_cache_file" 2>/dev/null || true
      cache_mark "symbols_index"
    fi
  else
    log DEBUG "Script de indexação não encontrado - criando índice vazio"
    echo '{"symbols":[]}' > "$output"
  fi
}

#############################################
# CACHE DE EXECUÇÃO
#############################################

SOURCE_HASH=""

_compute_source_hash() {
  local -a hash_targets=()
  local targets_csv="$QUALITY_HASH_TARGETS"

  if [[ -n "$targets_csv" ]]; then
    IFS=',' read -r -a hash_targets <<< "$targets_csv"
  fi
  if [[ ${#hash_targets[@]} -eq 0 ]]; then
    hash_targets=("${SCAN_TARGETS[@]}")
  fi

  if [[ "$QUALITY_FAST_HASH" == "true" ]] && git -C "$ROOT_DIR" rev-parse --is-inside-work-tree &>/dev/null; then
    local head_sha=""
    head_sha=$(git -C "$ROOT_DIR" rev-parse HEAD 2>/dev/null || true)
    if [[ -n "$head_sha" ]]; then
      local -a git_targets=()
      local target=""
      for target in "${hash_targets[@]}"; do
        [[ -n "$target" ]] || continue
        if [[ "$target" == "$ROOT_DIR"* ]]; then
          target="${target#"$ROOT_DIR"/}"
        fi
        git_targets+=("$target")
      done

      local dirty=""
      if [[ ${#git_targets[@]} -gt 0 ]]; then
        dirty=$(git -C "$ROOT_DIR" status --porcelain -- "${git_targets[@]}" 2>/dev/null || true)
      else
        dirty=$(git -C "$ROOT_DIR" status --porcelain 2>/dev/null || true)
      fi

      local git_hash=""
      git_hash=$(printf "%s\n%s\n" "$head_sha" "$dirty" | md5sum 2>/dev/null | cut -d' ' -f1)
      if [[ -n "$git_hash" ]]; then
        echo "$git_hash"
        return 0
      fi
    fi
  fi

  if [[ -f "$QUALITY_SCRIPTS_DIR/hash_python.py" ]]; then
    local py_hash=""
    local -a hash_cmd=("$PYTHON_BIN" "$QUALITY_SCRIPTS_DIR/hash_python.py" --mode metadata)
    hash_cmd+=("${hash_targets[@]}")
    py_hash=$("${hash_cmd[@]}" 2>/dev/null || true)
    if [[ -n "$py_hash" ]]; then
      echo "$py_hash"
      return 0
    fi
  fi

  local current_hash
  current_hash=$(
    for target in "${hash_targets[@]}"; do
      [[ -n "$target" ]] || continue
      [[ -e "$target" ]] || continue
      find "$target" -type f \( -name "*.py" -o -name "pyproject.toml" -o -name "pytest.ini" -o -name "setup.py" \) \
        -not -path "*/__pycache__/*" \
        -not -path "*/.venv/*" \
        -not -path "*/venv/*" \
        -not -path "*/.quality_cache/*" \
        -not -path "*/.quality_reports/*" \
        -not -path "*/.quality_tmp/*" \
        -exec md5sum {} \; 2>/dev/null
    done | sort | md5sum 2>/dev/null | cut -d' ' -f1
  )

  if [[ -z "$current_hash" ]]; then
    echo "no-hash"
  else
    echo "$current_hash"
  fi
}

get_source_hash() {
  if [[ -z "$SOURCE_HASH" ]]; then
    SOURCE_HASH=$(_compute_source_hash)
  fi
  echo "$SOURCE_HASH"
}

cache_hit() {
  local cache_key="$1"
  shift
  local cache_file="$CACHE_DIR/${cache_key}.hash"
  local output_files=("$@")

  if [[ "$NO_CACHE" == true ]] || [[ "$MODE" != "dry-run" ]]; then
    return 1
  fi

  local current_hash
  current_hash=$(get_source_hash)
  if [[ "$current_hash" == "no-hash" ]]; then
    return 1
  fi

  local previous_hash=""
  [[ -f "$cache_file" ]] && previous_hash=$(cat "$cache_file")

  if [[ "$current_hash" != "$previous_hash" ]]; then
    return 1
  fi

  local output_file
  for output_file in "${output_files[@]}"; do
    if [[ ! -f "$output_file" ]]; then
      return 1
    fi
  done

  log INFO "Cache HIT para $cache_key"
  return 0
}

cache_mark() {
  local cache_key="$1"
  local cache_file="$CACHE_DIR/${cache_key}.hash"

  if [[ "$NO_CACHE" == true ]] || [[ "$MODE" != "dry-run" ]]; then
    return 0
  fi

  local current_hash
  current_hash=$(get_source_hash)
  if [[ "$current_hash" == "no-hash" ]]; then
    return 0
  fi

  echo "$current_hash" > "$cache_file"
}

#############################################
# RUFF - LINTER + FORMATTER
#############################################

run_ruff() {
  local output_file="${1:-.ruff.json}"
  start_timer "Ruff"
  log INFO "Executando Ruff (linter + formatter)..."

  local ruff_select="F,E,W,I,N,UP,B,C4,SIM,PERF,PL,RUF,S"
  local cache_key="ruff_${MODE}"

  if cache_hit "$cache_key" "$output_file"; then
    local cached_issue_count
    cached_issue_count=$(jq 'length' "$output_file" 2>/dev/null || echo 0)
    if [[ "$cached_issue_count" -eq 0 ]]; then
      log SUCCESS "Ruff (cache): nenhum issue encontrado"
    else
      log WARN "Ruff (cache): $cached_issue_count issue(s) detectado(s)"
    fi
    end_timer "Ruff"
    return 0
  fi

  if [[ "$MODE" == "dry-run" ]]; then
    run_with_timeout "$TOOL_TIMEOUT" "ruff-check" \
      "$PYTHON_BIN" -m ruff check "${SCAN_TARGETS[@]}" --select "$ruff_select" --config "$RUFF_CONFIG" --exit-zero --output-format=json \
      > "$output_file" 2>/dev/null || true
  else
    log INFO "Aplicando correções automáticas..."
    run_with_timeout "$TOOL_TIMEOUT" "ruff-check-fix" \
      "$PYTHON_BIN" -m ruff check "${SCAN_TARGETS[@]}" --select "$ruff_select" --config "$RUFF_CONFIG" --fix --exit-zero --output-format=json \
      > "$output_file" 2>/dev/null || true
    log INFO "Formatando código..."
    run_with_timeout "$TOOL_TIMEOUT" "ruff-format" "$PYTHON_BIN" -m ruff format "${SCAN_TARGETS[@]}" --config "$RUFF_CONFIG" 2>/dev/null || true
  fi

  local issue_count
  issue_count=$(jq 'length' "$output_file" 2>/dev/null || echo 0)

  if [[ "$issue_count" -eq 0 ]]; then
    log SUCCESS "Ruff: nenhum issue encontrado"
  else
    log WARN "Ruff: $issue_count issue(s) detectado(s)"
  fi
  cache_mark "$cache_key"
  end_timer "Ruff"
}

#############################################
# MYPY - TYPE CHECKING
#############################################

run_mypy() {
  local output_file="${1:-.mypy_baseline.log}"
  start_timer "Mypy"
  log INFO "Executando Mypy (type checking)..."
  local cache_key="mypy_${MODE}"
  local py_version
  py_version="$("$PYTHON_BIN" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")"
  local py_major="${py_version%%.*}"
  local py_minor="${py_version#*.}"

  if [[ "$py_major" -lt 3 ]] || [[ "$py_major" -eq 3 && "$py_minor" -lt 12 ]]; then
    cat > "$output_file" <<EOF
Mypy skipped: Python >= 3.12 required by project syntax.
Resolved interpreter: $PYTHON_BIN ($py_version)
Tip: run with PYTHON_BIN=<python-3.12-bin> for full type checking.
EOF
    log WARN "Mypy pulado: Python >= 3.12 requerido (atual: $py_version)"
    cache_mark "$cache_key"
    end_timer "Mypy"
    return 0
  fi

  if cache_hit "$cache_key" "$output_file"; then
    local cached_errors
    cached_errors=$(grep -c "error:" "$output_file" 2>/dev/null || true)
    cached_errors="${cached_errors:-0}"
    if [[ "$cached_errors" -gt 0 ]]; then
      log WARN "Mypy (cache): erros de tipagem detectados"
      end_timer "Mypy"
      return 1
    fi
    log SUCCESS "Mypy (cache): tipagem validada"
    end_timer "Mypy"
    return 0
  fi

  local mypy_cache="$CACHE_DIR/mypy_cache"
  mkdir -p "$mypy_cache"

  local mypy_targets=""
  [[ -d "$PROJECT_CORE" ]] && mypy_targets="$PROJECT_CORE"
  [[ -d "$PROJECT_LOGIC" ]] && mypy_targets="$mypy_targets $PROJECT_LOGIC"
  [[ -d "$PROJECT_VIS" ]] && mypy_targets="$mypy_targets $PROJECT_VIS"

  if [[ -z "$mypy_targets" ]]; then
    log WARN "Nenhum diretório para análise Mypy"
    return 0
  fi

  # shellcheck disable=SC2086
  if run_with_timeout "$TOOL_TIMEOUT" "mypy" \
    "$PYTHON_BIN" -m mypy $mypy_targets \
    --config-file "$MYPY_CONFIG" \
    --cache-dir "$mypy_cache" \
    --no-error-summary \
    --show-column-numbers \
    --show-error-codes \
    > "$output_file" 2>&1; then
    cat "$output_file"
    log SUCCESS "Mypy: tipagem validada"
    cache_mark "$cache_key"
    end_timer "Mypy"
    return 0
  else
    [[ -f "$output_file" ]] && cat "$output_file"
    log WARN "Mypy: erros de tipagem detectados"
    cache_mark "$cache_key"
    end_timer "Mypy"
    return 1
  fi
}

#############################################
# PYLINT - ANÁLISE COMPLEMENTAR
#############################################

run_pylint() {
  start_timer "Pylint"
  log INFO "Executando Pylint (análise complementar)..."

  if ! "$PYTHON_BIN" -m pylint --version &>/dev/null 2>&1; then
    log DEBUG "Pylint não disponível - pulando"
    end_timer "Pylint"
    return 0
  fi

  local output_file="$REPORT_DIR/pylint.json"
  local cache_key="pylint"

  if cache_hit "$cache_key" "$output_file"; then
    local cached_issue_count
    cached_issue_count=$(jq 'length' "$output_file" 2>/dev/null || echo 0)
    if [[ "$cached_issue_count" -gt 0 ]]; then
      log INFO "Pylint (cache): $cached_issue_count issue(s) encontrado(s)"
    else
      log SUCCESS "Pylint (cache): nenhum issue"
    fi
    end_timer "Pylint"
    return 0
  fi

  run_with_timeout "$TOOL_TIMEOUT" "pylint" \
    "$PYTHON_BIN" -m pylint "$PROJECT_DIR" \
      --output-format=json \
      --jobs "$PARALLEL_JOBS" \
      --exit-zero \
      --disable=C0114,C0115,C0116 \
      > "$output_file" 2>/dev/null || true

  local issue_count
  issue_count=$(jq 'length' "$output_file" 2>/dev/null || echo 0)

  if [[ "$issue_count" -gt 0 ]]; then
    log INFO "Pylint: $issue_count issue(s) encontrado(s)"
  else
    log SUCCESS "Pylint: nenhum issue"
  fi
  cache_mark "$cache_key"
  end_timer "Pylint"
}

#############################################
# RADON - COMPLEXIDADE
#############################################

run_radon() {
  local output_file="${1:-.radon.json}"
  start_timer "Radon"
  log INFO "Executando Radon (complexidade)..."
  local cache_key="radon"
  local mi_output="${output_file%.json}_mi.json"

  if cache_hit "$cache_key" "$output_file" "$mi_output"; then
    local cached_high_complexity
    cached_high_complexity=$(jq --arg thresh "$RADON_CC_THRESHOLD" '[.. | objects | select(.complexity > ($thresh | tonumber))] | length' "$output_file" 2>/dev/null || echo 0)
    if [[ "$cached_high_complexity" -gt 0 ]]; then
      log WARN "Radon (cache): $cached_high_complexity função(ões) com complexidade > $RADON_CC_THRESHOLD"
    else
      log SUCCESS "Radon (cache): complexidade dentro dos limites"
    fi
    end_timer "Radon"
    return 0
  fi

  local radon_excludes=".venv,venv,__pycache__,.quality_cache,.quality_reports,.quality_tmp"
  IFS=',' read -r -a radon_targets <<< "$RADON_TARGETS"

  run_with_timeout "$TOOL_TIMEOUT" "radon-cc" \
    "$PYTHON_BIN" -m radon cc "${radon_targets[@]}" --min B --json --exclude "$radon_excludes" > "$output_file" 2>/dev/null || true
  run_with_timeout "$TOOL_TIMEOUT" "radon-mi" \
    "$PYTHON_BIN" -m radon mi "${radon_targets[@]}" --min B --json --exclude "$radon_excludes" > "$mi_output" 2>/dev/null || true

  local high_complexity
  high_complexity=$(jq --arg thresh "$RADON_CC_THRESHOLD" '[.. | objects | select(.complexity > ($thresh | tonumber))] | length' "$output_file" 2>/dev/null || echo 0)

  if [[ "$high_complexity" -gt 0 ]]; then
    log WARN "Radon: $high_complexity função(ões) com complexidade > $RADON_CC_THRESHOLD"
  else
    log SUCCESS "Radon: complexidade dentro dos limites"
  fi
  cache_mark "$cache_key"
  end_timer "Radon"
}

#############################################
# BANDIT - SEGURANÇA
#############################################

run_bandit() {
  if [[ "$SKIP_SECURITY" == true ]]; then
    log INFO "Análise Bandit pulada (--skip-security)"
    return 0
  fi

  log INFO "Executando Bandit (segurança)..."

  local output_file="$REPORT_DIR/bandit.json"

  if ! "$PYTHON_BIN" -m bandit --version &>/dev/null 2>&1; then
    log WARN "Bandit não disponível"
    return 0
  fi

  local bandit_excludes=".venv,venv,tests,__pycache__,.quality_cache,.quality_reports,.quality_tmp"
  run_with_timeout "$TOOL_TIMEOUT" "bandit" \
    "$PYTHON_BIN" -m bandit -q -r "$PROJECT_DIR" \
      -f json \
      -o "$output_file" \
      -x "$bandit_excludes" \
      --severity-level medium \
      --confidence-level medium 2>/dev/null || true

  if [[ ! -f "$output_file" ]]; then
    log WARN "Bandit não gerou relatório"
    return 0
  fi

  local issue_count
  issue_count=$(jq '.results | length' "$output_file" 2>/dev/null || echo 0)

  if [[ "$issue_count" -gt 0 ]]; then
    log WARN "Bandit: $issue_count potencial(is) vulnerabilidade(s)"
  else
    log SUCCESS "Bandit: nenhuma vulnerabilidade"
  fi
}

#############################################
# SAFETY - VULNERABILIDADES EM DEPENDÊNCIAS
#############################################

run_safety() {
  if [[ "$SKIP_SECURITY" == true ]]; then
    log INFO "Análise Safety pulada (--skip-security)"
    return 0
  fi

  log INFO "Executando Safety (vulnerabilidades em dependências)..."

  if ! "$PYTHON_BIN" -m safety --version &>/dev/null 2>&1; then
    log WARN "Safety não disponível - instale com: pip install safety"
    return 0
  fi

  local output_file="$REPORT_DIR/safety.json"

  if run_with_timeout "$TOOL_TIMEOUT" "safety" "$PYTHON_BIN" -m safety check --json > "$output_file" 2>/dev/null; then
    log SUCCESS "Safety: nenhuma vulnerabilidade conhecida"
  else
    local vuln_count
    vuln_count=$(jq 'length' "$output_file" 2>/dev/null || echo 0)
    log WARN "Safety: $vuln_count vulnerabilidade(s) em dependências"
    log INFO "  Revise $output_file para detalhes"
  fi
}

#############################################
# SONARLINT CLI - ANÁLISE LOCAL
#############################################

run_sonarlint() {
  if [[ "$SKIP_SONARLINT" == true ]]; then
    log INFO "SonarLint pulado (--skip-sonarlint)"
    return 0
  fi

  log INFO "Executando SonarLint CLI (análise local)..."

  local output_file="$REPORT_DIR/sonarlint.json"

  # Tenta sonarlint-ls-cli primeiro
  if command -v sonarlint-ls-cli &>/dev/null; then
    log DEBUG "Usando sonarlint-ls-cli"
    sonarlint-ls-cli analyze \
      --src "$PROJECT_DIR" \
      --output "$output_file" \
      --format json 2>/dev/null || {
      log WARN "sonarlint-ls-cli falhou"
      return 0
    }
  elif command -v sonarlint &>/dev/null; then
    log DEBUG "Usando sonarlint CLI"
    sonarlint \
      --src "$PROJECT_DIR" \
      --output "$output_file" 2>/dev/null || {
      log WARN "sonarlint CLI falhou"
      return 0
    }
  else
    log WARN "SonarLint CLI não disponível"
    log INFO "  Instalação via pip: pip install sonarlint-ls-cli"
    log INFO "  Instalação via Docker: docker pull sonarsource/sonarlint-cli"
    return 0
  fi

  if [[ -f "$output_file" ]]; then
    local issue_count
    issue_count=$(jq 'length' "$output_file" 2>/dev/null || echo 0)
    if [[ "$issue_count" -gt 0 ]]; then
      log INFO "SonarLint: $issue_count issue(s) encontrado(s)"
    else
      log SUCCESS "SonarLint: nenhum issue"
    fi
  fi
}

#############################################
# DETECT-SECRETS - SECRET SCANNING
#############################################

run_detect_secrets() {
  if [[ "$SKIP_SECURITY" == true ]]; then
    log INFO "Detect-secrets pulado (--skip-security)"
    return 0
  fi

  log INFO "Executando detect-secrets (secret scanning)..."

  local output_file="$REPORT_DIR/secrets.json"

  # Tenta detect-secrets primeiro
  if command -v detect-secrets &>/dev/null; then
    run_with_timeout "$TOOL_TIMEOUT" "detect-secrets" detect-secrets scan "$PROJECT_DIR" \
      --exclude-files '\.git/.*' \
      --exclude-files '\.venv/.*' \
      --exclude-files 'venv/.*' \
      --exclude-files '__pycache__/.*' \
      --exclude-files '\.quality_.*' \
      --exclude-files '^awesome-copilot/.*' \
      --exclude-files '^remeres-map-editor-redux/.*' \
      --exclude-files '.*\.(otbm|otb|xml|json|spr|dat|pic|png|jpg|jpeg|gif|bmp|tiff|ico)$' \
      > "$output_file" 2>/dev/null || true

    local secret_count
    secret_count=$(jq '.results | to_entries | map(.value | length) | add // 0' "$output_file" 2>/dev/null || echo 0)

    if [[ "$secret_count" -gt 0 ]]; then
      log ERROR "detect-secrets: $secret_count segredo(s) potencial(is) encontrado(s)!"
      log INFO "  Revise $output_file e use 'detect-secrets audit' para verificar"
    else
      log SUCCESS "detect-secrets: nenhum segredo detectado"
    fi
  # Fallback para gitleaks
  elif command -v gitleaks &>/dev/null; then
    log DEBUG "Usando gitleaks como alternativa"
    run_with_timeout "$TOOL_TIMEOUT" "gitleaks" gitleaks detect \
      --source "$PROJECT_DIR" \
      --report-format json \
      --report-path "$output_file" \
      --no-git 2>/dev/null || true

    if [[ -f "$output_file" ]]; then
      local secret_count
      secret_count=$(jq 'length' "$output_file" 2>/dev/null || echo 0)
      if [[ "$secret_count" -gt 0 ]]; then
        log ERROR "gitleaks: $secret_count segredo(s) encontrado(s)!"
      else
        log SUCCESS "gitleaks: nenhum segredo detectado"
      fi
    fi
  else
    log WARN "Nenhuma ferramenta de secret scanning disponível"
    log INFO "  Instale: pip install detect-secrets"
    log INFO "  Ou: brew install gitleaks / go install github.com/gitleaks/gitleaks/v8@latest"
  fi
}

#############################################
# SEMGREP - ANÁLISE DE PADRÕES
#############################################

run_semgrep() {
  if [[ "$SKIP_SECURITY" == true ]]; then
    log INFO "Semgrep pulado (--skip-security)"
    return 0
  fi

  log INFO "Executando Semgrep (análise de padrões)..."

  if ! command -v semgrep &>/dev/null; then
    log WARN "Semgrep não disponível - instale com: pip install semgrep"
    return 0
  fi

  local output_file="$REPORT_DIR/semgrep.json"
  local rules_dir="$ROOT_DIR/tools/semgrep_rules"

  # Usa regras customizadas se existirem, senão usa auto
  local -a rule_config=("--config" "auto")
  if [[ -d "$rules_dir" ]]; then
    rule_config=("--config" "$rules_dir")
    log DEBUG "Usando regras customizadas de $rules_dir"
  fi

  # Regras para Python/Django/Flask/FastAPI
  run_with_timeout "$TOOL_TIMEOUT" "semgrep" semgrep scan \
    "${rule_config[@]}" \
    --json \
    --output "$output_file" \
    --exclude '.venv' \
    --exclude 'venv' \
    --exclude '__pycache__' \
    --exclude '.quality_*' \
    --metrics off \
    "${SCAN_TARGETS[@]}" 2>/dev/null || true

  if [[ -f "$output_file" ]]; then
    local issue_count
    issue_count=$(jq '.results | length' "$output_file" 2>/dev/null || echo 0)
    local error_count
    error_count=$(jq '[.results[] | select(.extra.severity == "ERROR")] | length' "$output_file" 2>/dev/null || echo 0)

    if [[ "$error_count" -gt 0 ]]; then
      log ERROR "Semgrep: $error_count erro(s) crítico(s) encontrado(s)"
    elif [[ "$issue_count" -gt 0 ]]; then
      log WARN "Semgrep: $issue_count issue(s) encontrado(s)"
    else
      log SUCCESS "Semgrep: nenhum padrão problemático"
    fi
  fi
}

#############################################
# VULTURE - CÓDIGO MORTO
#############################################

run_vulture() {
  log INFO "Executando Vulture (código morto)..."

  if ! "$PYTHON_BIN" -m vulture --version &>/dev/null 2>&1; then
    log WARN "Vulture não disponível - instale com: pip install vulture"
    return 0
  fi

  local output_file="$REPORT_DIR/vulture.txt"
  local whitelist="$ROOT_DIR/.vulture_whitelist.py"

  local vulture_args=("${SCAN_TARGETS[@]}" "--min-confidence" "80")
  if [[ -f "$whitelist" ]]; then
    vulture_args+=("$whitelist")
  fi

  run_with_timeout "$TOOL_TIMEOUT" "vulture" "$PYTHON_BIN" -m vulture "${vulture_args[@]}" > "$output_file" 2>/dev/null || true

  if [[ -s "$output_file" ]]; then
    local dead_code_count
    dead_code_count=$(wc -l < "$output_file" | tr -d ' ')
    log WARN "Vulture: $dead_code_count item(ns) de código morto detectado(s)"
    log INFO "  Revise $output_file para detalhes"
    log INFO "  Para ignorar falsos positivos, adicione ao .vulture_whitelist.py"
  else
    log SUCCESS "Vulture: nenhum código morto detectado"
  fi
}

#############################################
# JSCPD - CÓDIGO DUPLICADO
#############################################

run_jscpd() {
  log INFO "Executando jscpd (código duplicado)..."

  if ! command -v jscpd &>/dev/null; then
    log WARN "jscpd não disponível - instale com: npm install -g jscpd"
    return 0
  fi

  local output_file="$REPORT_DIR/jscpd.json"

  run_with_timeout "$TOOL_TIMEOUT" "jscpd" jscpd "${SCAN_TARGETS[@]}" \
    --reporters json \
    --output "$REPORT_DIR" \
    --ignore '**/venv/**,**/__pycache__/**,**/.venv/**,**/tests/**,**/*.json,**/*.xml,**/*.otbm,**/*.otb' \
    --min-lines 10 \
    --min-tokens 50 \
    --format python \
    2>/dev/null || true

  # jscpd gera jscpd-report.json
  if [[ -f "$REPORT_DIR/jscpd-report.json" ]]; then
    mv "$REPORT_DIR/jscpd-report.json" "$output_file"
    local dup_count
    dup_count=$(jq '.duplicates | length' "$output_file" 2>/dev/null || echo 0)
    local dup_percentage
    dup_percentage=$(jq '.statistics.total.percentage // 0' "$output_file" 2>/dev/null || echo 0)

    if [[ "$dup_count" -gt 0 ]]; then
      log WARN "jscpd: $dup_count bloco(s) duplicado(s) (${dup_percentage}% do código)"
      log INFO "  Revise $output_file para detalhes"
    else
      log SUCCESS "jscpd: nenhuma duplicação significativa"
    fi
  else
    log DEBUG "jscpd não gerou relatório"
  fi
}

#############################################
# PIP-AUDIT - VULNERABILIDADES DEPS (PyPI/OSV)
#############################################

run_pip_audit() {
  if [[ "$SKIP_SECURITY" == true ]]; then
    log INFO "pip-audit pulado (--skip-security)"
    return 0
  fi

  log INFO "Executando pip-audit (vulnerabilidades em dependências - PyPI/OSV)..."

  if ! "$PYTHON_BIN" -m pip_audit --version &>/dev/null 2>&1; then
    log WARN "pip-audit não disponível - instale com: pip install pip-audit"
    return 0
  fi

  local output_file="$REPORT_DIR/pip_audit.json"

  # pip-audit usa banco PyPI Advisory e OSV
  if run_with_timeout "$TOOL_TIMEOUT" "pip-audit" \
    "$PYTHON_BIN" -m pip_audit \
      --format json \
      --output "$output_file" \
      --progress-spinner off \
      2>/dev/null; then
    log SUCCESS "pip-audit: nenhuma vulnerabilidade conhecida"
  else
    if [[ -f "$output_file" ]]; then
      local vuln_count
      vuln_count=$(jq 'length' "$output_file" 2>/dev/null || echo 0)
      log WARN "pip-audit: $vuln_count vulnerabilidade(s) em dependências"
      log INFO "  Use 'pip-audit --fix' para corrigir automaticamente"
    fi
  fi
}

#############################################
# OSV-SCANNER - VULNERABILIDADES MULTI-ECOSSISTEMA
#############################################

run_osv_scanner() {
  if [[ "$SKIP_SECURITY" == true ]]; then
    log INFO "OSV-Scanner pulado (--skip-security)"
    return 0
  fi

  log INFO "Executando OSV-Scanner (vulnerabilidades multi-ecossistema)..."

  if ! command -v osv-scanner &>/dev/null; then
    log WARN "OSV-Scanner não disponível"
    log INFO "  Instale: go install github.com/google/osv-scanner/cmd/osv-scanner@latest"
    return 0
  fi

  local output_file="$REPORT_DIR/osv_scanner.json"

  run_with_timeout "$TOOL_TIMEOUT" "osv-scanner" \
    osv-scanner scan \
      --format json \
      --output "$output_file" \
      --recursive \
      "$PROJECT_DIR" 2>/dev/null || true

  if [[ -f "$output_file" ]]; then
    local vuln_count
    vuln_count=$(jq '.results | map(.packages | map(.vulnerabilities | length) | add) | add // 0' "$output_file" 2>/dev/null || echo 0)

    if [[ "$vuln_count" -gt 0 ]]; then
      log WARN "OSV-Scanner: $vuln_count vulnerabilidade(s) encontrada(s)"
      log INFO "  Revise $output_file para detalhes e licenças"
    else
      log SUCCESS "OSV-Scanner: nenhuma vulnerabilidade"
    fi
  fi
}

#############################################
# PYRIGHT - TYPE CHECKING AVANÇADO
#############################################

run_pyright() {
  start_timer "Pyright"
  log INFO "Executando Pyright (type checking avançado)..."

  if ! command -v pyright &>/dev/null; then
    log DEBUG "Pyright não disponível - instale com: pip install pyright"
    end_timer "Pyright"
    return 0
  fi

  local output_file="$REPORT_DIR/pyright.json"
  local cache_key="pyright"

  if cache_hit "$cache_key" "$output_file"; then
    local cached_error_count
    cached_error_count=$(jq '.generalDiagnostics | length' "$output_file" 2>/dev/null || echo 0)
    if [[ "$cached_error_count" -gt 0 ]]; then
      log INFO "Pyright (cache): $cached_error_count diagnóstico(s)"
    else
      log SUCCESS "Pyright (cache): tipagem validada"
    fi
    end_timer "Pyright"
    return 0
  fi

  # Diretórios específicos (evita analisar tudo)
  local targets=(
    "$PROJECT_CORE"
    "$PROJECT_LOGIC"
    "$PROJECT_VIS"
  )

  # Verifica quais existem
  local existing_targets=()
  for target in "${targets[@]}"; do
    if [[ -d "$target" ]]; then
      existing_targets+=("$target")
    fi
  done

  # Se nenhum existe, usa o diretório de projeto
  if [[ ${#existing_targets[@]} -eq 0 ]]; then
    existing_targets=("$PROJECT_DIR")
  fi

  log DEBUG "Pyright analisando: ${existing_targets[*]}"

  # Executar com threads paralelas se disponível
  run_with_timeout "$TOOL_TIMEOUT" "pyright" \
    pyright "${existing_targets[@]}" \
      --outputjson \
      --threads \
      > "$output_file" 2>/dev/null || true

  if [[ -f "$output_file" ]]; then
    local error_count
    error_count=$(jq '.generalDiagnostics | length' "$output_file" 2>/dev/null || echo 0)

    if [[ "$error_count" -gt 0 ]]; then
      log INFO "Pyright: $error_count diagnóstico(s) (complementar ao Mypy)"
    else
      log SUCCESS "Pyright: tipagem validada"
    fi
  fi
  cache_mark "$cache_key"
  end_timer "Pyright"
}

#############################################
# COMPLEXIPY - COGNITIVE COMPLEXITY
#############################################

run_complexipy() {
  start_timer "Complexipy"
  log INFO "Executando Complexipy (cognitive complexity)..."

  if ! command -v complexipy &>/dev/null; then
    log WARN "Complexipy não disponível - instale com: pip install complexipy"
    end_timer "Complexipy"
    return 0
  fi

  local output_file="$REPORT_DIR/complexipy.json"
  local threshold="${COMPLEXIPY_THRESHOLD:-15}"
  local cache_key="complexipy"

  if cache_hit "$cache_key" "$output_file"; then
    local cached_violations
    cached_violations=$(jq '[.[] | select(.cognitive_complexity > '"$threshold"')] | length' "$output_file" 2>/dev/null || echo 0)
    if [[ "$cached_violations" -gt 0 ]]; then
      log WARN "Complexipy (cache): $cached_violations função(ões) com complexidade cognitiva >$threshold"
    else
      log SUCCESS "Complexipy (cache): complexidade cognitiva aceitável"
    fi
    end_timer "Complexipy"
    return 0
  fi

  run_with_timeout "$TOOL_TIMEOUT" "complexipy" \
    complexipy "$PROJECT_DIR" \
      --threshold "$threshold" \
      --format json \
      > "$output_file" 2>/dev/null || true

  if [[ -f "$output_file" ]]; then
    local violations
    violations=$(jq '[.[] | select(.cognitive_complexity > '"$threshold"')] | length' "$output_file" 2>/dev/null || echo 0)

    if [[ "$violations" -gt 0 ]]; then
      log WARN "Complexipy: $violations função(ões) com complexidade cognitiva >$threshold"
    else
      log SUCCESS "Complexipy: complexidade cognitiva aceitável"
    fi
  fi
  cache_mark "$cache_key"
  end_timer "Complexipy"
}

#############################################
# SKYLOS - CÓDIGO MORTO + SEGURANÇA
#############################################

run_skylos() {
  if [[ "$SKIP_DEADCODE" == true ]]; then
    log INFO "Skylos pulado (--skip-deadcode)"
    return 0
  fi

  log INFO "Executando Skylos (dead code + security analysis)..."

  if ! command -v skylos &>/dev/null; then
    log WARN "Skylos não disponível - instale com: pip install skylos"
    return 0
  fi

  local output_file="$REPORT_DIR/skylos.json"

  # Executar skylos com trace para reduzir falsos positivos
  run_with_timeout "$TOOL_TIMEOUT" "skylos" skylos "$PROJECT_DIR" --json > "$output_file" 2>/dev/null || true

  if [[ -f "$output_file" ]]; then
    local dead_code
    local security_issues
    local quality_issues

    dead_code=$(jq '.dead_code | length' "$output_file" 2>/dev/null || echo 0)
    security_issues=$(jq '.security | length' "$output_file" 2>/dev/null || echo 0)
    quality_issues=$(jq '.quality | length' "$output_file" 2>/dev/null || echo 0)

    log INFO "Skylos: $dead_code código(s) morto(s), $security_issues issue(s) segurança, $quality_issues issue(s) qualidade"
  fi
}

#############################################
# LIZARD - COMPLEXIDADE CICLOMÁTICA
#############################################

run_lizard() {
  start_timer "Lizard"
  log INFO "Executando Lizard (cyclomatic complexity)..."

  if ! "$PYTHON_BIN" -m lizard --version &>/dev/null 2>&1; then
    log WARN "Lizard não disponível - instale com: pip install lizard"
    end_timer "Lizard"
    return 0
  fi

  local ccn_threshold="${LIZARD_CCN_THRESHOLD:-15}"
  local length_threshold="${LIZARD_LENGTH_THRESHOLD:-1000}"
  local args_threshold="${LIZARD_ARGS_THRESHOLD:-15}"
  local xml_file="$REPORT_DIR/lizard.xml"
  local html_file="$REPORT_DIR/lizard.html"
  local csv_file="$REPORT_DIR/lizard.csv"
  local cache_key="lizard"

  if cache_hit "$cache_key" "$xml_file" "$html_file" "$csv_file"; then
    local cached_violations
    cached_violations=$(grep -c "ccn=\"[0-9]\{2,\}\"" "$xml_file" 2>/dev/null || true)
    cached_violations="${cached_violations:-0}"
    if [[ "$cached_violations" -gt 0 ]]; then
      log WARN "Lizard (cache): $cached_violations função(ões) com CCN >$ccn_threshold"
    else
      log SUCCESS "Lizard (cache): complexidade ciclomática aceitável"
    fi
    end_timer "Lizard"
    return 0
  fi

  # Diretórios específicos para análise (evita analisar todo o projeto desnecessariamente)
  local targets=(
    "$PROJECT_CORE"
    "$PROJECT_LOGIC"
    "$PROJECT_VIS"
  )

  # Verifica quais diretórios existem
  local existing_targets=()
  for target in "${targets[@]}"; do
    if [[ -d "$target" ]]; then
      existing_targets+=("$target")
    fi
  done

  # Se nenhum diretório específico existe, analisa o diretório principal do projeto
  if [[ ${#existing_targets[@]} -eq 0 ]]; then
    existing_targets=("$PROJECT_DIR")
  fi

  log DEBUG "Lizard analisando: ${existing_targets[*]}"

  # Argumentos comuns de exclusão
  local exclude_args=(
    --exclude "*/test_*"
    --exclude "*/tests/*"
    --exclude "*_test.py"
    --exclude "*/venv/*"
    --exclude "*/.venv/*"
    --exclude "*/build/*"
    --exclude "*/__pycache__/*"
    --exclude "*/.pytest_cache/*"
    --exclude "*/quality-pipeline/*"
  )

  # XML output (padrão)
  run_with_timeout "$TOOL_TIMEOUT" "lizard-xml" \
    "$PYTHON_BIN" -m lizard "${existing_targets[@]}" \
      --CCN "$ccn_threshold" \
      --length "$length_threshold" \
      --arguments "$args_threshold" \
      --xml \
      "${exclude_args[@]}" \
      > "$xml_file" 2>/dev/null || true

  # HTML output (mais legível)
  run_with_timeout "$TOOL_TIMEOUT" "lizard-html" \
    "$PYTHON_BIN" -m lizard "${existing_targets[@]}" \
      --CCN "$ccn_threshold" \
      --length "$length_threshold" \
      --arguments "$args_threshold" \
      --html \
      "${exclude_args[@]}" \
      > "$html_file" 2>/dev/null || true

  # CSV output (para análise em planilhas)
  run_with_timeout "$TOOL_TIMEOUT" "lizard-csv" \
    "$PYTHON_BIN" -m lizard "${existing_targets[@]}" \
      --CCN "$ccn_threshold" \
      --length "$length_threshold" \
      --arguments "$args_threshold" \
      --csv \
      "${exclude_args[@]}" \
      > "$csv_file" 2>/dev/null || true

  # Análise de resultados
  if [[ -f "$xml_file" ]]; then
    local violations
    violations=$(grep -c "ccn=\"[0-9]\{2,\}\"" "$xml_file" 2>/dev/null || true)
    violations="${violations:-0}"

    if [[ "$violations" -gt 0 ]]; then
      log WARN "Lizard: $violations função(ões) com CCN >$ccn_threshold"
      log INFO "Relatórios gerados: XML ($xml_file), HTML ($html_file), CSV ($csv_file)"
    else
      log SUCCESS "Lizard: complexidade ciclomática aceitável"
    fi
  fi
  cache_mark "$cache_key"
  end_timer "Lizard"
}

#############################################
# INTERROGATE - COBERTURA DE DOCSTRINGS
#############################################

run_interrogate() {
  start_timer "Interrogate"
  log INFO "Executando Interrogate (docstring coverage)..."

  if ! command -v interrogate &>/dev/null; then
    log WARN "Interrogate não disponível - instale com: pip install interrogate"
    end_timer "Interrogate"
    return 0
  fi

  local output_file="$REPORT_DIR/interrogate.txt"
  local min_coverage="${INTERROGATE_MIN_COVERAGE:-50}"
  local badge_file="$REPORT_DIR/interrogate_badge.svg"
  local cache_key="interrogate"

  if cache_hit "$cache_key" "$output_file"; then
    local cached_coverage
    cached_coverage=$(grep -oP 'Result: \K[0-9.]+(?=%)' "$output_file" 2>/dev/null || echo "0")
    if (( $(echo "$cached_coverage < $min_coverage" | bc -l 2>/dev/null || echo 1) )); then
      log WARN "Interrogate (cache): ${cached_coverage}% cobertura de docstrings (mínimo: ${min_coverage}%)"
    else
      log SUCCESS "Interrogate (cache): ${cached_coverage}% cobertura de docstrings"
    fi
    end_timer "Interrogate"
    return 0
  fi

  run_with_timeout "$TOOL_TIMEOUT" "interrogate" interrogate "${SCAN_TARGETS[@]}" \
    --verbose \
    --fail-under "$min_coverage" \
    --generate-badge "$badge_file" \
    > "$output_file" 2>&1 || true

  if [[ -f "$output_file" ]]; then
    local coverage
    coverage=$(grep -oP 'Result: \K[0-9.]+(?=%)' "$output_file" 2>/dev/null || echo "0")

    if (( $(echo "$coverage < $min_coverage" | bc -l 2>/dev/null || echo 1) )); then
      log WARN "Interrogate: ${coverage}% cobertura de docstrings (mínimo: ${min_coverage}%)"
    else
      log SUCCESS "Interrogate: ${coverage}% cobertura de docstrings"
    fi
  fi
  cache_mark "$cache_key"
  end_timer "Interrogate"
}

#############################################
# PYDOCSTYLE - CONFORMIDADE DE DOCSTRINGS
#############################################

run_pydocstyle() {
  start_timer "Pydocstyle"
  log INFO "Executando pydocstyle (PEP 257 compliance)..."

  if ! command -v pydocstyle &>/dev/null; then
    log WARN "pydocstyle não disponível - instale com: pip install pydocstyle"
    end_timer "Pydocstyle"
    return 0
  fi

  local output_file="$REPORT_DIR/pydocstyle.txt"
  local cache_key="pydocstyle"

  if cache_hit "$cache_key" "$output_file"; then
    local cached_violations
    cached_violations=$(wc -l < "$output_file" 2>/dev/null || echo 0)
    if [[ "$cached_violations" -gt 0 ]]; then
      log WARN "pydocstyle (cache): $cached_violations violação(ões) PEP 257"
    else
      log SUCCESS "pydocstyle (cache): docstrings conformes com PEP 257"
    fi
    end_timer "Pydocstyle"
    return 0
  fi

  run_with_timeout "$TOOL_TIMEOUT" "pydocstyle" pydocstyle "${SCAN_TARGETS[@]}" > "$output_file" 2>&1 || true

  if [[ -f "$output_file" ]]; then
    local violations
    violations=$(wc -l < "$output_file" 2>/dev/null || echo 0)

    if [[ "$violations" -gt 0 ]]; then
      log WARN "pydocstyle: $violations violação(ões) PEP 257"
    else
      log SUCCESS "pydocstyle: docstrings conformes com PEP 257"
    fi
  fi
  cache_mark "$cache_key"
  end_timer "Pydocstyle"
}

#############################################
# MUTMUT - MUTATION TESTING
#############################################

run_mutmut() {
  if [[ "$SKIP_TESTS" == true ]]; then
    log INFO "Mutmut pulado (--skip-tests)"
    return 0
  fi

  # Skip on Windows due to 'resource' module dependency
  if [[ "${OS:-}" == "Windows_NT" || "${OSTYPE:-}" == msys* ]]; then
    log INFO "Mutmut pulado no Windows (dependência de 'resource')"
    return 0
  fi

  log INFO "Executando Mutmut (mutation testing)..."

  if ! command -v mutmut &>/dev/null; then
    log WARN "Mutmut não disponível - instale com: pip install mutmut"
    log INFO "  Nota: Mutation testing é computacionalmente intensivo"
    return 0
  fi

  local cache_file="$CACHE_DIR/.mutmut-cache"

  # Executar mutmut de forma incremental
  mutmut run \
    --paths-to-mutate="$PROJECT_DIR" \
    --tests-dir="$PROJECT_TESTS" \
    --runner="pytest -x -q" \
    --use-cache \
    2>&1 | tee "$REPORT_DIR/mutmut.log" || true

  # Gerar relatório HTML
  mutmut html --directory="$REPORT_DIR/mutmut_html" 2>/dev/null || true

  # Resumo de mutantes
  local killed survived timeout suspicious
  killed=$(mutmut results 2>/dev/null | grep -c "🎉 Killed" || echo 0)
  survived=$(mutmut results 2>/dev/null | grep -c "BAD Survived" || echo 0)
  timeout=$(mutmut results 2>/dev/null | grep -c "⏰ Timeout" || echo 0)
  suspicious=$(mutmut results 2>/dev/null | grep -c "🤔 Suspicious" || echo 0)

  log INFO "Mutmut: killed=$killed, survived=$survived, timeout=$timeout, suspicious=$suspicious"

  if [[ "$survived" -gt 0 ]]; then
    log WARN "Mutmut: $survived mutante(s) sobreviveram - melhorar testes"
  fi
}

#############################################
# PROSPECTOR - AGREGADOR DE LINTERS
#############################################

run_prospector() {
  start_timer "Prospector"
  log INFO "Executando Prospector (linter aggregator)..."

  if ! command -v prospector &>/dev/null; then
    log WARN "Prospector não disponível - instale com: pip install prospector"
    end_timer "Prospector"
    return 0
  fi

  local output_file="$REPORT_DIR/prospector.json"
  local strictness="${PROSPECTOR_STRICTNESS:-medium}"
  local cache_key="prospector"

  if cache_hit "$cache_key" "$output_file"; then
    local cached_messages
    cached_messages=$(jq '.messages | length' "$output_file" 2>/dev/null || echo 0)
    if [[ "$cached_messages" -gt 0 ]]; then
      log INFO "Prospector (cache): $cached_messages mensagem(ns) (strictness: $strictness)"
    else
      log SUCCESS "Prospector (cache): nenhum issue detectado"
    fi
    end_timer "Prospector"
    return 0
  fi

  run_with_timeout "$TOOL_TIMEOUT" "prospector" prospector "${SCAN_TARGETS[@]}" \
    --strictness "$strictness" \
    --output-format json \
    --output-file "$output_file" \
    2>/dev/null || true

  if [[ -f "$output_file" ]]; then
    local messages
    messages=$(jq '.messages | length' "$output_file" 2>/dev/null || echo 0)

    if [[ "$messages" -gt 0 ]]; then
      log INFO "Prospector: $messages mensagem(ns) (strictness: $strictness)"
    else
      log SUCCESS "Prospector: nenhum issue detectado"
    fi
  fi
  cache_mark "$cache_key"
  end_timer "Prospector"
}

#############################################
# PYAUTOGUI - UI AUTOMATION TESTING
#############################################

run_pyautogui_tests() {
  if [[ "$SKIP_TESTS" == true ]] || [[ "$SKIP_UI_TESTS" == true ]]; then
    log INFO "PyAutoGUI tests pulado (--skip-tests ou --skip-ui-tests)"
    return 0
  fi

  log INFO "Executando PyAutoGUI UI automation tests..."

  if ! $PYTHON_BIN -c "import pyautogui" 2>/dev/null; then
    log WARN "PyAutoGUI não disponível - instale com: pip install pyautogui"
    return 0
  fi

  local test_script="$ROOT_DIR/$PROJECT_TESTS/ui/test_pyautogui.py"
  local output_file="$REPORT_DIR/pyautogui_tests.log"

  if [[ ! -f "$test_script" ]]; then
    log DEBUG "Script de teste PyAutoGUI não encontrado: $test_script"
    return 0
  fi

  run_with_timeout "$TOOL_TIMEOUT" "pyautogui-tests" "$PYTHON_BIN" "$test_script" > "$output_file" 2>&1 || true

  if [[ -f "$output_file" ]]; then
    local passed failed
    passed=$(grep -c "PASSED" "$output_file" 2>/dev/null || echo 0)
    failed=$(grep -c "FAILED" "$output_file" 2>/dev/null || echo 0)

    log INFO "PyAutoGUI: $passed test(s) passado(s), $failed falhado(s)"
  fi
}

#############################################
# PYWINAUTO - WINDOWS GUI AUTOMATION
#############################################

run_pywinauto_tests() {
  if [[ "$SKIP_TESTS" == true ]] || [[ "$SKIP_UI_TESTS" == true ]]; then
    log INFO "Pywinauto tests pulado (--skip-tests ou --skip-ui-tests)"
    return 0
  fi

  # Apenas para Windows
  if [[ "${OS:-}" != "Windows_NT" ]] && [[ "${OSTYPE:-}" != msys* ]]; then
    log DEBUG "Pywinauto requer Windows - pulando"
    return 0
  fi

  log INFO "Executando Pywinauto Windows GUI automation tests..."

  if ! $PYTHON_BIN -c "import pywinauto" 2>/dev/null; then
    log WARN "Pywinauto não disponível - instale com: pip install pywinauto"
    return 0
  fi

  local test_script="$ROOT_DIR/$PROJECT_TESTS/ui/test_pywinauto.py"
  local output_file="$REPORT_DIR/pywinauto_tests.log"

  if [[ ! -f "$test_script" ]]; then
    log DEBUG "Script de teste Pywinauto não encontrado: $test_script"
    return 0
  fi

  run_with_timeout "$TOOL_TIMEOUT" "pywinauto-tests" "$PYTHON_BIN" "$test_script" > "$output_file" 2>&1 || true

  if [[ -f "$output_file" ]]; then
    local passed failed
    passed=$(grep -c "PASSED" "$output_file" 2>/dev/null || echo 0)
    failed=$(grep -c "FAILED" "$output_file" 2>/dev/null || echo 0)

    log INFO "Pywinauto: $passed test(s) passado(s), $failed falhado(s)"
  fi
}

#############################################
# LIGHTHOUSE - WEB QUALITY AUDITS
#############################################

run_lighthouse() {
  if [[ "$SKIP_UI_TESTS" == true ]]; then
    log INFO "Lighthouse pulado (--skip-ui-tests)"
    return 0
  fi

  log INFO "Executando Lighthouse (web quality audits)..."

  if ! command -v lighthouse &>/dev/null; then
    log WARN "Lighthouse não disponível - instale com: npm install -g lighthouse"
    return 0
  fi

  local url="${LIGHTHOUSE_URL:-http://localhost:8000}"
  local output_file="$REPORT_DIR/lighthouse.json"
  local html_report="$REPORT_DIR/lighthouse.html"

  # Verificar se há um servidor rodando
  if ! curl -s --head "$url" &>/dev/null; then
    log DEBUG "Nenhum servidor detectado em $url - pulando Lighthouse"
    return 0
  fi

  lighthouse "$url" \
    --output json \
    --output html \
    --output-path "$REPORT_DIR/lighthouse" \
    --chrome-flags="--headless" \
    --quiet \
    2>/dev/null || true

  if [[ -f "${REPORT_DIR}/lighthouse.report.json" ]]; then
    mv "${REPORT_DIR}/lighthouse.report.json" "$output_file"
    mv "${REPORT_DIR}/lighthouse.report.html" "$html_report" 2>/dev/null || true

    local performance accessibility seo pwa best_practices
    performance=$(jq '.categories.performance.score * 100 | floor' "$output_file" 2>/dev/null || echo 0)
    accessibility=$(jq '.categories.accessibility.score * 100 | floor' "$output_file" 2>/dev/null || echo 0)
    seo=$(jq '.categories.seo.score * 100 | floor' "$output_file" 2>/dev/null || echo 0)
    pwa=$(jq '.categories.pwa.score * 100 | floor' "$output_file" 2>/dev/null || echo 0)
    best_practices=$(jq '(.categories."best-practices".score // 0) * 100 | floor' "$output_file" 2>/dev/null || echo 0)

    log INFO "Lighthouse: Performance=${performance}%, Accessibility=${accessibility}%, SEO=${seo}%, PWA=${pwa}%, Best Practices=${best_practices}%"

    # Avisar se scores abaixo de threshold
    if [[ "$performance" -lt 90 ]] || [[ "$accessibility" -lt 90 ]]; then
      log WARN "Lighthouse: Performance ou Accessibility abaixo de 90%"
    fi
  fi
}

#############################################
# PERCY - VISUAL TESTING
#############################################

run_percy() {
  if [[ "$SKIP_UI_TESTS" == true ]]; then
    log INFO "Percy pulado (--skip-ui-tests)"
    return 0
  fi

  log INFO "Executando Percy (visual regression testing)..."

  if ! command -v percy &>/dev/null; then
    log WARN "Percy CLI não disponível - instale com: npm install -g @percy/cli"
    log INFO "  Requer PERCY_TOKEN configurado como variável de ambiente"
    return 0
  fi

  if [[ -z "${PERCY_TOKEN:-}" ]]; then
    log DEBUG "PERCY_TOKEN não configurado - pulando Percy"
    return 0
  fi

  local output_file="$REPORT_DIR/percy.log"

  # Percy executa junto com testes (ex: pytest com percy-python)
  run_with_timeout "$TOOL_TIMEOUT" "percy" percy exec -- pytest "$PROJECT_TESTS/visual/" -v \
    > "$output_file" 2>&1 || true

  if [[ -f "$output_file" ]]; then
    local snapshots
    snapshots=$(grep -c "Percy snapshot" "$output_file" 2>/dev/null || echo 0)

    if [[ "$snapshots" -gt 0 ]]; then
      log INFO "Percy: $snapshots snapshot(s) capturado(s)"
    else
      log DEBUG "Percy: nenhum snapshot capturado"
    fi
  fi
}

#############################################
# APPLITOOLS - AI-POWERED VISUAL VALIDATION
#############################################

run_applitools() {
  if [[ "$SKIP_UI_TESTS" == true ]]; then
    log INFO "Applitools pulado (--skip-ui-tests)"
    return 0
  fi

  log INFO "Executando Applitools (AI visual validation)..."

  if ! $PYTHON_BIN -c "import eyes_selenium" 2>/dev/null; then
    log WARN "Applitools Eyes SDK não disponível - instale com: pip install eyes-selenium"
    log INFO "  Requer APPLITOOLS_API_KEY configurado"
    return 0
  fi

  if [[ -z "${APPLITOOLS_API_KEY:-}" ]]; then
    log DEBUG "APPLITOOLS_API_KEY não configurado - pulando Applitools"
    return 0
  fi

  local test_script="$ROOT_DIR/$PROJECT_TESTS/visual/test_applitools.py"
  local output_file="$REPORT_DIR/applitools.log"

  if [[ ! -f "$test_script" ]]; then
    log DEBUG "Script de teste Applitools não encontrado: $test_script"
    return 0
  fi

  run_with_timeout "$TOOL_TIMEOUT" "applitools-tests" "$PYTHON_BIN" "$test_script" > "$output_file" 2>&1 || true

  if [[ -f "$output_file" ]]; then
    local passed failed
    passed=$(grep -c "PASSED" "$output_file" 2>/dev/null || echo 0)
    failed=$(grep -c "FAILED" "$output_file" 2>/dev/null || echo 0)

    log INFO "Applitools: $passed validação(ões) passada(s), $failed falhada(s)"
  fi
}

#############################################
# AST-GREP - ANÁLISE ESTRUTURAL
#############################################

run_astgrep() {
  log INFO "Executando ast-grep (análise estrutural)..."

  local rules_dir="$ROOT_DIR/tools/ast_rules/python"
  local output_file="$REPORT_DIR/astgrep_results.json"

  if ! command -v sg &>/dev/null; then
    log DEBUG "ast-grep não disponível"
    return 0
  fi

  if [[ ! -d "$rules_dir" ]]; then
    log DEBUG "Diretório de regras ast-grep não encontrado: $rules_dir"
    return 0
  fi

  run_with_timeout "$TOOL_TIMEOUT" "ast-grep-scan" sg scan --rule "$rules_dir" --json "$PROJECT_DIR" > "$output_file" 2>/dev/null || true

  if [[ "$MODE" == "apply" ]]; then
    log INFO "Aplicando transformações ast-grep..."
    run_with_timeout "$TOOL_TIMEOUT" "ast-grep-rewrite" sg scan --rule "$rules_dir" --rewrite "$PROJECT_DIR" 2>/dev/null || true
  fi

  local match_count
  match_count=$(jq '[.[] | .matches | length] | add // 0' "$output_file" 2>/dev/null || echo 0)

  if [[ "$match_count" -gt 0 ]]; then
    log INFO "ast-grep: $match_count correspondência(s)"
  else
    log SUCCESS "ast-grep: nenhum padrão problemático"
  fi
}

#############################################
# LIBCST - TRANSFORMAÇÕES
#############################################

run_libcst() {
  if [[ "$SKIP_LIBCST" == true ]]; then
    log INFO "LibCST pulado (--skip-libcst)"
    return 0
  fi

  local transforms_dir="$ROOT_DIR/tools/libcst_transforms"

  if [[ ! -d "$transforms_dir" ]]; then
    log DEBUG "Diretório LibCST não encontrado"
    return 0
  fi

  log INFO "Aplicando transformações LibCST..."

  if [[ "$MODE" == "apply" ]]; then
    run_with_timeout "$TOOL_TIMEOUT" "libcst-codemod" \
      "$PYTHON_BIN" -m libcst.tool codemod "$transforms_dir" "$PROJECT_DIR" 2>/dev/null || log WARN "LibCST: algumas transformações falharam"
  else
    log INFO "Modo dry-run: transformações LibCST não aplicadas"
  fi
}

#############################################
# NORMALIZAÇÃO DE ISSUES
#############################################

normalize_issues() {
  log INFO "Normalizando issues..."

  if [[ -d "$QUALITY_SCRIPTS_DIR" ]] && [[ -f "$QUALITY_SCRIPTS_DIR/normalize_issues.py" ]]; then
    "$PYTHON_BIN" "$QUALITY_SCRIPTS_DIR/normalize_issues.py" "$ISSUES_NORMALIZED" 2>/dev/null || {
      log WARN "Falha na normalização de issues"
      echo '[]' > "$ISSUES_NORMALIZED"
    }
  else
    log DEBUG "Script de normalização não encontrado"
    echo '[]' > "$ISSUES_NORMALIZED"
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

  if [[ ! -f pytest.ini ]] && [[ ! -d tests ]] && [[ ! -d "$PROJECT_TESTS" ]]; then
    log DEBUG "Nenhum teste encontrado"
    return 0
  fi

  log INFO "Executando testes..."

  local test_root=""
  [[ -d "$PROJECT_TESTS/unit" ]] && test_root="$PROJECT_TESTS/unit"
  [[ -z "$test_root" ]] && [[ -d "$PROJECT_TESTS" ]] && test_root="$PROJECT_TESTS"
  [[ -z "$test_root" ]] && [[ -d tests/unit ]] && test_root="tests/unit"
  [[ -z "$test_root" ]] && [[ -d tests ]] && test_root="tests"

  if [[ -z "$test_root" ]]; then
    log WARN "Nenhum diretório de testes encontrado"
    return 0
  fi

  if run_with_timeout "$TOOL_TIMEOUT" "pytest" pytest "$test_root" -v --tb=short 2>&1 | tee "$REPORT_DIR/pytest.log"; then
    log SUCCESS "Testes passaram"
  else
    log WARN "Alguns testes falharam"
    return 1
  fi
}

#############################################
# PRE-COMMIT INTEGRATION
#############################################

setup_precommit() {
  log INFO "Verificando configuração pre-commit..."

  if [[ ! -f ".pre-commit-config.yaml" ]]; then
    log INFO "Criando .pre-commit-config.yaml..."
    cat > ".pre-commit-config.yaml" <<'EOF'
# Pre-commit hooks for PyRME Canary
# Instale: pip install pre-commit && pre-commit install

repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--ignore-missing-imports]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.8
    hooks:
      - id: bandit
        args: [-r, py_rme_canary, -x, tests]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: [--maxkb=1000]

  - repo: local
    hooks:
      - id: radon-cc
        name: Radon Cyclomatic Complexity
        entry: bash -c 'radon cc py_rme_canary --min D --show-complexity --total-average'
        language: system
        pass_filenames: false
EOF
    log SUCCESS "Pre-commit configurado"
  else
    log DEBUG "Pre-commit já configurado"
  fi

  if command -v pre-commit &>/dev/null; then
    log INFO "Instalando hooks pre-commit..."
    pre-commit install 2>/dev/null || log WARN "Falha ao instalar hooks"
  else
    log INFO "Instale pre-commit: pip install pre-commit"
  fi
}

#############################################
# COMPARAÇÃO DE SÍMBOLOS
#############################################

compare_symbols() {
  log INFO "Comparando símbolos (antes vs depois)..."

  if [[ ! -f "$SYMBOL_INDEX_BEFORE" ]] || [[ ! -f "$SYMBOL_INDEX_AFTER" ]]; then
    log DEBUG "Índices de símbolos não disponíveis"
    return 0
  fi

  "$PYTHON_BIN" - "$SYMBOL_INDEX_BEFORE" "$SYMBOL_INDEX_AFTER" <<'PYTHON' || true
import json
import sys

try:
    before_data = json.load(open(sys.argv[1], encoding="utf-8"))
    after_data = json.load(open(sys.argv[2], encoding="utf-8"))

    before = {(s["file"], s["name"]) for s in before_data.get("symbols", [])}
    after = {(s["file"], s["name"]) for s in after_data.get("symbols", [])}

    removed = before - after
    added = after - before

    if removed:
        print(f"[WARN] Simbolos removidos: {len(removed)}")
        for item in list(removed)[:5]:
            print(f"  - {item[0]}:{item[1]}")

    if added:
        print(f"[INFO] Simbolos adicionados: {len(added)}")
        for item in list(added)[:5]:
            print(f"  + {item[0]}:{item[1]}")

    if not removed and not added:
        print("[OK] Simbolos consistentes")
except Exception as e:
    print(f"Erro na comparação: {e}")
PYTHON

  log SUCCESS "Comparação de símbolos concluída"
}

#############################################
# JULES INTEGRAÇÃO LOCAL
#############################################

run_jules_generate_suggestions() {
  if [[ "$SKIP_JULES" == true ]]; then
    log INFO "Integração Jules pulada (--skip-jules)"
    return 0
  fi

  local runner="$PROJECT_DIR/scripts/jules_runner.py"
  if [[ ! -f "$runner" ]]; then
    log WARN "jules_runner.py não encontrado em $runner - pulando Jules"
    return 0
  fi

  local schema_path="$ROOT_DIR/.github/jules/suggestions.schema.json"
  local output_dir="$ROOT_DIR/reports/jules"
  local connectivity_json="$REPORT_DIR/jules_connectivity.json"
  mkdir -p "$output_dir"

  local -a source_args=()
  local -a branch_args=()
  if [[ -n "${JULES_SOURCE:-}" ]]; then
    source_args=(--source "$JULES_SOURCE")
  fi
  if [[ -n "${JULES_BRANCH:-}" ]]; then
    branch_args=(--branch "$JULES_BRANCH")
  fi

  log INFO "Executando check de conectividade Jules..."
  run_with_timeout "$TOOL_TIMEOUT" "jules-check" \
    "$PYTHON_BIN" "$runner" --project-root "$ROOT_DIR" check \
    --json-out "$connectivity_json" \
    "${source_args[@]}" \
    "${branch_args[@]}" || true

  log INFO "Gerando sugestões Jules (quality -> suggestions contract)..."
  if run_with_timeout "$TOOL_TIMEOUT" "jules-generate-suggestions" \
    "$PYTHON_BIN" "$runner" --project-root "$ROOT_DIR" generate-suggestions \
    --quality-report "$FINAL_REPORT" \
    --output-dir "$output_dir" \
    --report-dir "$REPORT_DIR" \
    --schema "$schema_path" \
    "${source_args[@]}" \
    "${branch_args[@]}"; then
    log SUCCESS "Jules: artefatos gerados em $output_dir"
  else
    log WARN "Jules: integração falhou (pipeline continuará)."
  fi
}

#############################################
# RELATÓRIO FINAL
#############################################

generate_final_report() {
  log INFO "Gerando relatório consolidado..."

  "$PYTHON_BIN" - \
    "$MODE" \
    "$SYMBOL_INDEX_BEFORE" \
    "$SYMBOL_INDEX_AFTER" \
    "$LOG_FILE" \
    "$RUN_START_EPOCH" \
    "$ISSUES_NORMALIZED" \
    "$FINAL_REPORT" \
    "$REPORT_DIR" \
    "$SKIP_SECURITY" \
    "$SKIP_SONARLINT" \
    <<'PYTHON'
import json
from pathlib import Path
from datetime import datetime
import sys

mode = sys.argv[1]
run_started_at = float(sys.argv[5])
report_dir = Path(sys.argv[8])
skip_security = str(sys.argv[9]).lower() == "true"
skip_sonarlint = str(sys.argv[10]).lower() == "true"
log_path = Path(sys.argv[4])
log_text = log_path.read_text(encoding="utf-8", errors="ignore") if log_path.exists() else ""

def is_fresh(path: Path) -> bool:
    try:
        return path.exists() and path.stat().st_mtime >= run_started_at
    except OSError:
        return False

def saw_log(fragment: str) -> bool:
    return fragment in log_text

# Coletar resultados
ruff_json = Path(".ruff.json")
issues_normalized = report_dir / "issues_normalized.json"
ruff_issues_count = 0
if is_fresh(issues_normalized):
    try:
        normalized = json.loads(issues_normalized.read_text(encoding="utf-8"))
        by_tool = normalized.get("by_tool", {}) if isinstance(normalized, dict) else {}
        if isinstance(by_tool, dict):
            ruff_issues_count = int(by_tool.get("Ruff", by_tool.get("ruff", 0)) or 0)
    except Exception:
        ruff_issues_count = 0

bandit_issues = 0
bandit_json = report_dir / "bandit.json"
if is_fresh(bandit_json):
    try:
        bandit_data = json.loads(bandit_json.read_text(encoding="utf-8"))
        bandit_issues = len(bandit_data.get("results", []))
    except:
        pass

safety_issues = 0
safety_json = report_dir / "safety.json"
if is_fresh(safety_json):
    try:
        safety_data = json.loads(safety_json.read_text(encoding="utf-8"))
        safety_issues = len(safety_data) if isinstance(safety_data, list) else 0
    except:
        pass

def status_line(*, executed: bool, skipped: bool, label: str) -> str:
    if skipped:
        return f"- ⏭️ {label} (pulado por flag)"
    if executed:
        return f"- ✅ {label}"
    return f"- ⚠️ {label} (não executado ou ferramenta indisponível)"

bandit_summary = "N/A (skip-security)" if skip_security else str(bandit_issues)
safety_summary = "N/A (skip-security)" if skip_security else str(safety_issues)
tools_status = [
    status_line(executed=saw_log("Executando Ruff"), skipped=False, label="Ruff (linter + formatter)"),
    (
        "- ⚠️ Mypy (type checking) (pulado por requisito de versão Python >= 3.12)"
        if saw_log("Mypy pulado")
        else status_line(executed=saw_log("Executando Mypy"), skipped=False, label="Mypy (type checking)")
    ),
    status_line(executed=saw_log("Executando Radon"), skipped=False, label="Radon (complexidade)"),
    status_line(executed=saw_log("Executando Bandit"), skipped=skip_security or saw_log("Análise Bandit pulada"), label="Bandit (segurança)"),
    status_line(executed=saw_log("Analisando Safety") or saw_log("Executando Safety"), skipped=skip_security or saw_log("Análise Safety pulada"), label="Safety (dependências)"),
    status_line(executed=saw_log("Executando SonarLint CLI"), skipped=(skip_security or skip_sonarlint or saw_log("SonarLint pulado")), label="SonarLint CLI (análise local)"),
]

report = f"""# Relatório de Qualidade v2.0
**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Modo:** {mode}

## 📊 Sumário Executivo
- **Issues Ruff:** {ruff_issues_count}
- **Vulnerabilidades Bandit:** {bandit_summary}
- **Vulnerabilidades Safety:** {safety_summary}

## 🛠️ Ferramentas Executadas
{chr(10).join(tools_status)}

## 📁 Artefatos Gerados
"""

for f in sorted(report_dir.glob("*.json")):
    report += f"- `{f.name}`\n"
for f in sorted(report_dir.glob("*.log")):
    report += f"- `{f.name}`\n"

report += f"""
## 🎯 Próximos Passos
- Revisar issues de alta severidade
- Atualizar dependências com vulnerabilidades
- Executar testes de integração

## 📝 Notas
- SonarQube Server NÃO utilizado (projeto local)
- SonarLint CLI usado para análise de segurança local
- Pre-commit configurado para automação
"""

Path(sys.argv[7]).write_text(report, encoding="utf-8")
print(f"[OK] Relatorio: {sys.argv[7]}")
PYTHON
}

#############################################
# PIPELINE PRINCIPAL
#############################################

main() {
  log INFO "=== Quality Pipeline v2.3 Iniciado ==="
  log INFO "Modo: $MODE | Verbose: $VERBOSE"

  check_dependencies
  snapshot
  setup_precommit

  # Fase 1: Baseline (Linting, Types, Complexity)
  log INFO "=== FASE 1: BASELINE ==="
  index_symbols "$SYMBOL_INDEX_BEFORE"
  run_ruff ".ruff.json" || true
  run_mypy ".mypy_baseline.log" || true
  run_radon ".radon.json" || true
  run_pyright || true
  run_complexipy || true
  run_lizard || true

  # Fase 2: Refatoração (se apply)
  if [[ "$MODE" == "apply" ]]; then
    log INFO "=== FASE 2: REFATORAÇÃO ==="
    run_astgrep
    run_libcst
    run_ruff ".ruff_after.json"
    run_mypy ".mypy_after.log" || true
    run_tests || true
  fi

  # Fase 3: Análise complementar (Dead Code, Duplication, Quality)
  log INFO "=== FASE 3: ANÁLISE COMPLEMENTAR ==="
  run_pylint || true
  run_prospector || true
  if [[ "$SKIP_DEADCODE" == false ]]; then
    run_vulture || true
    run_skylos || true
    run_jscpd || true
  fi

  # Fase 4: Segurança (Multi-layer)
  log INFO "=== FASE 4: SEGURANÇA ==="

  # 4.1: Secret Scanning
  if [[ "$SKIP_SECRETS" == false ]]; then
    log INFO "--- Fase 4.1: Secret Scanning ---"
    run_detect_secrets || true
  fi

  # 4.2: Code Security Analysis
  log INFO "--- Fase 4.2: Code Security ---"
  run_bandit || true
  run_semgrep || true
  run_sonarlint || true

  # 4.3: Dependency Vulnerabilities
  log INFO "--- Fase 4.3: Dependency Vulnerabilities ---"
  run_safety || true
  run_pip_audit || true
  run_osv_scanner || true

  # Fase 5: Documentação e Qualidade de Testes
  log INFO "=== FASE 5: DOCUMENTAÇÃO E TESTES ==="
  run_interrogate || true
  run_pydocstyle || true
  run_mutmut || true

  # Fase 6: UI/UX Automation e Visual Testing
  if [[ "$SKIP_UI_TESTS" == false ]]; then
    log INFO "=== FASE 6: UI/UX AUTOMATION ==="
    run_pyautogui_tests || true
    run_pywinauto_tests || true
    run_lighthouse || true
    run_percy || true
    run_applitools || true
  fi

  # Fase 7: Consolidação
  log INFO "=== FASE 7: CONSOLIDAÇÃO ==="
  normalize_issues
  index_symbols "$SYMBOL_INDEX_AFTER"
  compare_symbols
  generate_final_report
  run_jules_generate_suggestions

  log SUCCESS "=== Pipeline v2.3 Concluído ==="

  if [[ "$MODE" == "dry-run" ]]; then
    log INFO "ℹ️  Modo dry-run: nenhuma alteração aplicada"
    log INFO "ℹ️  Execute com --apply para aplicar mudanças"
  fi
}

main
