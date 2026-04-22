#!/usr/bin/env python3
from pathlib import Path
import markdown
from weasyprint import HTML

repo_root = Path(__file__).resolve().parent.parent
base = repo_root
md_path = repo_root / 'docs' / 'chess-search-guide.md'
pdf_path = repo_root / 'generated' / 'chess-search-guide.pdf'
pdf_path.parent.mkdir(parents=True, exist_ok=True)
text = md_path.read_text(encoding='utf-8')
html_body = markdown.markdown(text, extensions=['fenced_code', 'tables'])
html = f'''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {{ size: A4; margin: 18mm 16mm 18mm 16mm; }}
  body {{ font-family: Inter, Arial, sans-serif; color: #1b1f23; font-size: 11pt; line-height: 1.45; }}
  h1 {{ font-size: 24pt; margin: 0 0 12px 0; color: #0f172a; }}
  h2 {{ font-size: 16pt; margin-top: 22px; color: #111827; border-bottom: 1px solid #d1d5db; padding-bottom: 4px; }}
  h3 {{ font-size: 13pt; margin-top: 16px; color: #1f2937; }}
  p, li {{ orphans: 3; widows: 3; }}
  code {{ font-family: 'DejaVu Sans Mono', monospace; background: #f3f4f6; padding: 1px 4px; border-radius: 3px; font-size: 9.8pt; }}
  pre {{ background: #0f172a; color: #e5e7eb; padding: 10px 12px; border-radius: 6px; overflow-wrap: anywhere; white-space: pre-wrap; font-size: 9pt; }}
  pre code {{ background: transparent; color: inherit; padding: 0; }}
  a {{ color: #1d4ed8; text-decoration: none; }}
  blockquote {{ border-left: 4px solid #94a3b8; padding-left: 10px; color: #334155; margin-left: 0; }}
  ul, ol {{ padding-left: 22px; }}
  .meta {{ color: #475569; font-size: 10pt; margin-bottom: 14px; }}
</style>
</head>
<body>
<div class="meta">Generated from <code>docs/chess-search-guide.md</code></div>
{html_body}
</body>
</html>'''
HTML(string=html, base_url=str(base)).write_pdf(str(pdf_path))
print(pdf_path)
