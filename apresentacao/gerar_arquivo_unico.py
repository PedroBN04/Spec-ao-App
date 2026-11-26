"""Gera da_spec_ao_app.html: a apresentação inteira num único arquivo.

Imagens, ícones, fontes e o gerador de QR Code vão embutidos (base64), então o arquivo funciona
sozinho: aberto de dentro do .zip, enviado por e-mail/WhatsApp ou copiado sem a pasta assets/.

Uso (a partir da raiz do repositório ou desta pasta):  python apresentacao/gerar_arquivo_unico.py
"""

import base64
import re
from pathlib import Path

PASTA = Path(__file__).resolve().parent
TIPOS = {".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml",
         ".woff2": "font/woff2", ".ttf": "font/ttf"}


def data_uri(caminho: Path) -> str:
    dados = base64.b64encode(caminho.read_bytes()).decode("ascii")
    return f"data:{TIPOS[caminho.suffix]};base64,{dados}"


def main() -> None:
    html = (PASTA / "index.html").read_text(encoding="utf-8")

    # 1. Folha de estilos dos ícones (Codicons), com a fonte embutida
    css = (PASTA / "assets/icons/codicon.css").read_text(encoding="utf-8")
    css = css.replace('url("../fonts/codicon.ttf")', f'url("{data_uri(PASTA / "assets/fonts/codicon.ttf")}")')
    html = html.replace('<link rel="stylesheet" href="assets/icons/codicon.css">', f"<style>\n{css}\n</style>")

    # 2. Fontes Inter e JetBrains Mono
    html = re.sub(r"url\((assets/fonts/[^)]+)\)", lambda m: f"url({data_uri(PASTA / m.group(1))})", html)

    # 3. Imagens e logos
    html = re.sub(r'src="(assets/(?:img|icons)/[^"]+)"', lambda m: f'src="{data_uri(PASTA / m.group(1))}"', html)

    # 4. Gerador de QR Code
    js = (PASTA / "assets/js/qrcode.js").read_text(encoding="utf-8")
    html = html.replace('<script src="assets/js/qrcode.js"></script>', f"<script>\n{js}\n</script>")

    restantes = re.findall(r'(?:src|href)="assets/|url\(assets/', html)
    if restantes:
        raise SystemExit(f"Ainda há {len(restantes)} referência(s) a assets/ no arquivo gerado.")

    destino = PASTA / "da_spec_ao_app.html"
    destino.write_text(html, encoding="utf-8")
    print(f"Gerado {destino.name} ({destino.stat().st_size / 1_048_576:.1f} MB), sem dependências externas.")


if __name__ == "__main__":
    main()
