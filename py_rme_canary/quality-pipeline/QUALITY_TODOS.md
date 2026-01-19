# Quality Pipeline TODOs (derived from quality_pipeline_v1.md)

## Semana 1-2 — Quick Wins
- [ ] Criar diretório `tools/quality_scripts/` e `__init__.py`
- [ ] Extrair `index_symbols.py`
- [ ] Extrair `normalize_issues.py`
- [ ] Atualizar `quality.sh` para usar scripts externos
- [ ] Testar `./quality.sh --dry-run --verbose`
- [ ] Instalar `pre-commit`
- [ ] Adicionar `.pre-commit-config.yaml`
- [ ] Rodar `pre-commit run --all-files`
- [ ] Instalar `uv`
- [ ] Testar `uv pip install -r requirements.txt`
- [ ] Atualizar `quality.sh` para detectar `uv`

## Semana 3-4 — Paralelização
- [ ] Instalar GNU Parallel
- [ ] Adicionar `export_functions()` no `quality.sh`
- [ ] Rodar baseline em paralelo
- [ ] Medir tempo: `time ./quality.sh --dry-run`
- [ ] Adicionar `get_python_hash()`
- [ ] Adicionar `run_with_cache()`
- [ ] Usar cache em ruff/mypy/radon
- [ ] Testar cache (2 execuções seguidas)

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
