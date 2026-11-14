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


def format_int_br(value: float | int) -> str:
    """Formata inteiro com separador de milhar brasileiro."""
    return f"{int(round(value)):,}".replace(",", ".")


def format_ms_br(value: float) -> str:
    """Formata tempo mediano respeitando resolucao minima de 1 ms do SQL Server."""
    if value <= 0.0:
        return "< 1 ms"
    return f"{value:.1f} ms".replace(".", ",")


def _find_own_index(node: ET.Element) -> str:
    """Retorna o nome do indice associado diretamente a um RelOp (sem cruzar filhos RelOp)."""
    relop_tag = f"{{{NS['sp']}}}RelOp"
    obj_tag = f"{{{NS['sp']}}}Object"
    for child in node:
        if child.tag == relop_tag:
            continue
        if child.tag == obj_tag:
            return child.attrib.get("Index", "").strip("[]")
        nested = _find_own_index(child)
        if nested:
            return nested
    return ""


_ROW_COUNT_OPS = {
    "Index Seek",
    "Clustered Index Seek",
    "Index Scan",
    "Clustered Index Scan",
    "Clustered Index Insert",
    "Index Insert",
}


def parse_plan_summary(xml_path: Path, target_physical_op: str | None = None) -> dict[str, object]:
    """Extrai custo total, modo de execucao real e linhas por indice de um .sqlplan."""
    root = ET.parse(xml_path).getroot()
    first_relop = root.find(".//sp:RelOp", NS)
    cost = first_relop.attrib.get("EstimatedTotalSubtreeCost", "?") if first_relop is not None else "?"

    mode = "?"
    rows_by_index: dict[str, int] = {}
    for relop in root.findall(".//sp:RelOp", NS):
        phys = relop.attrib.get("PhysicalOp", "")
        rts = relop.findall("./sp:RunTimeInformation/sp:RunTimeCountersPerThread", NS)
        idx_name = _find_own_index(relop)
        act_rows = sum(int(rt.attrib.get("ActualRows", 0)) for rt in rts) if rts else None
        if idx_name and act_rows is not None and phys in _ROW_COUNT_OPS:
            rows_by_index.setdefault(idx_name, act_rows)

        if target_physical_op and phys == target_physical_op and mode == "?":
            if rts and rts[0].attrib.get("ActualExecutionMode"):
                mode = rts[0].attrib["ActualExecutionMode"]
            elif relop.attrib.get("EstimatedExecutionMode"):
                mode = relop.attrib["EstimatedExecutionMode"]

    if mode == "?" and first_relop is not None:
        rts = first_relop.findall("./sp:RunTimeInformation/sp:RunTimeCountersPerThread", NS)
        if rts and rts[0].attrib.get("ActualExecutionMode"):
            mode = rts[0].attrib["ActualExecutionMode"]
        else:
            mode = first_relop.attrib.get("EstimatedExecutionMode", "?")

    return {
        "cost": f"{float(cost):.3f}" if cost != "?" else "?",
        "mode": mode,
        "rows_by_index": rows_by_index,
    }


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
    p_q4_i = parse_plan_summary(RESULTS_DIR / "plans/optimized/q4_intermediate_lookup.sqlplan")
    p_q4_o = parse_plan_summary(RESULTS_DIR / "plans/optimized/q4_optimized.sqlplan")
    p_q7_b = parse_plan_summary(
        RESULTS_DIR / "plans/baseline/q7_baseline.sqlplan", target_physical_op="Hash Match"
    )
    p_q7_o = parse_plan_summary(
        RESULTS_DIR / "plans/optimized/q7_optimized.sqlplan", target_physical_op="Stream Aggregate"
    )
    p_w1_o = parse_plan_summary(RESULTS_DIR / "plans/optimized/w1_optimized.sqlplan")

    q1_b_reads = format_int_br(warm["Q1"]["baseline"]["logical_reads"]["median"])
    q1_b_ms = format_ms_br(float(warm["Q1"]["baseline"]["elapsed_time_ms"]["median"]))
    q1_o_reads = format_int_br(warm["Q1"]["optimized"]["logical_reads"]["median"])
    q1_o_ms = format_ms_br(float(warm["Q1"]["optimized"]["elapsed_time_ms"]["median"]))
    q1_o_rows = p_q1_o["rows_by_index"].get("IX_Clientes_Email", warm["Q1"]["row_count"])
    q1_o_lookups = p_q1_o["rows_by_index"].get("PK_Clientes", q1_o_rows)

    q4_b_reads = format_int_br(warm["Q4"]["baseline"]["logical_reads"]["median"])
    q4_i_reads = format_int_br(q4_inter["metrics"]["logical_reads"])
    q4_i_rows = p_q4_i["rows_by_index"].get("IX_Pedidos_ClienteID", q4_inter["metrics"]["row_count"])
    q4_i_lookups = p_q4_i["rows_by_index"].get("PK_Pedidos", q4_i_rows)
    q4_o_reads = format_int_br(warm["Q4"]["optimized"]["logical_reads"]["median"])
    q4_o_ms = format_ms_br(float(warm["Q4"]["optimized"]["elapsed_time_ms"]["median"]))

    q7_b_reads = format_int_br(warm["Q7"]["baseline"]["logical_reads"]["median"])
    q7_b_ms = format_ms_br(float(warm["Q7"]["baseline"]["elapsed_time_ms"]["median"]))
    q7_o_reads = format_int_br(warm["Q7"]["optimized"]["logical_reads"]["median"])
    q7_o_ms = format_ms_br(float(warm["Q7"]["optimized"]["elapsed_time_ms"]["median"]))

    w1_b_reads = format_int_br(warm["W1"]["baseline"]["logical_reads"]["median"])
    w1_o_reads = format_int_br(warm["W1"]["optimized"]["logical_reads"]["median"])
    w1_rows_by_idx = p_w1_o["rows_by_index"]
    w1_total_rows = warm["W1"]["row_count"]
    w1_pk_rows = format_int_br(w1_rows_by_idx.get("PK_ItensPedido", w1_total_rows))
    w1_ped_rows = format_int_br(w1_rows_by_idx.get("IX_ItensPedido_PedidoID", w1_total_rows))
    w1_prod_rows = format_int_br(w1_rows_by_idx.get("IX_ItensPedido_ProdutoID", w1_total_rows))
    w1_filt_rows = format_int_br(w1_rows_by_idx.get("IX_ItensPedido_Desconto_Alto", 0))

    fig, axes = plt.subplots(2, 2, figsize=(12.2, 7.4))
    for ax in axes.flat:
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(0, 1)
        ax.axis("off")

    # Painel (a): Q1 Scan vs Seek + Key Lookup
    ax = axes[0, 0]
    ax.set_title("(a) Q1: Scan Completo vs. Seek + Key Lookup", fontsize=10, fontweight="bold", pad=6)
    ax.text(0.22, 0.93, f"Baseline (Custo Est. {p_q1_b['cost']})", ha="center", fontsize=8.2, fontweight="bold", color="#1E3A8A")
    draw_node(ax, 0.22, 0.50, 0.38, 0.22, "Clustered Index Scan", f"PK_Clientes | {q1_b_reads} pág. | {q1_b_ms}", "#DBEAFE", "#1D4ED8")

    ax.text(0.75, 0.93, f"Otimizado (Custo Est. {p_q1_o['cost']})", ha="center", fontsize=8.2, fontweight="bold", color="#166534")
    draw_node(ax, 0.75, 0.72, 0.42, 0.17, "Nested Loops (Inner Join)", f"{q1_o_reads} páginas lógicas | {q1_o_ms}", "#DCFCE7", "#15803D")
    row_lbl = "linha" if q1_o_rows == 1 else "linhas"
    lkp_lbl = "lookup" if q1_o_lookups == 1 else "lookups"
    draw_node(ax, 0.62, 0.28, 0.20, 0.19, "Index Seek", f"IX_Clientes_Email\n({format_int_br(q1_o_rows)} {row_lbl})", "#DCFCE7", "#15803D", fontsize=7.0)
    draw_node(ax, 0.88, 0.28, 0.20, 0.19, "Key Lookup", f"PK_Clientes\n({format_int_br(q1_o_lookups)} {lkp_lbl})", "#FEF3C7", "#B45309", fontsize=7.0)
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
        f"{q4_i_reads} pág. (scan base: {q4_b_reads})",
        "#FEF3C7",
        "#B45309",
    )
    draw_node(ax, 0.12, 0.28, 0.20, 0.19, "Index Seek", f"IX_ClienteID\n({format_int_br(q4_i_rows)} linhas)", "#DCFCE7", "#15803D", fontsize=7.0)
    draw_node(ax, 0.36, 0.28, 0.20, 0.19, "Key Lookup", f"PK_Pedidos\n({format_int_br(q4_i_lookups)} lookups)", "#FEE2E2", "#B91C1C", fontsize=7.0)
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
        f"IX_Pedidos_ClienteID_Cov\nINCLUDE (DataPedido, ValorTotal)\n{q4_o_reads} pág. | {q4_o_ms}",
        "#DCFCE7",
        "#15803D",
    )
    ax.axvline(0.50, ymin=0.06, ymax=0.95, color="#CBD5E1", linestyle="--", lw=1)

    # Painel (c): Q7 Batch Mode vs Row Mode
    ax = axes[1, 0]
    ax.set_title("(c) Q7: Trade-off Batch Mode vs. Row Mode (MAXDOP 1)", fontsize=10, fontweight="bold", pad=6)
    ax.text(0.22, 0.93, f"Baseline (Custo Est. {p_q7_b['cost']})", ha="center", fontsize=8.0, fontweight="bold", color="#1E3A8A")
    draw_node(ax, 0.22, 0.72, 0.40, 0.18, "Hash Match [Aggregate]", f"Modo: {p_q7_b['mode']} | {q7_b_ms} med.", "#DBEAFE", "#1D4ED8")
    draw_node(ax, 0.22, 0.28, 0.40, 0.18, "Clustered Index Scan", f"PK_Pedidos | {q7_b_reads} páginas", "#DBEAFE", "#1D4ED8")
    draw_arrow(ax, 0.22, 0.39, 0.22, 0.61)

    ax.text(0.75, 0.93, f"Otimizado (Custo Est. {p_q7_o['cost']})", ha="center", fontsize=8.0, fontweight="bold", color="#B91C1C")
    draw_node(ax, 0.75, 0.72, 0.40, 0.18, "Stream Aggregate", f"Modo: {p_q7_o['mode']} | {q7_o_ms} med.", "#FEE2E2", "#B91C1C")
    draw_node(ax, 0.75, 0.28, 0.40, 0.18, "Index Scan (Ordered)", f"IX_Pedidos_Status_Cov | {q7_o_reads} pág.", "#DCFCE7", "#15803D")
    draw_arrow(ax, 0.75, 0.39, 0.75, 0.61)
    ax.axvline(0.47, ymin=0.06, ymax=0.95, color="#CBD5E1", linestyle="--", lw=1)

    # Painel (d): W1 Amplificacao de escrita em B+ Trees
    ax = axes[1, 1]
    ax.set_title("(d) W1: Amplificação de Escrita na Carga Otimizada", fontsize=10, fontweight="bold", pad=6)
    ax.text(
        0.50,
        0.93,
        f"Sequence Multi-Índice (Custo {p_w1_o['cost']} | {w1_o_reads} pág. vs {w1_b_reads} base)",
        ha="center",
        fontsize=8.0,
        fontweight="bold",
        color="#B91C1C",
    )
    draw_node(ax, 0.50, 0.74, 0.52, 0.15, f"Sequence (Escrita {format_int_br(w1_total_rows)} linhas)", "Manutenção síncrona em 4 B+ Trees", "#FEE2E2", "#B91C1C")
    draw_node(ax, 0.11, 0.28, 0.18, 0.22, "Clustered\nInsert", f"PK_ItensPedido\n{w1_pk_rows} linhas", "#DBEAFE", "#1D4ED8", fontsize=6.9)
    draw_node(ax, 0.37, 0.28, 0.18, 0.22, "Index\nInsert", f"IX_PedidoID\n{w1_ped_rows} linhas", "#FEE2E2", "#B91C1C", fontsize=6.9)
    draw_node(ax, 0.63, 0.28, 0.18, 0.22, "Index\nInsert", f"IX_ProdutoID\n{w1_prod_rows} linhas", "#FEE2E2", "#B91C1C", fontsize=6.9)
    draw_node(ax, 0.89, 0.28, 0.18, 0.22, "Filter +\nInsert", f"Desconto>=10\n{w1_filt_rows} linhas", "#FEF3C7", "#B45309", fontsize=6.9)
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
