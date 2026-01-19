# Quality Pipeline TODOs (derived from quality_pipeline_v1.md)

## Semana 1-2 — Quick Wins
- [x] Criar diretório `tools/quality_scripts/` e `__init__.py`
- [x] Extrair `index_symbols.py`
- [x] Extrair `normalize_issues.py`
- [x] Atualizar `quality.sh` para usar scripts externos
- [x] Testar `./quality.sh --dry-run --verbose`
- [ ] Instalar `pre-commit`
- [x] Adicionar `.pre-commit-config.yaml`
- [ ] Rodar `pre-commit run --all-files`
- [x] Instalar `uv`
- [ ] Testar `uv pip install -r requirements.txt`
- [x] Atualizar `quality.sh` para detectar `uv`

## Semana 3-4 — Paralelização
- [ ] Instalar GNU Parallel
- [x] Adicionar `export_functions()` no `quality.sh`
- [x] Rodar baseline em paralelo
- [ ] Medir tempo: `time ./quality.sh --dry-run`
- [x] Adicionar `get_python_hash()`
- [x] Adicionar `run_with_cache()`
- [x] Usar cache em ruff/mypy/radon
- [x] Testar cache (2 execuções seguidas)

## Semana 5-6 — Task Migration
- [ ] Instalar Task (Go 1.19+)
- [ ] Criar `Taskfile.yml`
- [ ] Migrar tasks: `ruff:check`, `mypy:check`, `radon:check`
- [ ] Migrar task `tests`
- [ ] Testar `task quality:check`
- [ ] Adicionar utilidades (clean, snapshot)
- [ ] Documentar Task no README

## Opcional — Ferramentas Avançadas
- [ ] Instalar `watchexec` e testar auto-run
- [ ] Instalar `hyperfine` e rodar benchmark (quality.sh vs Task)
- [ ] Avaliar Earthly (criar Earthfile) para CI/CD
