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
./quality.sh --dry-run --verbose
```

**O que faz:**
- ✅ Executa todas as análises
- ✅ Gera relatórios detalhados
- ❌ **NÃO modifica** nenhum arquivo

### Modo Apply (Aplica correções)

```bash
./quality.sh --apply
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
./quality.sh --apply --skip-tests
```

### Pular LibCST (transformações complexas)

```bash
./quality.sh --apply --skip-libcst
```

### Pular SonarQube (sem análise de segurança)

```bash
./quality.sh --apply --skip-sonar
```

### Habilitar Telemetria (debugging avançado)

```bash
./quality.sh --apply --telemetry
```

Gera arquivo `.quality_reports/telemetry.jsonl` com eventos estruturados.

---

## Estrutura de Diretórios

```
projeto/
├── quality.sh                      # Script principal
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
        run: ./quality.sh --dry-run --verbose

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
shellcheck quality.sh
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
./quality.sh --apply --skip-sonar
```

### Performance lenta

**Causa:** Cache do Mypy inválido ou projeto muito grande.

**Solução:**
```bash
# Limpa cache
rm -rf .quality_cache/mypy_cache

# Pula testes para execução mais rápida
./quality.sh --apply --skip-tests
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
# Valida o próprio quality.sh
shellcheck quality.sh

# Executa em modo verbose para debugging
./quality.sh --dry-run --verbose --telemetry
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
