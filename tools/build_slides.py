"""Build the demo-day slides as one self-contained HTML file.

    python tools/build_slides.py "Your Name"

Reads `tools/slides/template.html` and inlines reveal.js (`tools/slides/vendor/`),
the Archivo font (`docs/fonts/`), the demo recording (`tools/slides/demo.mp4`, made by
`tools/slides/record_demo.mjs`, with its step times in `demo-steps.json`) and its poster into
`docs/slides/index.html`, which GitHub Pages serves at
https://esst-prog2.github.io/Route-tariff-and-Capacity-fee-Calculator/slides/
"""

import base64
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "slides"
OUT = ROOT / "docs" / "slides" / "index.html"


def data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def build(name: str) -> str:
    html = (SRC / "template.html").read_text(encoding="utf-8")

    def code(match: re.Match) -> str:
        text = (SRC / "vendor" / match.group(1)).read_text(encoding="utf-8")
        if match.group(1).endswith(".js"):
            # "</script" inside a JS string would close the inline tag; "<\/script" is the same string.
            text = re.sub(r"</(script)", r"<\\/\1", text, flags=re.IGNORECASE)
        closing = "</script" if match.group(1).endswith(".js") else "</style"
        if closing in text.lower():
            raise ValueError(f"{match.group(1)} would end its inline tag early")
        return text

    html = re.sub(r"/\*\{\{([\w.-]+\.(?:js|css))\}\}\*/", code, html)
    html = re.sub(r"\{\{font:([\w.-]+)\}\}", lambda m: data_uri(ROOT / "docs" / "fonts" / m.group(1), "font/woff2"), html)
    html = re.sub(r"\{\{img:([\w.-]+)\}\}", lambda m: data_uri(SRC / m.group(1), "image/webp"), html)
    html = re.sub(r"\{\{video:([\w.-]+)\}\}", lambda m: data_uri(SRC / m.group(1), "video/mp4"), html)
    html = re.sub(r"\{\{json:([\w.-]+)\}\}", lambda m: json.dumps(json.loads((SRC / m.group(1)).read_text(encoding="utf-8"))), html)
    html = html.replace("{{NAME}}", name)
    if "{{" in html and re.search(r"\{\{[\w:.-]+\}\}", html):
        raise ValueError("unfilled placeholder: " + re.search(r"\{\{[\w:.-]+\}\}", html).group(0))
    return html


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(sys.argv[1]), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {OUT.stat().st_size:,} bytes")
