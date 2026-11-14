"""Compilador multiplataforma e validador de conformidade do artigo SBC em LaTeX."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
PAPER_DIR = ROOT_DIR / "paper"
RESULTS_DIR = ROOT_DIR / "results"


def _run_step(cmd: list[str], cwd: Path) -> str:
    """Executa um passo de compilacao LaTeX e retorna a saida combinada."""
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = f"{proc.stdout}\n{proc.stderr}"
    if proc.returncode != 0:
        print(output)
        raise RuntimeError(f"Falha ao executar {' '.join(cmd)} (codigo {proc.returncode}).")
    return output


def _read_png_dpi(png_path: Path) -> tuple[float, float] | None:
    """Le o chunk pHYs de um arquivo PNG (stdlib) e retorna (dpi_x, dpi_y)."""
    data = png_path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    pos = 8
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        chunk_data = data[pos + 8 : pos + 8 + length]
        if chunk_type == b"pHYs" and len(chunk_data) == 9:
            ppu_x, ppu_y, unit = struct.unpack(">IIB", chunk_data)
            if unit == 1:
                return (round(ppu_x * 0.0254, 1), round(ppu_y * 0.0254, 1))
        pos += 12 + length
    return None


def validate_latex_conformance(
    tex_path: Path,
    final_output: str,
    max_pages: int = 10,
    strict: bool = True,
) -> dict[str, Any]:
    """Valida paginacao, Overfull hbox, citacoes, BibTeX e figuras de 300 DPI."""
    stem = tex_path.stem
    log_path = tex_path.with_suffix(".log")
    blg_path = tex_path.with_suffix(".blg")
    pdf_path = tex_path.with_suffix(".pdf")

    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else final_output
    blg_text = blg_path.read_text(encoding="utf-8", errors="replace") if blg_path.exists() else ""
    tex_text = tex_path.read_text(encoding="utf-8")

    pages_match = re.search(rf"Output written on {re.escape(stem)}\.pdf \((\d+) pages?", log_text)
    pages = int(pages_match.group(1)) if pages_match else None
    overfull = re.findall(r"Overfull \\hbox .*", log_text)

    undefined_warnings = re.findall(
        r"LaTeX Warning: (?:Citation|Reference) .* undefined.*|"
        r"LaTeX Warning: There were undefined .*|"
        r"LaTeX Warning: There were multiply-defined .*|"
        r"LaTeX Warning: Label\(s\) may have changed.*",
        log_text,
    )
    blg_issues = [
        line.strip()
        for line in blg_text.splitlines()
        if line.startswith("Warning--")
        or "error message" in line.lower()
        or "i couldn't" in line.lower()
        or "repeated entry" in line.lower()
    ]

    figure_paths = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex_text)
    figures_status: list[dict[str, Any]] = []
    missing_or_low_dpi: list[str] = []
    for rel_fig in figure_paths:
        fig_file = tex_path.parent / rel_fig
        exists = fig_file.exists()
        dpi = _read_png_dpi(fig_file) if exists and fig_file.suffix.lower() == ".png" else None
        figures_status.append({"path": rel_fig, "exists": exists, "dpi": dpi})
        if not exists:
            missing_or_low_dpi.append(f"Ausente: {rel_fig}")
        elif fig_file.suffix.lower() == ".png" and (dpi is None or dpi[0] < 299.0 or dpi[1] < 299.0):
            missing_or_low_dpi.append(f"DPI < 300 ({dpi}): {rel_fig}")

    errors: list[str] = []
    if pages is None or pages < 1 or pages > max_pages:
        errors.append(f"Contagem de paginas invalida: {pages} (limite: 1..{max_pages})")
    if overfull:
        errors.append(f"{len(overfull)} ocorrencia(s) de Overfull \\hbox")
    if undefined_warnings:
        errors.append(f"{len(undefined_warnings)} aviso(s) de citacao/referencia indefinida")
    if blg_issues:
        errors.append(f"{len(blg_issues)} aviso(s)/erro(s) no BibTeX (.blg)")
    if missing_or_low_dpi:
        errors.append(f"Problemas em figuras: {'; '.join(missing_or_low_dpi)}")

    report = {
        "pdf_path": str(pdf_path.relative_to(ROOT_DIR)).replace("\\", "/"),
        "pdf_bytes": pdf_path.stat().st_size,
        "pages": pages,
        "max_pages": max_pages,
        "overfull_count": len(overfull),
        "undefined_warnings": undefined_warnings,
        "bibtex_issues": blg_issues,
        "figures": figures_status,
        "passed": len(errors) == 0,
        "errors": errors,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = RESULTS_DIR / "latex_validation.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    print(f"[OK] PDF compilado: {pdf_path} ({report['pdf_bytes']} bytes)")
    print(f"[OK] Total de paginas: {pages} (limite do trabalho: {max_pages})")
    print("[OK] Nenhuma advertencia de Overfull \\hbox." if not overfull else f"[AVISO] {len(overfull)} Overfull \\hbox")
    print("[OK] Citacoes e referencias cruzadas resolvidas." if not undefined_warnings else f"[AVISO] {undefined_warnings}")
    print("[OK] BibTeX sem avisos/erros." if not blg_issues else f"[AVISO] BibTeX: {blg_issues}")
    print(f"[OK] Figuras validadas ({len(figures_status)} em 300 DPI)." if not missing_or_low_dpi else f"[AVISO] {missing_or_low_dpi}")
    print(f"[OK] Relatorio salvo em: {report_path}")

    if strict and errors:
        raise RuntimeError("Falha na validacao de conformidade LaTeX: " + " | ".join(errors))

    return report


def compile_paper(tex_name: str = "main.tex", max_pages: int = 10, strict: bool = True) -> Path:
    """Compila o artigo SBC via pdflatex + bibtex + pdflatex x2 e executa validacao."""
    if not PAPER_DIR.exists():
        raise FileNotFoundError(f"Diretorio nao encontrado: {PAPER_DIR}")

    tex_path = PAPER_DIR / tex_name
    if not tex_path.exists():
        raise FileNotFoundError(f"Arquivo LaTeX nao encontrado: {tex_path}")

    for tool in ("pdflatex", "bibtex"):
        if shutil.which(tool) is None:
            raise EnvironmentError(
                f"Ferramenta '{tool}' nao encontrada no PATH.\n"
                "Windows: instale MiKTeX ou TeX Live.\n"
                "Ubuntu: sudo apt install texlive-latex-base texlive-latex-extra "
                "texlive-fonts-recommended texlive-lang-portuguese"
            )

    stem = tex_path.stem
    pdflatex_cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_name]

    _run_step(pdflatex_cmd, PAPER_DIR)
    _run_step(["bibtex", stem], PAPER_DIR)
    _run_step(pdflatex_cmd, PAPER_DIR)
    final_output = _run_step(pdflatex_cmd, PAPER_DIR)

    pdf_path = PAPER_DIR / f"{stem}.pdf"
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF esperado nao foi gerado: {pdf_path}")

    validate_latex_conformance(tex_path, final_output, max_pages=max_pages, strict=strict)
    return pdf_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Compila e valida o artigo SBC em LaTeX.")
    parser.add_argument("--tex", default="main.tex", help="Arquivo .tex dentro de paper/")
    parser.add_argument("--max-pages", type=int, default=10, help="Limite maximo de paginas.")
    parser.add_argument("--no-strict", action="store_true", help="Nao falhar se houver avisos.")
    args = parser.parse_args()

    compile_paper(tex_name=args.tex, max_pages=args.max_pages, strict=not args.no_strict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
