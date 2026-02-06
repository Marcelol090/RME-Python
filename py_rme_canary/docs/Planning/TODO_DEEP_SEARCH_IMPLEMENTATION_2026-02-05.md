# TODO Deep Search + Parity C++/Lua - 2026-02-05

Escopo consolidado a partir da varredura de:
- `remeres-map-editor-redux/source/` (referencia C++/Lua)
- `awesome-copilot/` e `codex/` (workflow/operacao)
- `py_rme_canary/docs/Planning/Features.md` (features alvo)
- `py_rme_canary/` (implementacao Python atual)

## TODO tecnico (8 tarefas)

- [x] `DS-001` Consolidar checklist de paridade C++ -> Python com foco em lacunas reais de implementacao.
- [x] `JL-001` Implementar cliente Jules API local em Python usando `JULES_API_KEY` e `JULES_SOURCE` do `.env`.
- [x] `JL-002` Implementar comando CLI de conectividade Jules (sources/sessions/latest activity) com logs sem segredo.
- [x] `JL-003` Gerar `reports/jules/suggestions.json` e `reports/jules/suggestions.md` em contrato com `.github/jules/suggestions.schema.json`.
- [x] `QF-001` Integrar Jules no `quality_lf.sh` (fluxo local: quality -> jules -> artefatos).
- [x] `QF-002` Otimizar hash/cache do pipeline para reduzir custo de IO e tempo de processamento.
- [x] `DOC-001` Atualizar documentacao operacional de Jules + troubleshooting no pipeline.
- [x] `VAL-001` Rodar validacao completa: `quality_lf.sh`, checks equivalentes ao CI e testes unitarios.

## Estado de paridade (resumo)

### Ja coberto no Python
- [x] OTBM v5/v6 com traducao ClientID/ServerID
- [x] Cross-instance clipboard com sprite hash (FNV-1a)
- [x] Lasso/freehand e modos de selecao
- [x] Import Lua de monster/NPC
- [x] Quick replace no contexto + dialog
- [x] OTMM/minimap export
- [x] Client profiles com persistencia e ativacao

### Parcial/pendente
- [ ] `BORDER-001` Border Builder com edicao persistente de regras (nao apenas visualizacao)
- [x] `WF-001` Execucao local equivalente aos workflows GitHub com consolidacao de artefatos

## TODO operacional Jules API (8 tarefas) - 2026-02-06

- [x] `JL-OPS-001` Validar documentação oficial atual da Jules API (sources/sessions/activities/approvePlan/sendMessage).
- [x] `JL-OPS-002` Expandir `jules_api.py` com listagem paginada de atividades e sessões.
- [x] `JL-OPS-003` Implementar ações de sessão (`approvePlan`, `sendMessage`) no cliente local.
- [x] `JL-OPS-004` Adicionar comandos CLI no `jules_runner.py` para monitorar e operar sessões.
- [x] `JL-OPS-005` Melhorar extração de contrato `implemented/suggested_next` com fallback mais robusto.
- [x] `JL-OPS-006` Cobrir novos fluxos com testes unitários de scripts Jules.
- [x] `JL-OPS-007` Validar conectividade real usando `JULES_API_KEY` e `JULES_SOURCE` do `.env`.
- [x] `JL-OPS-008` Atualizar guias operacionais e registrar conclusão no TODO.
