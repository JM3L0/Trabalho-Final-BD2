"""Analise estatistica dos benchmarks BD2 (Warm N=30 e Cold N=10) e geracao de tabela LaTeX."""

from __future__ import annotations

import csv
import json
import sys
import warnings
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.db import PAPER_DIR, RESULTS_DIR, ROOT_DIR
from scripts.queries import QUERIES, QUERY_MAP

METRICS_TO_SUMMARIZE = (
    "elapsed_time_ms",
    "cpu_time_ms",
    "logical_reads",
    "physical_reads",
    "read_ahead_reads",
    "wall_time_ms",
)


def compute_descriptive(values: list[float]) -> dict[str, float | int]:
    """Calcula estatisticas descritivas e IC 95% (t-Student) para uma serie."""
    arr = np.asarray(values, dtype=float)
    n = int(arr.size)
    if n == 0:
        raise ValueError("Serie vazia para calculo descritivo.")
    mean = float(np.mean(arr))
    median = float(np.median(arr))
    std = float(np.std(arr, ddof=1)) if n > 1 else 0.0
    q25, q75 = (float(x) for x in np.percentile(arr, [25, 75]))
    iqr = q75 - q25
    if n > 1 and std > 0.0:
        se = std / np.sqrt(n)
        ci_low, ci_high = (float(x) for x in stats.t.interval(0.95, df=n - 1, loc=mean, scale=se))
    else:
        ci_low, ci_high = mean, mean
    return {
        "n": n,
        "mean": round(mean, 4),
        "median": round(median, 4),
        "std": round(std, 4),
        "min": round(float(np.min(arr)), 4),
        "max": round(float(np.max(arr)), 4),
        "q25": round(q25, 4),
        "q75": round(q75, 4),
        "iqr": round(iqr, 4),
        "ci95_low": round(ci_low, 4),
        "ci95_high": round(ci_high, 4),
    }


def compute_paired_test(base_vals: list[float], opt_vals: list[float]) -> dict[str, Any]:
    """Executa Shapiro-Wilk nas diferencas e escolhe t-test pareado ou Wilcoxon."""
    base = np.asarray(base_vals, dtype=float)
    opt = np.asarray(opt_vals, dtype=float)
    diffs = base - opt
    n = int(diffs.size)

    if n < 3 or float(np.ptp(diffs)) == 0.0:
        # Diferenca constante (ex.: logical_reads deterministicos)
        all_zero = bool(np.all(diffs == 0.0))
        return {
            "shapiro_stat": 1.0,
            "shapiro_p": 1.0,
            "is_normal_diff": True,
            "test_used": "Constante (sem variancia nas diferencas)",
            "statistic": 0.0,
            "p_value": 1.0 if all_zero else 0.0,
            "significant_005": not all_zero,
        }

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sh_stat, sh_p = stats.shapiro(diffs)
    is_normal = bool(float(sh_p) >= 0.05)

    if is_normal:
        t_stat, p_val = stats.ttest_rel(base, opt)
        test_used = "t-Student pareado"
        stat_val = float(t_stat)
        p_float = float(p_val)
    else:
        w_stat, p_val = stats.wilcoxon(diffs, zero_method="wilcox", alternative="two-sided")
        test_used = "Wilcoxon pareado"
        stat_val = float(w_stat)
        p_float = float(p_val)

    return {
        "shapiro_stat": round(float(sh_stat), 6),
        "shapiro_p": float(f"{float(sh_p):.6g}"),
        "is_normal_diff": is_normal,
        "test_used": test_used,
        "statistic": round(stat_val, 6),
        "p_value": float(f"{p_float:.6g}"),
        "significant_005": bool(p_float < 0.05),
    }


def format_p_value_latex(p_val: float) -> str:
    """Formata p-valor de maneira compacta para tabela LaTeX."""
    if p_val < 0.0001:
        return "$<10^{-4}$"
    if p_val < 0.001:
        return f"{p_val:.4f}".replace(".", ",")
    return f"{p_val:.3f}".replace(".", ",")


def format_num_br(val: float, decimals: int = 1) -> str:
    """Formata numero para apresentacao em LaTeX/Markdown com separador de milhar."""
    if decimals == 0:
        return f"{int(round(val)):,}".replace(",", ".")
    return f"{val:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build_speedup_info(base_med: float, opt_med: float, base_mean: float, opt_mean: float) -> dict[str, Any]:
    """Calcula speedup por mediana/media tratando resolucao < 1 ms do SQL Server."""
    if opt_med > 0.0:
        sp_med: float | None = round(base_med / opt_med, 2)
        sp_label = f"{base_med / opt_med:.1f}x" if (base_med / opt_med) >= 10 else f"{base_med / opt_med:.2f}x"
    else:
        sp_med = None
        # Valores 0 ms no SQL Server correspondem a < 0,5 ms (limite conservador < 1 ms)
        sp_label = f">{base_med:.0f}x (<1 ms)"

    sp_mean: float | None = round(base_mean / opt_mean, 2) if opt_mean > 0.0 else None
    return {
        "speedup_median": sp_med,
        "speedup_mean": sp_mean,
        "speedup_display": sp_label,
    }


def analyze() -> tuple[Path, Path, Path]:
    """Processa benchmark_runs.json e gera JSON, CSV e fragmento LaTeX."""
    runs_path = RESULTS_DIR / "benchmark_runs.json"
    raw = json.loads(runs_path.read_text(encoding="utf-8"))
    runs: list[dict[str, Any]] = raw["runs"]

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in runs:
        key = (row["cache_mode"], row["query_code"], row["scenario"])
        grouped.setdefault(key, []).append(row)

    for key in grouped:
        grouped[key].sort(key=lambda r: int(r["run_index"]))

    summary: dict[str, Any] = {
        "metadata": raw["metadata"],
        "cache_modes": {},
        "q4_three_stage": None,
    }

    q4_inter_path = RESULTS_DIR / "q4_intermediate.json"
    if q4_inter_path.exists():
        summary["q4_three_stage"] = json.loads(q4_inter_path.read_text(encoding="utf-8"))

    csv_rows: list[dict[str, Any]] = []

    for cache_mode in ("warm", "cold"):
        mode_dict: dict[str, Any] = {}
        for query in QUERIES:
            base_rows = grouped[(cache_mode, query.code, "baseline")]
            opt_rows = grouped[(cache_mode, query.code, "optimized")]

            base_stats = {
                m: compute_descriptive([float(r[m]) for r in base_rows]) for m in METRICS_TO_SUMMARIZE
            }
            opt_stats = {
                m: compute_descriptive([float(r[m]) for r in opt_rows]) for m in METRICS_TO_SUMMARIZE
            }

            test_elapsed = compute_paired_test(
                [float(r["elapsed_time_ms"]) for r in base_rows],
                [float(r["elapsed_time_ms"]) for r in opt_rows],
            )
            test_wall = compute_paired_test(
                [float(r["wall_time_ms"]) for r in base_rows],
                [float(r["wall_time_ms"]) for r in opt_rows],
            )
            test_reads = compute_paired_test(
                [float(r["logical_reads"]) for r in base_rows],
                [float(r["logical_reads"]) for r in opt_rows],
            )

            base_reads_mean = float(base_stats["logical_reads"]["mean"])
            opt_reads_mean = float(opt_stats["logical_reads"]["mean"])
            base_reads_med = float(base_stats["logical_reads"]["median"])
            opt_reads_med = float(opt_stats["logical_reads"]["median"])
            io_reduction_pct = round(((base_reads_med - opt_reads_med) / base_reads_med) * 100.0, 2)
            io_reduction_mean_pct = round(((base_reads_mean - opt_reads_mean) / base_reads_mean) * 100.0, 2)

            sp_elapsed = build_speedup_info(
                float(base_stats["elapsed_time_ms"]["median"]),
                float(opt_stats["elapsed_time_ms"]["median"]),
                float(base_stats["elapsed_time_ms"]["mean"]),
                float(opt_stats["elapsed_time_ms"]["mean"]),
            )
            wall_base_med = float(base_stats["wall_time_ms"]["median"])
            wall_opt_med = float(opt_stats["wall_time_ms"]["median"])
            wall_speedup_med = round(wall_base_med / wall_opt_med, 2) if wall_opt_med > 0 else None

            mode_dict[query.code] = {
                "title": query.title,
                "category": query.category,
                "is_dml_write": query.is_dml_write,
                "row_count": int(base_rows[0]["row_count"]),
                "baseline": base_stats,
                "optimized": opt_stats,
                "comparison": {
                    "io_reduction_pct": io_reduction_pct,
                    "io_reduction_mean_pct": io_reduction_mean_pct,
                    "speedup_elapsed_median": sp_elapsed["speedup_median"],
                    "speedup_elapsed_mean": sp_elapsed["speedup_mean"],
                    "speedup_elapsed_display": sp_elapsed["speedup_display"],
                    "speedup_wall_median": wall_speedup_med,
                    "test_elapsed": test_elapsed,
                    "test_wall": test_wall,
                    "test_logical_reads": test_reads,
                },
            }

            csv_rows.append(
                {
                    "cache_mode": cache_mode,
                    "query_code": query.code,
                    "n": base_stats["elapsed_time_ms"]["n"],
                    "row_count": int(base_rows[0]["row_count"]),
                    "base_reads_median": base_stats["logical_reads"]["median"],
                    "opt_reads_median": opt_stats["logical_reads"]["median"],
                    "base_reads_mean": base_stats["logical_reads"]["mean"],
                    "opt_reads_mean": opt_stats["logical_reads"]["mean"],
                    "io_reduction_pct": io_reduction_pct,
                    "base_elapsed_median_ms": base_stats["elapsed_time_ms"]["median"],
                    "base_elapsed_mean_ms": base_stats["elapsed_time_ms"]["mean"],
                    "base_elapsed_std_ms": base_stats["elapsed_time_ms"]["std"],
                    "opt_elapsed_median_ms": opt_stats["elapsed_time_ms"]["median"],
                    "opt_elapsed_mean_ms": opt_stats["elapsed_time_ms"]["mean"],
                    "opt_elapsed_std_ms": opt_stats["elapsed_time_ms"]["std"],
                    "speedup_elapsed_display": sp_elapsed["speedup_display"],
                    "speedup_wall_median": wall_speedup_med,
                    "test_used": test_elapsed["test_used"],
                    "p_value_elapsed": test_elapsed["p_value"],
                    "p_value_wall": test_wall["p_value"],
                }
            )
        summary["cache_modes"][cache_mode] = mode_dict

    summary_json = RESULTS_DIR / "summary_stats.json"
    summary_json.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    summary_csv = RESULTS_DIR / "summary_table.csv"
    with summary_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(csv_rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(csv_rows)

    # Fragmento LaTeX unificado (Warm Cache N=30) gerado automaticamente dos resultados medidos
    gen_dir = PAPER_DIR / "generated"
    gen_dir.mkdir(parents=True, exist_ok=True)
    tex_path = gen_dir / "tabela_resultados.tex"

    warm = summary["cache_modes"]["warm"]
    lines = [
        "% Gerado automaticamente por scripts/analyze_results.py (Warm Cache N=30)",
        "\\begin{table}[ht]",
        "\\centering",
        "\\caption{Comparativo de desempenho em \\textit{Warm Cache} ($N=30$): Leituras Lógicas, Tempo de Execução (mediana $\\pm$ DP), Redução de E/S, \\textit{Speedup} e significância estatística.}",
        "\\label{tab:resultados-warm}",
        "\\scriptsize",
        "\\setlength{\\tabcolsep}{3.5pt}",
        "\\begin{tabular}{lrrrrrrr}",
        "\\toprule",
        "\\textbf{Cons.} & \\textbf{Leit. Base} & \\textbf{Leit. Otim.} & \\textbf{Red. E/S} & \\textbf{Tempo Base (ms)} & \\textbf{Tempo Otim. (ms)} & \\textbf{Speedup} & \\textbf{$p$-valor} \\\\",
        "\\midrule",
    ]
    for query in QUERIES:
        item = warm[query.code]
        b_reads = format_num_br(float(item["baseline"]["logical_reads"]["median"]), 0)
        o_reads = format_num_br(float(item["optimized"]["logical_reads"]["median"]), 0)
        io_pct = float(item["comparison"]["io_reduction_pct"])
        io_str = f"{io_pct:+.2f}\\%".replace(".", ",") if io_pct < 0 else f"{io_pct:.2f}\\%".replace(".", ",")
        b_t = (
            f"{format_num_br(float(item['baseline']['elapsed_time_ms']['median']), 1)}"
            f" $\\pm$ {format_num_br(float(item['baseline']['elapsed_time_ms']['std']), 1)}"
        )
        o_med_val = float(item["optimized"]["elapsed_time_ms"]["median"])
        o_std_val = float(item["optimized"]["elapsed_time_ms"]["std"])
        o_med_str = "$<1$" if o_med_val == 0.0 else format_num_br(o_med_val, 1)
        o_t = f"{o_med_str} $\\pm$ {format_num_br(o_std_val, 1)}"
        sp_str = str(item["comparison"]["speedup_elapsed_display"]).replace(".", ",").replace("<1 ms", "$<$1 ms").replace(">", "$>$")
        p_str = format_p_value_latex(float(item["comparison"]["test_elapsed"]["p_value"]))
        code_lbl = f"\\textbf{{{query.code}}}" if query.code in {"Q7", "W1"} else query.code
        if query.code == "W1":
            lines.append("\\midrule")
        lines.append(
            f"{code_lbl} & {b_reads} & {o_reads} & {io_str} & {b_t} & {o_t} & {sp_str} & {p_str} \\\\"
        )

    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table}",
            "",
        ]
    )
    tex_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    return summary_json, summary_csv, tex_path


def update_cerebro_results(summary_json: Path) -> Path:
    """Atualiza cerebro/06-experimentacao/registro-resultados.md com os numeros reais."""
    data = json.loads(summary_json.read_text(encoding="utf-8"))
    warm = data["cache_modes"]["warm"]
    cold = data["cache_modes"]["cold"]

    md_lines = [
        "# Registro de Resultados Experimentais",
        "",
        f"- **Data de execucao:** {data['metadata']['generated_at_utc']}",
        f"- **Motor:** `{data['metadata']['sql_version']}`",
        "- **Hardware do host:** Windows 11 Home Single Language | 12th Gen Intel Core i5-1235U (10 nucleos / 12 threads) | 15,71 GB RAM | SSD",
        f"- **Protocolo:** `OPTION (MAXDOP 1)` | Warm Cache: `N = {data['metadata']['warm_runs']}` (apos `{data['metadata']['warmups_discarded']}` aquecimentos) | Cold Cache: `N = {data['metadata']['cold_runs']}` (`CHECKPOINT; DBCC DROPCLEANBUFFERS; DBCC FREEPROCCACHE;`)",
        "",
        "## Resultados Consolidados — Warm Cache (N = 30)",
        "",
        "| Consulta | Leituras Base (med) | Leituras Otim. (med) | Reducao E/S | Tempo Base med (ms) | Tempo Otim. med (ms) | Speedup | Teste / p-valor |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |",
    ]
    for query in QUERIES:
        it = warm[query.code]
        t_el = it["comparison"]["test_elapsed"]
        md_lines.append(
            f"| {query.code} | {it['baseline']['logical_reads']['median']:.0f} | "
            f"{it['optimized']['logical_reads']['median']:.0f} | "
            f"{it['comparison']['io_reduction_pct']:.2f}% | "
            f"{it['baseline']['elapsed_time_ms']['median']:.1f} (DP {it['baseline']['elapsed_time_ms']['std']:.1f}) | "
            f"{it['optimized']['elapsed_time_ms']['median']:.1f} (DP {it['optimized']['elapsed_time_ms']['std']:.1f}) | "
            f"{it['comparison']['speedup_elapsed_display']} | "
            f"{t_el['test_used']} (p={t_el['p_value']:.4g}) |"
        )

    md_lines.extend(
        [
            "",
            "## Resultados Consolidados — Cold Cache (N = 10)",
            "",
            "| Consulta | Leituras Base (med) | Leituras Otim. (med) | Reducao E/S | Tempo Base med (ms) | Tempo Otim. med (ms) | Speedup | p-valor |",
            "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for query in QUERIES:
        it = cold[query.code]
        t_el = it["comparison"]["test_elapsed"]
        md_lines.append(
            f"| {query.code} | {it['baseline']['logical_reads']['median']:.0f} | "
            f"{it['optimized']['logical_reads']['median']:.0f} | "
            f"{it['comparison']['io_reduction_pct']:.2f}% | "
            f"{it['baseline']['elapsed_time_ms']['median']:.1f} | "
            f"{it['optimized']['elapsed_time_ms']['median']:.1f} | "
            f"{it['comparison']['speedup_elapsed_display']} | "
            f"{t_el['p_value']:.4g} |"
        )

    q4_inter = data.get("q4_three_stage")
    if q4_inter:
        md_lines.extend(
            [
                "",
                "## Evolucao em 3 Estagios de Q4 (Eliminacao de Key Lookup)",
                "",
                f"- **Baseline (`PK_Pedidos` Clustered Scan):** `{warm['Q4']['baseline']['logical_reads']['median']:.0f}` leituras logicas (`{warm['Q4']['baseline']['elapsed_time_ms']['median']:.1f}` ms mediano).",
                f"- **Intermediario (`IX_Pedidos_ClienteID` Seek + Key Lookup):** `{q4_inter['metrics']['logical_reads']}` leituras logicas (`{q4_inter['metrics']['elapsed_time_ms']}` ms).",
                f"- **Covering Index (`IX_Pedidos_ClienteID_Cov` com `INCLUDE`):** `{warm['Q4']['optimized']['logical_reads']['median']:.0f}` leituras logicas (`{warm['Q4']['optimized']['elapsed_time_ms']['median']:.1f}` ms mediano, `<1 ms`).",
            ]
        )

    md_lines.extend(
        [
            "",
            "## Achados Experimentais Criticos",
            "",
            "- **Ganhos expressivos de E/S e latencia em leituras (`Q1`–`Q6`, `Q8`–`Q10`):** Reducoes de leituras logicas entre 24,61% (`Q10`) e 99,96% (`Q6`), com aceleracao de ate >424x (`Q6`), >111x (`Q4`) e 114x (`Q8`) em *Warm Cache*.",
            "- **Trade-off real em `Q7` (Batch Mode vs Row Mode sob `MAXDOP 1`):** O indice de cobertura `IX_Pedidos_Status_Cov` reduziu as leituras logicas em 30,06% (8.090 para 5.658) e eliminou o *Hash Match* (e sua concessao de memoria), mas o operador `Stream Aggregate` resultante executou em *Row Mode* (364,0 ms medianos), ficando mais lento em CPU que o `Hash Match` em *Batch Mode on Rowstore* do Baseline (217,0 ms).",
            "- **Custo de escrita em `W1`:** A manutencao de 3 indices secundarios em `ItensPedido` elevou as leituras logicas de 97.154 para 180.057 (+85,33% em *Warm Cache*) e aumentou o tempo de insercao em lote (502,0 ms para 1.098,5 ms em *Cold Cache*).",
            "",
        ]
    )

    out_md = ROOT_DIR / "cerebro" / "06-experimentacao" / "registro-resultados.md"
    out_md.write_text("\n".join(md_lines), encoding="utf-8", newline="\n")
    return out_md


def main() -> int:
    summary_json, summary_csv, tex_path = analyze()
    out_md = update_cerebro_results(summary_json)
    print(f"Resumo JSON:  {summary_json}")
    print(f"Resumo CSV:   {summary_csv}")
    print(f"Tabela LaTeX: {tex_path}")
    print(f"Registro MD:  {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
