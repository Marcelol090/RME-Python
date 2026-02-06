#!/usr/bin/env python3
import subprocess
import time
import sys
from pathlib import Path

# Ferramentas a testar
tools = {
    'Ruff': ['ruff', 'check', 'py_rme_canary/core', '--exit-zero'],
    'Mypy': ['mypy', 'py_rme_canary/core', '--config-file', 'pyproject.toml', '--cache-dir', '.mypy_cache'],
    'Radon': ['radon', 'cc', 'py_rme_canary/core', '--min', 'B'],
    'Pyright': ['pyright', 'py_rme_canary/core'],
    'Bandit': ['bandit', '-q', '-r', 'py_rme_canary/core'],
    'Lizard (otimizado)': ['python', '-m', 'lizard', 'py_rme_canary/core', 'py_rme_canary/logic_layer', '--CCN', '15', '--exclude', '*/test_*'],
    'Lizard (SEM otimização)': ['python', '-m', 'lizard', 'py_rme_canary', '--CCN', '15'],
}

print("=== MEDIÇÃO DE PERFORMANCE DAS FERRAMENTAS ===\n")
print(f"{'Ferramenta':<25} {'Tempo (s)':<12} {'Status':<15} {'Observação'}")
print("=" * 80)

results = {}

for tool_name, command in tools.items():
    try:
        start = time.time()

        # Timeout de 60 segundos
        result = subprocess.run(
            command,
            capture_output=True,
            timeout=60,
            cwd='/c/Users/Marcelo Henrique/Desktop/projec_rme'
        )

        duration = time.time() - start
        results[tool_name] = duration

        if duration < 10:
            status = "✓ RÁPIDO"
            obs = "OK"
        elif duration < 30:
            status = "⚡ MÉDIO"
            obs = "Aceitável"
        elif duration < 60:
            status = "⏱️  LENTO"
            obs = "Otimizar"
        else:
            status = "❌ MUITO LENTO"
            obs = "CRÍTICO"

        print(f"{tool_name:<25} {duration:<12.2f} {status:<15} {obs}")

    except subprocess.TimeoutExpired:
        print(f"{tool_name:<25} {'TIMEOUT':<12} {'❌ TRAVADO':<15} '>60s - CRÍTICO!'")
        results[tool_name] = 999
    except FileNotFoundError:
        print(f"{tool_name:<25} {'-':<12} {'⚠ N/D':<15} 'Não instalado'")
    except Exception as e:
        print(f"{tool_name:<25} {'-':<12} {'❌ ERRO':<15} {str(e)[:30]}")

print("=" * 80)
print(f"\n��� Resumo:")
total_time = sum(v for v in results.values() if v < 900)
print(f"   Tempo total: {total_time:.2f}s ({total_time/60:.1f} minutos)")
print(f"   Ferramentas medidas: {len([v for v in results.values() if v < 900])}")
