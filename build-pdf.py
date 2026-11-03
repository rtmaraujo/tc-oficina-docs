"""
Gera o PDF do relatorio da Fase 4 a partir do Markdown.

Uso:
    py docs/build-pdf.py

Requisitos: `markdown` (pip install markdown) e Microsoft Edge instalado.
O script escreve docs/_relatorio.html e docs/RELATORIO-FASE4.pdf.
"""

from pathlib import Path
import os
import subprocess
import sys

import markdown

DOCS = Path(__file__).resolve().parent
ORIGEM = DOCS / "RELATORIO.md"
HTML = DOCS / "_relatorio.html"
PDF = DOCS / "RELATORIO.pdf"

EDGE_CANDIDATOS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
* { box-sizing: border-box; }
body {
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  font-size: 10.5pt;
  line-height: 1.55;
  color: #1f2933;
  margin: 0;
}
h1 {
  font-size: 24pt;
  color: #0b3d62;
  border-bottom: 3px solid #0b3d62;
  padding-bottom: 10px;
  margin: 0 0 6px 0;
  page-break-before: avoid;
}
h2 {
  font-size: 15pt;
  color: #0b3d62;
  margin-top: 26px;
  margin-bottom: 8px;
  border-left: 5px solid #1d7ea8;
  padding-left: 10px;
  page-break-after: avoid;
}
h3 {
  font-size: 12pt;
  color: #16506e;
  margin-top: 18px;
  margin-bottom: 6px;
  page-break-after: avoid;
}
p { margin: 7px 0; text-align: justify; }
ul, ol { margin: 7px 0 7px 20px; padding: 0; }
li { margin: 3px 0; }
table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0 16px 0;
  font-size: 9pt;
  page-break-inside: avoid;
}
th {
  background: #0b3d62;
  color: #ffffff;
  text-align: left;
  padding: 7px 8px;
  font-weight: 600;
}
td {
  border: 1px solid #d5dde5;
  padding: 6px 8px;
  vertical-align: top;
}
tr:nth-child(even) td { background: #f4f8fb; }
code {
  font-family: "Consolas", "Courier New", monospace;
  font-size: 8.8pt;
  background: #eef2f6;
  padding: 1px 4px;
  border-radius: 3px;
  color: #b83232;
}
pre {
  background: #f4f7fa;
  border: 1px solid #d5dde5;
  border-left: 4px solid #1d7ea8;
  border-radius: 4px;
  padding: 10px 12px;
  overflow-x: auto;
  page-break-inside: avoid;
}
pre code {
  background: transparent;
  color: #1f2933;
  font-size: 8.5pt;
  padding: 0;
}
blockquote {
  margin: 10px 0;
  padding: 8px 14px;
  background: #fff8e5;
  border-left: 4px solid #e0a800;
  color: #5a4a1a;
}
a { color: #10608a; text-decoration: none; }
img { max-width: 100%; height: auto; }
p img {
  display: block;
  margin: 14px auto 8px auto;
  max-height: 228mm;
  border: 1px solid #d5dde5;
  border-radius: 4px;
}
hr { border: none; border-top: 1px solid #d5dde5; margin: 22px 0; }
.capa {
  text-align: center;
  padding: 40px 0 30px 0;
  border-bottom: 1px solid #d5dde5;
  margin-bottom: 24px;
}
.capa .tag {
  display: inline-block;
  background: #0b3d62;
  color: #fff;
  font-size: 9pt;
  letter-spacing: 2px;
  text-transform: uppercase;
  padding: 5px 14px;
  border-radius: 3px;
  margin-bottom: 18px;
}
.capa .sub { color: #52606d; font-size: 11pt; margin-top: 4px; }
.capa .meta { color: #7b8794; font-size: 9.5pt; margin-top: 14px; }
h2, table, pre { page-break-inside: avoid; }
"""

CAPA = """
<div class="capa">
  <div class="tag">Tech Challenge &middot; Fase 4</div>
  <div style="font-size:13pt;color:#52606d;">Oficina Mec&acirc;nica &mdash; Microsservi&ccedil;os</div>
  <div style="font-size:10.5pt;color:#7b8794;margin-top:6px;">
    Saga orquestrada &middot; Kafka &middot; Kubernetes &middot; Observabilidade
  </div>
  <div class="meta">Marcos da Paz Araujo &mdash; 03/11/2026</div>
</div>
"""


def encontrar_edge() -> str:
    for caminho in EDGE_CANDIDATOS:
        if os.path.exists(caminho):
            return caminho
    raise SystemExit("Microsoft Edge nao encontrado.")


def main() -> int:
    texto = ORIGEM.read_text(encoding="utf-8")

    # O titulo H1 do markdown vira a capa, entao removemos a primeira linha H1.
    linhas = texto.splitlines()
    if linhas and linhas[0].startswith("# "):
        linhas = linhas[1:]
    corpo_md = "\n".join(linhas).lstrip()

    corpo = markdown.markdown(
        corpo_md,
        extensions=["extra", "tables", "fenced_code", "sane_lists", "toc"],
        output_format="html5",
    )

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Relatorio Tech Challenge Fase 4</title>
<style>{CSS}</style>
</head>
<body>
{CAPA}
{corpo}
</body>
</html>
"""
    HTML.write_text(html, encoding="utf-8")

    edge = encontrar_edge()
    perfil = DOCS / "_edge-profile"
    cmd = [
        edge,
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        f"--user-data-dir={perfil}",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF}",
        HTML.as_uri(),
    ]
    resultado = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if not PDF.exists():
        sys.stderr.write(resultado.stdout + "\n" + resultado.stderr + "\n")
        return 1

    print(f"PDF gerado: {PDF} ({PDF.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
