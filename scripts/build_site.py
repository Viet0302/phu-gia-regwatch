#!/usr/bin/env python3
"""Dựng trang web tĩnh: bảng theo dõi văn bản + nhật ký thay đổi + trang tra cứu phụ gia."""
from __future__ import annotations

import datetime as dt
import html
import json
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site_out"
SITE = ROOT / "site"
DATA = ROOT / "data"

MK_ORDER = ["Codex", "Việt Nam", "Mỹ", "Úc/NZ", "Thái Lan", "EU", "Hồng Kông", "Mông Cổ", "Đài Loan"]
STATUS = {
    "ok": ("Đang theo dõi", "ok"),
    "error": ("Không truy cập được", "err"),
    "manual": ("Kiểm tra thủ công", "man"),
    "blocked": ("Trang chặn tự động", "man"),
}


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def days_since(d: str) -> int | None:
    if not d:
        return None
    try:
        return (dt.date.today() - dt.date.fromisoformat(d)).days
    except ValueError:
        return None


def build() -> None:
    watch = yaml.safe_load((ROOT / "watchlist.yml").read_text(encoding="utf-8"))["sources"]
    state = json.loads((DATA / "state.json").read_text(encoding="utf-8")) if (DATA / "state.json").exists() else {}
    log = json.loads((DATA / "changelog.json").read_text(encoding="utf-8")) if (DATA / "changelog.json").exists() else []

    OUT.mkdir(exist_ok=True)
    for name in ("style.css", "pg-detail.json"):
        src = SITE / name
        if src.exists():
            shutil.copy(src, OUT / name)

    # trang tra cứu: bọc thành tài liệu HTML đầy đủ nếu nguồn chỉ là đoạn nội dung
    look = SITE / "tra-cuu.html"
    if look.exists():
        frag = look.read_text(encoding="utf-8")
        if not frag.lstrip().lower().startswith("<!doctype"):
            frag = ('<!doctype html><html lang="vi"><head><meta charset="utf-8">'
                    '<meta name="viewport" content="width=device-width,initial-scale=1">'
                    '<title>Sổ Tra Phụ Gia Xuất Khẩu</title>'
                    '<style>[hidden]{display:none!important}body{margin:0}</style></head><body>'
                    + frag + '</body></html>')
        (OUT / "tra-cuu.html").write_text(frag, encoding="utf-8")
    shutil.copy(DATA / "changelog.json", OUT / "changelog.json") if (DATA / "changelog.json").exists() else None
    shutil.copy(DATA / "state.json", OUT / "status.json") if (DATA / "state.json").exists() else None

    rows = []
    for src in watch:
        st = state.get(src["id"], {})
        rows.append({**src, **st})
    rows.sort(key=lambda r: (MK_ORDER.index(r["market"]) if r["market"] in MK_ORDER else 99, r["name"]))

    n_ok = sum(1 for r in rows if r.get("status") == "ok")
    n_err = sum(1 for r in rows if r.get("status") == "error")
    n_man = sum(1 for r in rows if r.get("status") in ("manual", "blocked"))
    recent = [e for e in log if days_since(e.get("date", "")) is not None and days_since(e["date"]) <= 30]

    # ---------------------------------------------------------------- bảng nguồn
    table = []
    for r in rows:
        label, cls = STATUS.get(r.get("status", ""), ("Chưa kiểm tra", "man"))
        d = days_since(r.get("last_change", ""))
        changed = f'{esc(r.get("last_change"))} ({d} ngày trước)' if d is not None else "—"
        msg = r.get("message") or r.get("note") or ""
        table.append(f"""      <tr>
        <td class="mk">{esc(r['market'])}</td>
        <td><a href="{esc(r['url'])}" target="_blank" rel="noopener">{esc(r['name'])}</a>
            {f'<div class="note">{esc(msg)}</div>' if msg else ''}</td>
        <td><span class="badge {cls}">{esc(label)}</span></td>
        <td class="num">{esc(r.get('last_check') or '—')}</td>
        <td class="num">{changed}</td>
      </tr>""")

    # ---------------------------------------------------------------- nhật ký
    items = []
    for e in log[:120]:
        diff = "".join(
            f'<div class="dl {"add" if ln.startswith("+") else "del"}">{esc(ln)}</div>'
            for ln in e.get("diff", [])[:12]
        )
        items.append(f"""      <li>
        <div class="ld"><time>{esc(e.get('date'))}</time><span class="mk2">{esc(e.get('market'))}</span>
          <span class="kind">{esc(e.get('kind'))}</span></div>
        <div class="ln"><a href="{esc(e.get('url'))}" target="_blank" rel="noopener">{esc(e.get('name'))}</a></div>
        {f'<div class="diffbox">{diff}</div>' if diff else ''}
      </li>""")

    tpl = (SITE / "index.template.html").read_text(encoding="utf-8")
    page = (tpl
            .replace("{{UPDATED}}", dt.datetime.now(dt.timezone.utc).strftime("%d/%m/%Y %H:%M UTC"))
            .replace("{{N_SRC}}", str(len(rows)))
            .replace("{{N_OK}}", str(n_ok))
            .replace("{{N_ERR}}", str(n_err))
            .replace("{{N_MAN}}", str(n_man))
            .replace("{{N_RECENT}}", str(len(recent)))
            .replace("{{ROWS}}", "\n".join(table))
            .replace("{{LOG}}", "\n".join(items) or '<li class="empty">Chưa có thay đổi nào được ghi nhận.</li>'))
    (OUT / "index.html").write_text(page, encoding="utf-8")

    # ---------------------------------------------------------------- RSS
    now = dt.datetime.now(dt.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    entries = []
    for e in log[:50]:
        desc = esc(" · ".join(e.get("diff", [])[:6]) or e.get("kind", ""))
        entries.append(f"""    <item>
      <title>[{esc(e.get('market'))}] {esc(e.get('name'))}</title>
      <link>{esc(e.get('url'))}</link>
      <guid isPermaLink="false">{esc(e.get('id'))}-{esc(e.get('ts') or e.get('date'))}</guid>
      <pubDate>{esc(e.get('date'))}</pubDate>
      <description>{desc}</description>
    </item>""")
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Theo dõi văn bản phụ gia thực phẩm</title>
  <link>./index.html</link>
  <description>Nhật ký thay đổi văn bản pháp luật về phụ gia thực phẩm tại Codex và 8 thị trường</description>
  <lastBuildDate>{now}</lastBuildDate>
{chr(10).join(entries)}
</channel></rss>"""
    (OUT / "feed.xml").write_text(rss, encoding="utf-8")

    print(f"Đã dựng site: {len(rows)} nguồn, {len(log)} mục nhật ký -> {OUT}")


if __name__ == "__main__":
    build()
