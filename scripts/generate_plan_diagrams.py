"""Gera diagrama comparativo de planos de execucao reais extraidos dos .sqlplan XML."""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.db import PAPER_DIR, RESULTS_DIR

NS = {"sp": "http://schemas.microsoft.com/sqlserver/2004/07/showplan"}


def parse_plan_summary(xml_path: Path) -> dict[str, str]:
    """Extrai custo total e modos de execucao reais de um arquivo .sqlplan."""
    root = ET.parse(xml_path).getroot()
    first_relop = root.find(".//sp:RelOp", NS)
    cost = first_relop.attrib.get("EstimatedTotalSubtreeCost", "?") if first_relop is not None else "?"
    mode = "?"
    if first_relop is not None:
        mode = (
            first_relop.attrib.get("ActualExecutionMode")
            or first_relop.attrib.get("EstimatedExecutionMode")
            or "?"
        )
    return {"cost": f"{float(cost):.3f}" if cost != "?" else "?", "mode": mode}


def draw_node(
    ax: plt.Axes,
    cx: float,
    cy: float,
    w: float,
    h: float,
    title: str,
    subtitle: str,
    facecolor: str,
    edgecolor: str = "#1E293B",
    fontsize: float = 7.6,
) -> None:
    """Desenha um bloco de operador fisico arredondado."""
    box = FancyBboxPatch(
        (cx - w / 2, cy - h / 2),
        w,
        h,
        boxstyle="round,pad=0.015,rounding_size=0.025",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=1.1,
    )
    ax.add_patch(box)
    ax.text(cx, cy + h * 0.16, title, ha="center", va="center", fontsize=fontsize, fontweight="bold", color="#0F172A")
    ax.text(cx, cy - h * 0.22, subtitle, ha="center", va="center", fontsize=fontsize - 0.8, color="#334155")


def draw_arrow(ax: plt.Axes, x0: float, y0: float, x1: float, y1: float) -> None:
    """Desenha seta de fluxo de dados entre operadores (filho -> pai)."""
    ax.annotate(
        "",
        xy=(x1, y1),
        xytext=(x0, y0),
        arrowprops={"arrowstyle": "-|>", "color": "#475569", "lw": 1.15, "shrinkA": 2, "shrinkB": 2},
    )


def generate_plan_figure() -> list[Path]:
    """Gera figura comparativa 2x2 dos planos reais extraidos dos XMLs."""
    summary = json.loads((RESULTS_DIR / "summary_stats.json").read_text(encoding="utf-8"))
    warm = summary["cache_modes"]["warm"]
    q4_inter = summary["q4_three_stage"]

    p_q1_b = parse_plan_summary(RESULTS_DIR / "plans/baseline/q1_baseline.sqlplan")
    p_q1_o = parse_plan_summary(RESULTS_DIR / "plans/optimized/q1_optimized.sqlplan")
    p_q4_b = parse_plan_summary(RESULTS_DIR / "plans/baseline/q4_baseline.sqlplan")
    p_q4_i = parse_plan_summary(RESULTS_DIR / "plans/optimized/q4_intermediate_lookup.sqlplan")
    p_q4_o = parse_plan_summary(RESULTS_DIR / "plans/optimized/q4_optimized.sqlplan")
    p_q7_b = parse_plan_summary(RESULTS_DIR / "plans/baseline/q7_baseline.sqlplan")
    p_q7_o = parse_plan_summary(RESULTS_DIR / "plans/optimized/q7_optimized.sqlplan")
    p_w1_o = parse_plan_summary(RESULTS_DIR / "plans/optimized/w1_optimized.sqlplan")

    fig, axes = plt.subplots(2, 2, figsize=(12.2, 7.4))
    for ax in axes.flat:
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(0, 1)
        ax.axis("off")

    # Painel (a): Q1 Scan vs Seek + Key Lookup
    ax = axes[0, 0]
    ax.set_title("(a) Q1: Scan Completo vs. Seek + Key Lookup", fontsize=10, fontweight="bold", pad=6)
    ax.text(0.22, 0.93, f"Baseline (Custo Est. {p_q1_b['cost']})", ha="center", fontsize=8.2, fontweight="bold", color="#1E3A8A")
    draw_node(ax, 0.22, 0.50, 0.38, 0.22, "Clustered Index Scan", "PK_Clientes | 2.856 pág. | 15,0 ms", "#DBEAFE", "#1D4ED8")

    ax.text(0.75, 0.93, f"Otimizado (Custo Est. {p_q1_o['cost']})", ha="center", fontsize=8.2, fontweight="bold", color="#166534")
    draw_node(ax, 0.75, 0.72, 0.42, 0.17, "Nested Loops (Inner Join)", "6 páginas lógicas | < 1 ms", "#DCFCE7", "#15803D")
    draw_node(ax, 0.62, 0.28, 0.20, 0.19, "Index Seek", "IX_Clientes_Email\n(1 linha)", "#DCFCE7", "#15803D", fontsize=7.0)
    draw_node(ax, 0.88, 0.28, 0.20, 0.19, "Key Lookup", "PK_Clientes\n(1 lookup)", "#FEF3C7", "#B45309", fontsize=7.0)
    draw_arrow(ax, 0.62, 0.40, 0.71, 0.61)
    draw_arrow(ax, 0.88, 0.40, 0.79, 0.61)
    ax.axvline(0.47, ymin=0.06, ymax=0.95, color="#CBD5E1", linestyle="--", lw=1)

    # Painel (b): Q4 Eliminacao de Key Lookup (3 estagios)
    ax = axes[0, 1]
    ax.set_title("(b) Q4: Eliminação do Key Lookup com INCLUDE", fontsize=10, fontweight="bold", pad=6)
    ax.text(0.24, 0.93, f"2. Intermediário (Custo {p_q4_i['cost']})", ha="center", fontsize=8.0, fontweight="bold", color="#B45309")
    draw_node(
        ax,
        0.24,
        0.72,
        0.42,
        0.17,
        "Nested Loops (Inner Join)",
        f"{int(q4_inter['metrics']['logical_reads']):,} pág. (scan base: 8.090)".replace(",", "."),
        "#FEF3C7",
        "#B45309",
    )
    draw_node(ax, 0.12, 0.28, 0.20, 0.19, "Index Seek", "IX_ClienteID\n(422 linhas)", "#DCFCE7", "#15803D", fontsize=7.0)
    draw_node(ax, 0.36, 0.28, 0.20, 0.19, "Key Lookup", "PK_Pedidos\n(422 lookups)", "#FEE2E2", "#B91C1C", fontsize=7.0)
    draw_arrow(ax, 0.12, 0.40, 0.20, 0.61)
    draw_arrow(ax, 0.36, 0.40, 0.28, 0.61)

    ax.text(0.76, 0.93, f"3. Covering (Custo {p_q4_o['cost']})", ha="center", fontsize=8.0, fontweight="bold", color="#166534")
    draw_node(
        ax,
        0.76,
        0.50,
        0.42,
        0.24,
        "Index Seek (Covering)",
        f"IX_Pedidos_ClienteID_Cov\nINCLUDE (DataPedido, ValorTotal)\n{int(warm['Q4']['optimized']['logical_reads']['median'])} pág. | < 1 ms",
        "#DCFCE7",
        "#15803D",
    )
    ax.axvline(0.50, ymin=0.06, ymax=0.95, color="#CBD5E1", linestyle="--", lw=1)

    # Painel (c): Q7 Batch Mode vs Row Mode
    ax = axes[1, 0]
    ax.set_title("(c) Q7: Trade-off Batch Mode vs. Row Mode (MAXDOP 1)", fontsize=10, fontweight="bold", pad=6)
    ax.text(0.22, 0.93, f"Baseline (Custo Est. {p_q7_b['cost']})", ha="center", fontsize=8.0, fontweight="bold", color="#1E3A8A")
    draw_node(ax, 0.22, 0.72, 0.40, 0.18, "Hash Match [Aggregate]", f"Modo: {p_q7_b['mode']} | 217,0 ms med.", "#DBEAFE", "#1D4ED8")
    draw_node(ax, 0.22, 0.28, 0.40, 0.18, "Clustered Index Scan", "PK_Pedidos | 8.090 páginas", "#DBEAFE", "#1D4ED8")
    draw_arrow(ax, 0.22, 0.39, 0.22, 0.61)

    ax.text(0.75, 0.93, f"Otimizado (Custo Est. {p_q7_o['cost']})", ha="center", fontsize=8.0, fontweight="bold", color="#B91C1C")
    draw_node(ax, 0.75, 0.72, 0.40, 0.18, "Stream Aggregate", f"Modo: {p_q7_o['mode']} | 364,0 ms med.", "#FEE2E2", "#B91C1C")
    draw_node(ax, 0.75, 0.28, 0.40, 0.18, "Index Scan (Ordered)", "IX_Pedidos_Status_Cov | 5.658 pág.", "#DCFCE7", "#15803D")
    draw_arrow(ax, 0.75, 0.39, 0.75, 0.61)
    ax.axvline(0.47, ymin=0.06, ymax=0.95, color="#CBD5E1", linestyle="--", lw=1)

    # Painel (d): W1 Amplificacao de escrita em B+ Trees
    ax = axes[1, 1]
    ax.set_title("(d) W1: Amplificação de Escrita na Carga Otimizada", fontsize=10, fontweight="bold", pad=6)
    ax.text(
        0.50,
        0.93,
        f"Sequence Multi-Índice (Custo {p_w1_o['cost']} | {int(warm['W1']['optimized']['logical_reads']['median']):,} pág. vs 97.154 base)".replace(",", "."),
        ha="center",
        fontsize=8.0,
        fontweight="bold",
        color="#B91C1C",
    )
    draw_node(ax, 0.50, 0.74, 0.52, 0.15, "Sequence (Escrita 10.000 linhas)", "Manutenção síncrona em 4 B+ Trees", "#FEE2E2", "#B91C1C")
    draw_node(ax, 0.11, 0.28, 0.18, 0.22, "Clustered\nInsert", "PK_ItensPedido\n10.000 linhas", "#DBEAFE", "#1D4ED8", fontsize=6.9)
    draw_node(ax, 0.37, 0.28, 0.18, 0.22, "Index\nInsert", "IX_PedidoID\n10.000 linhas", "#FEE2E2", "#B91C1C", fontsize=6.9)
    draw_node(ax, 0.63, 0.28, 0.18, 0.22, "Index\nInsert", "IX_ProdutoID\n10.000 linhas", "#FEE2E2", "#B91C1C", fontsize=6.9)
    draw_node(ax, 0.89, 0.28, 0.18, 0.22, "Filter +\nInsert", "Desconto>=10\n1.964 linhas", "#FEF3C7", "#B45309", fontsize=6.9)
    for cx in (0.11, 0.37, 0.63, 0.89):
        draw_arrow(ax, cx, 0.41, 0.50, 0.65)

    plt.tight_layout(pad=1.2)
    outputs: list[Path] = []
    for folder in (PAPER_DIR / "figures", RESULTS_DIR / "charts"):
        folder.mkdir(parents=True, exist_ok=True)
        out = folder / "fig5_planos_execucao.png"
        fig.savefig(out, dpi=300, bbox_inches="tight")
        outputs.append(out)
    plt.close(fig)
    return outputs


def main() -> int:
    for out in generate_plan_figure():
        print(f"Gerado: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
