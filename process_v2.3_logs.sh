#!/usr/bin/env bash

LOG_DIR=".quality_reports"
ARCHIVE_DIR="$LOG_DIR/archive/logs_2026-01"
CURRENT_LOG="quality_full_v2.3_run.log"
OUTPUT_DIR="$LOG_DIR/analysis"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$OUTPUT_DIR"

echo "=== Processamento de Logs Quality Pipeline v2.3 ==="
echo "Timestamp: $TIMESTAMP"
echo ""

# 1. Analisar log atual
echo "[1/6] Analisando log do último run..."
if [[ -f "$CURRENT_LOG" ]]; then
  INFO_COUNT=$(grep -c "\[INFO\]" "$CURRENT_LOG" 2>/dev/null || echo 0)
  WARN_COUNT=$(grep -c "\[WARN\]" "$CURRENT_LOG" 2>/dev/null || echo 0)
  ERROR_COUNT=$(grep -c "\[ERROR\]" "$CURRENT_LOG" 2>/dev/null || echo 0)

  echo "  • [INFO]:  $INFO_COUNT mensagens"
  echo "  • [WARN]:  $WARN_COUNT mensagens"
  echo "  • [ERROR]: $ERROR_COUNT mensagens"

  # Ferramentas não disponíveis
  grep "\[WARN\].*não disponível\|não encontrado" "$CURRENT_LOG" 2>/dev/null | \
    sed 's/.*\[WARN\].*\] //' | sort -u > "$OUTPUT_DIR/missing_tools_${TIMESTAMP}.txt"

  MISSING_COUNT=$(wc -l < "$OUTPUT_DIR/missing_tools_${TIMESTAMP}.txt" 2>/dev/null || echo 0)
  echo "  • Ferramentas não instaladas: $MISSING_COUNT"
fi

# 2. Consolidar logs arquivados
echo ""
echo "[2/6] Consolidando logs arquivados..."
ARCHIVED_LOGS=$(find "$ARCHIVE_DIR" -type f -name "*.log" 2>/dev/null | wc -l)
echo "  • Total de logs arquivados: $ARCHIVED_LOGS"

# 3. Extrair issues detectados
echo ""
echo "[3/6] Extraindo issues detectados..."

ruff_issues=$(grep "Ruff:.*issue(s)" "$CURRENT_LOG" 2>/dev/null | sed 's/.*Ruff: \([0-9]*\).*/\1/' || echo 0)
mypy_errors=$(grep -c "error:" "$CURRENT_LOG" 2>/dev/null || echo 0)
radon_funcs=$(grep "Radon:.*função" "$CURRENT_LOG" 2>/dev/null | sed 's/.*Radon: \([0-9]*\).*/\1/' || echo 0)
pylint_issues=$(grep "Pylint:.*issue(s)" "$CURRENT_LOG" 2>/dev/null | sed 's/.*Pylint: \([0-9]*\).*/\1/' || echo 0)
bandit_vulns=$(grep "Bandit:.*vulnerabilidade" "$CURRENT_LOG" 2>/dev/null | sed 's/.*Bandit: \([0-9]*\).*/\1/' || echo 0)

echo "  • Ruff: $ruff_issues issues"
echo "  • Mypy: $mypy_errors errors"
echo "  • Radon: $radon_funcs funções complexas"
echo "  • Pylint: $pylint_issues issues"
echo "  • Bandit: $bandit_vulns vulnerabilidades"

# 4. Top ferramentas com avisos
echo ""
echo "[4/6] Identificando ferramentas com mais avisos..."
grep "\[WARN\]" "$CURRENT_LOG" 2>/dev/null | \
  sed 's/.*\] //' | \
  cut -d: -f1 | \
  sort | uniq -c | sort -rn | head -10 > "$OUTPUT_DIR/top_warnings_${TIMESTAMP}.txt"

echo "  ✅ Top avisos: $OUTPUT_DIR/top_warnings_${TIMESTAMP}.txt"

# 5. Gerar relatório consolidado
echo ""
echo "[5/6] Gerando relatório consolidado..."

cat > "$OUTPUT_DIR/CONSOLIDATED_REPORT_${TIMESTAMP}.md" << ENDREPORT
# Relatório Consolidado - Quality Pipeline v2.3
**Data:** $(date '+%Y-%m-%d %H:%M:%S')

---

## ��� Estatísticas Gerais

| Métrica | Valor |
|---------|-------|
| Total de Logs Arquivados | $ARCHIVED_LOGS |
| [INFO] no último run | $INFO_COUNT |
| [WARN] no último run | $WARN_COUNT |
| [ERROR] no último run | $ERROR_COUNT |
| Ferramentas não instaladas | $MISSING_COUNT |

## ��� Issues Detectados

| Ferramenta | Issues |
|------------|--------|
| Ruff | $ruff_issues |
| Mypy | $mypy_errors |
| Radon (complexidade > 10) | $radon_funcs |
| Pylint | $pylint_issues |
| Bandit (segurança) | $bandit_vulns |

## ��� Ferramentas Não Disponíveis

$(cat "$OUTPUT_DIR/missing_tools_${TIMESTAMP}.txt" | sed 's/^/- /')

## ⚠️ Top 10 Ferramentas com Mais Avisos

$(cat "$OUTPUT_DIR/top_warnings_${TIMESTAMP}.txt" | awk '{print "- " $2 ": " $1 " avisos"}')

## ��� Arquivos Gerados

- Ferramentas ausentes: \`$OUTPUT_DIR/missing_tools_${TIMESTAMP}.txt\`
- Top avisos: \`$OUTPUT_DIR/top_warnings_${TIMESTAMP}.txt\`
- Relatório consolidado: \`$OUTPUT_DIR/CONSOLIDATED_REPORT_${TIMESTAMP}.md\`

---

*Relatório gerado automaticamente pelo processador de logs v2.3*
ENDREPORT

echo "  ✅ Relatório: $OUTPUT_DIR/CONSOLIDATED_REPORT_${TIMESTAMP}.md"

# 6. Arquivar log atual
echo ""
echo "[6/6] Arquivando log atual..."
cp "$CURRENT_LOG" "$ARCHIVE_DIR/quality_${TIMESTAMP}.log" 2>/dev/null
echo "  ✅ Log arquivado: $ARCHIVE_DIR/quality_${TIMESTAMP}.log"

echo ""
echo "=== Processamento Concluído ==="
echo ""
echo "��� Arquivos gerados:"
ls -lh "$OUTPUT_DIR"/*_${TIMESTAMP}.* 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'
