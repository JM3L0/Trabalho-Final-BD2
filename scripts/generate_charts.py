"""Gera graficos em 300 DPI a partir dos dados estatisticos e brutos dos benchmarks."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.db import PAPER_DIR, RESULTS_DIR
from scripts.queries import QUERIES

COLOR_BASE = "#2B4C7E"
COLOR_OPT = "#2A8C62"
COLOR_INTER = "#D97706"
COLOR_WARN = "#C0392B"


def configure_style() -> None:
    """Padroniza estilo academico limpo para figuras em 300 DPI."""
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linestyle": "--",
        }
    )


def save_figure(fig: plt.Figure, filename: str) -> list[Path]:
    """Salva figura em paper/figures/ e results/charts/ em 300 DPI."""
    outputs: list[Path] = []
    for folder in (PAPER_DIR / "figures", RESULTS_DIR / "charts"):
        folder.mkdir(parents=True, exist_ok=True)
        out = folder / filename
        fig.savefig(out, dpi=300, bbox_inches="tight")
        outputs.append(out)
    plt.close(fig)
    return outputs


def plot_logical_reads(summary: dict[str, Any]) -> list[Path]:
    """Figura 1: Leituras logicas medianas em Warm Cache (escala log10)."""
    warm = summary["cache_modes"]["warm"]
    codes = [q.code for q in QUERIES]
    base_reads = [float(warm[c]["baseline"]["logical_reads"]["median"]) for c in codes]
    opt_reads = [float(warm[c]["optimized"]["logical_reads"]["median"]) for c in codes]
    io_pcts = [float(warm[c]["comparison"]["io_reduction_pct"]) for c in codes]

    x = np.arange(len(codes))
    width = 0.36

    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    bars_base = ax.bar(x - width / 2, base_reads, width, label="Baseline (sem índices secundários)", color=COLOR_BASE)
    opt_colors = [COLOR_WARN if c == "W1" else COLOR_OPT for c in codes]
    bars_opt = ax.bar(x + width / 2, opt_reads, width, label="Otimizado (9 índices + reescritas)", color=opt_colors)

    ax.set_yscale("log")
    ax.set_ylim(1, max(max(base_reads), max(opt_reads)) * 6.0)
    ax.set_xticks(x)
    ax.set_xticklabels(codes)
    ax.set_ylabel("Leituras Lógicas (páginas de 8 KB, escala log)")
    ax.set_title("Comparativo de Leituras Lógicas em Warm Cache (N = 30)")

    # Legenda customizada incluindo barra de overhead de escrita
    from matplotlib.patches import Patch

    legend_handles = [
        Patch(facecolor=COLOR_BASE, label="Baseline (apenas PKs clusterizadas)"),
        Patch(facecolor=COLOR_OPT, label="Otimizado (ganho de leitura)"),
        Patch(facecolor=COLOR_WARN, label="Otimizado (overhead de escrita W1)"),
    ]
    ax.legend(handles=legend_handles, loc="upper left", frameon=True)

    for idx, (b_b, b_o, pct) in enumerate(zip(bars_base, bars_opt, io_pcts)):
        top_y = max(b_b.get_height(), b_o.get_height()) * 1.28
        if pct < 0:
            label = f"+{abs(pct):.1f}%"
        elif pct >= 99.9:
            label = f"-{pct:.2f}%"
        else:
            label = f"-{pct:.1f}%"
        color = COLOR_WARN if pct < 0 else "#1B5E20"
        ax.text(
            x[idx],
            top_y,
            label,
            ha="center",
            va="bottom",
            fontsize=7.8,
            fontweight="bold",
            color=color,
        )

    ax.axvline(9.5, color="#666666", linestyle=":", linewidth=1.1)
    ax.text(9.6, max(opt_reads) * 2.8, "Escrita\nOLTP", fontsize=8, color="#555555")

    return save_figure(fig, "fig1_leituras_logicas.png")


def plot_execution_time_boxplots(raw_runs: list[dict[str, Any]]) -> list[Path]:
    """Figura 2: Distribuicao de tempo de execucao em Warm Cache (2 paineis)."""
    grouped: dict[tuple[str, str], list[float]] = {}
    for row in raw_runs:
        if row["cache_mode"] != "warm":
            continue
        grouped.setdefault((row["query_code"], row["scenario"]), []).append(float(row["elapsed_time_ms"]))

    fast_codes = ["Q1", "Q2", "Q3", "Q4", "Q6", "Q8"]
    heavy_codes = ["Q5", "Q7", "Q9", "Q10", "W1"]

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.5), gridspec_kw={"width_ratios": [6, 5]})

    for ax, codes, panel_title in (
        (axes[0], fast_codes, "(a) Consultas OLTP Seletivas (Q1–Q4, Q6, Q8)"),
        (axes[1], heavy_codes, "(b) Consultas Analíticas e Escrita (Q5, Q7, Q9, Q10, W1)"),
    ):
        pos = np.arange(len(codes))
        base_data = [grouped[(c, "baseline")] for c in codes]
        opt_data = [grouped[(c, "optimized")] for c in codes]

        bp1 = ax.boxplot(
            base_data,
            positions=pos - 0.18,
            widths=0.30,
            patch_artist=True,
            showfliers=True,
            flierprops={"marker": "o", "markersize": 3, "alpha": 0.45},
            medianprops={"color": "#111111", "linewidth": 1.3},
        )
        bp2 = ax.boxplot(
            opt_data,
            positions=pos + 0.18,
            widths=0.30,
            patch_artist=True,
            showfliers=True,
            flierprops={"marker": "o", "markersize": 3, "alpha": 0.45},
            medianprops={"color": "#111111", "linewidth": 1.3},
        )

        for patch in bp1["boxes"]:
            patch.set_facecolor(COLOR_BASE)
            patch.set_alpha(0.85)
        for idx, patch in enumerate(bp2["boxes"]):
            code = codes[idx]
            patch.set_facecolor(COLOR_WARN if code in {"Q7", "W1"} else COLOR_OPT)
            patch.set_alpha(0.85)

        ax.set_xticks(pos)
        ax.set_xticklabels(codes)
        ax.set_ylabel("Tempo Decorrrido SQL Server (ms)".replace("Decorrrido", "Decorrido"))
        ax.set_title(panel_title)

    from matplotlib.patches import Patch

    axes[0].legend(
        handles=[
            Patch(facecolor=COLOR_BASE, alpha=0.85, label="Baseline"),
            Patch(facecolor=COLOR_OPT, alpha=0.85, label="Otimizado (ganho)"),
            Patch(facecolor=COLOR_WARN, alpha=0.85, label="Otimizado (trade-off)"),
        ],
        loc="upper left",
        frameon=True,
    )
    fig.suptitle("Distribuição de Latência em Warm Cache (N = 30 por cenário)", fontsize=12, fontweight="bold", y=1.02)
    return save_figure(fig, "fig2_tempos_execucao_boxplot.png")


def plot_q4_three_stage(summary: dict[str, Any]) -> list[Path]:
    """Figura 3: Evolucao em 3 estagios da consulta Q4 (eliminacao de Key Lookup)."""
    warm_q4 = summary["cache_modes"]["warm"]["Q4"]
    q4_inter = summary["q4_three_stage"]

    stages = [
        "1. Baseline\n(Clustered\nScan)",
        "2. Intermediário\n(Seek +\nKey Lookup)",
        "3. Otimizado\n(Covering Index\nINCLUDE)",
    ]
    reads = [
        float(warm_q4["baseline"]["logical_reads"]["median"]),
        float(q4_inter["metrics"]["logical_reads"]),
        float(warm_q4["optimized"]["logical_reads"]["median"]),
    ]
    times = [
        float(warm_q4["baseline"]["elapsed_time_ms"]["median"]),
        float(q4_inter["metrics"]["elapsed_time_ms"]),
        float(warm_q4["optimized"]["elapsed_time_ms"]["median"]),
    ]
    colors = [COLOR_BASE, COLOR_INTER, COLOR_OPT]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 4.3))

    b1 = ax1.bar(stages, reads, color=colors, width=0.52)
    ax1.set_ylabel("Leituras Lógicas (páginas de 8 KB)")
    ax1.set_title("(a) Redução Progressiva de E/S em Q4")
    ax1.set_ylim(0, max(reads) * 1.18)
    for bar, val in zip(b1, reads):
        ax1.text(bar.get_x() + bar.get_width() / 2, val + 180, f"{int(val):,}".replace(",", "."), ha="center", fontweight="bold")

    b2 = ax2.bar(stages, [max(t, 0.25) for t in times], color=colors, width=0.52)
    ax2.set_ylabel("Tempo Decorrido Mediano (ms)")
    ax2.set_title("(b) Redução de Latência em Q4")
    ax2.set_ylim(0, max(times) * 1.2)
    for bar, val in zip(b2, times):
        lbl = "< 1 ms" if val == 0.0 else f"{val:.1f} ms".replace(".", ",")
        ax2.text(bar.get_x() + bar.get_width() / 2, max(val, 0.25) + 2.5, lbl, ha="center", fontweight="bold")

    fig.suptitle("Estudo de Caso Q4: Custo do Key Lookup e Benefício do Covering Index", fontsize=11.5, fontweight="bold", y=1.03)
    return save_figure(fig, "fig3_q4_tres_estagios.png")


def plot_warm_vs_cold(summary: dict[str, Any]) -> list[Path]:
    """Figura 4: Comparativo Warm Cache (N=30) vs Cold Cache (N=10)."""
    warm = summary["cache_modes"]["warm"]
    cold = summary["cache_modes"]["cold"]
    rep_codes = ["Q1", "Q3", "Q5", "Q7", "Q9", "W1"]

    x = np.arange(len(rep_codes))
    w = 0.20

    warm_base = [max(float(warm[c]["baseline"]["elapsed_time_ms"]["median"]), 0.5) for c in rep_codes]
    warm_opt = [max(float(warm[c]["optimized"]["elapsed_time_ms"]["median"]), 0.5) for c in rep_codes]
    cold_base = [max(float(cold[c]["baseline"]["elapsed_time_ms"]["median"]), 0.5) for c in rep_codes]
    cold_opt = [max(float(cold[c]["optimized"]["elapsed_time_ms"]["median"]), 0.5) for c in rep_codes]

    fig, ax = plt.subplots(figsize=(10.2, 4.4))
    ax.bar(x - 1.5 * w, warm_base, w, label="Warm Baseline (N=30)", color="#5C7CFA")
    ax.bar(x - 0.5 * w, cold_base, w, label="Cold Baseline (N=10)", color=COLOR_BASE)
    ax.bar(x + 0.5 * w, warm_opt, w, label="Warm Otimizado (N=30)", color="#51CF66")
    ax.bar(x + 1.5 * w, cold_opt, w, label="Cold Otimizado (N=10)", color=COLOR_OPT)

    ax.set_yscale("log")
    ax.set_ylim(0.3, max(cold_opt + cold_base) * 14.0)
    ax.set_xticks(x)
    ax.set_xticklabels(rep_codes)
    ax.set_ylabel("Tempo Mediano SQL Server (ms, escala log)")
    ax.set_title("Impacto do Estado de Cache (Warm vs. Cold) nas Consultas Representativas")
    ax.legend(ncol=2, loc="upper left", frameon=True)

    return save_figure(fig, "fig4_warm_vs_cold_cache.png")


def generate_all_charts() -> list[Path]:
    """Carrega dados processados e gera todas as 4 figuras estatisticas."""
    configure_style()
    summary = json.loads((RESULTS_DIR / "summary_stats.json").read_text(encoding="utf-8"))
    raw_runs = json.loads((RESULTS_DIR / "benchmark_runs.json").read_text(encoding="utf-8"))["runs"]

    generated: list[Path] = []
    generated.extend(plot_logical_reads(summary))
    generated.extend(plot_execution_time_boxplots(raw_runs))
    generated.extend(plot_q4_three_stage(summary))
    generated.extend(plot_warm_vs_cold(summary))
    return generated


def main() -> int:
    paths = generate_all_charts()
    for p in paths:
        print(f"Gerado: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
