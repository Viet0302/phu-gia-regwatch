#!/usr/bin/env python3
"""Kiểm tra các nguồn văn bản pháp luật về phụ gia thực phẩm và ghi lại thay đổi.

Chạy mỗi ngày bằng GitHub Actions. Với mỗi nguồn:
  - tôn trọng robots.txt; nguồn bị chặn sẽ được đánh dấu "kiểm tra thủ công"
  - tải nội dung, chuẩn hóa thành văn bản thuần, băm (sha256)
  - so với lần kiểm tra trước; nếu khác thì ghi một mục vào nhật ký kèm trích đoạn thay đổi

Không ghi đè dữ liệu phụ gia; chỉ theo dõi và báo. Người phụ trách đọc nhật ký rồi
cập nhật dữ liệu qua quy trình duyệt của mình.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
import yaml
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STATE_FILE = DATA / "state.json"
LOG_FILE = DATA / "changelog.json"
UA = "PhuGiaRegWatch/1.0 (theo doi van ban phu gia thuc pham; lien he: bo phan QA)"
TIMEOUT = 45
MAX_DIFF_LINES = 30
SNIPPET = 2000          # số ký tự lưu lại để so sánh nhanh khi cần xem lại


# ----------------------------------------------------------------- tiện ích
def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


# ------------------------------------------------------- chuẩn hóa nội dung
VOLATILE = [
    re.compile(r"\b\d{1,2}:\d{2}(:\d{2})?\b"),                       # giờ
    re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}[\d:.]*Z?\b"),       # dấu thời gian ISO
    re.compile(r"(?i)\b(session|csrf|nonce|token|jsessionid)=[\w\-]+"),
    re.compile(r"(?i)\b(last updated|cập nhật lúc|updated at)[^\n]{0,40}"),
]


def normalize_text(text: str) -> str:
    for pat in VOLATILE:
        text = pat.sub(" ", text)
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


def html_to_text(raw: bytes | str) -> str:
    # để BeautifulSoup tự nhận bảng mã từ thẻ meta, tránh đọc sai tiếng Việt
    soup = BeautifulSoup(raw, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()
    main = soup.find("main") or soup.find(id="main") or soup.find("article") or soup.body or soup
    return normalize_text(main.get_text("\n"))


def pdf_to_text(raw: bytes, tmp: Path) -> str:
    tmp.write_bytes(raw)
    out = tmp.with_suffix(".txt")
    rc = os.system(f'pdftotext -layout "{tmp}" "{out}" 2>/dev/null')
    if rc == 0 and out.exists():
        return normalize_text(out.read_text(encoding="utf-8", errors="ignore"))
    return ""


def json_to_text(raw: str, src: dict) -> str:
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return normalize_text(raw)
    if src.get("id") == "us-ecfr-changes":
        rows = obj.get("content_versions", obj if isinstance(obj, list) else [])
        keep = []
        for r in rows:
            part = str(r.get("part", ""))
            if part.isdigit() and 70 <= int(part) <= 189:
                keep.append(f"Part {part} · {r.get('date','')} · {r.get('identifier','')} · {r.get('name','')}")
        keep = sorted(set(keep))[-400:]
        return "\n".join(keep)
    return normalize_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=1))


# ------------------------------------------------------------------ robots
_robots_cache: dict[str, RobotFileParser | None] = {}


def robots_allows(url: str) -> bool:
    parts = urlparse(url)
    base = f"{parts.scheme}://{parts.netloc}"
    if base not in _robots_cache:
        rp = RobotFileParser()
        rp.set_url(base + "/robots.txt")
        try:
            rp.read()
        except Exception:
            rp = None
        _robots_cache[base] = rp
    rp = _robots_cache[base]
    if rp is None:
        return True          # không đọc được robots.txt thì coi như không cấm
    try:
        return rp.can_fetch(UA, url)
    except Exception:
        return True


# ------------------------------------------------------------------ tải nguồn
def fetch(src: dict) -> tuple[str, dict]:
    """Trả về (văn bản đã chuẩn hóa, thông tin phản hồi)."""
    url = src["url"]
    headers = {"User-Agent": UA, "Accept-Language": "vi,en;q=0.8"}
    last_err = ""
    for attempt in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=TIMEOUT)
            info = {"http": r.status_code,
                    "etag": r.headers.get("ETag", ""),
                    "last_modified": r.headers.get("Last-Modified", ""),
                    "bytes": len(r.content)}
            if r.status_code >= 400:
                return "", {**info, "error": f"HTTP {r.status_code}"}
            kind = src.get("kind", "html")
            if kind == "pdf":
                text = pdf_to_text(r.content, ROOT / "data" / f"_tmp_{src['id']}.pdf")
                if not text:
                    text = hashlib.sha256(r.content).hexdigest()   # không đọc được text thì so theo nội dung file
            elif kind == "json":
                text = json_to_text(r.content.decode("utf-8", "replace"), src)
            elif kind == "head":
                text = f"{info['etag']}|{info['last_modified']}|{info['bytes']}"
            else:
                text = html_to_text(r.content)
            return text, info
        except requests.RequestException as e:
            last_err = str(e)[:200]
            time.sleep(2 + attempt * 3)
    return "", {"http": 0, "error": last_err or "không kết nối được"}


def diff_snippet(old: str, new: str) -> list[str]:
    diff = difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=1)
    out = []
    for ln in diff:
        if ln.startswith(("+++", "---", "@@")):
            continue
        if ln.startswith(("+", "-")) and ln[1:].strip():
            out.append(ln[:300])
        if len(out) >= MAX_DIFF_LINES:
            out.append("… (còn nữa, mở văn bản gốc để xem đầy đủ)")
            break
    return out


# ------------------------------------------------------------------- chính
def run(dry: bool = False) -> int:
    watch = yaml.safe_load((ROOT / "watchlist.yml").read_text(encoding="utf-8"))
    sources = watch["sources"]
    state = load_json(STATE_FILE, {})
    log = load_json(LOG_FILE, [])
    changed_entries = []

    for src in sources:
        sid = src["id"]
        prev = state.get(sid, {})
        rec = {"id": sid, "market": src["market"], "name": src["name"], "url": src["url"],
               "kind": src.get("kind", "html"), "note": src.get("note", ""),
               "first_seen": prev.get("first_seen", today()),
               "last_change": prev.get("last_change", ""),
               "last_check": today(), "checks": prev.get("checks", 0) + 1}

        if src.get("manual"):
            rec["status"] = "manual"
            rec["message"] = src.get("note") or "Nguồn chặn công cụ tự động; cần mở kiểm tra thủ công."
            state[sid] = rec
            continue

        if not robots_allows(src["url"]):
            rec["status"] = "blocked"
            rec["message"] = "robots.txt của trang không cho phép truy cập tự động; cần kiểm tra thủ công."
            state[sid] = rec
            continue

        text, info = fetch(src)
        rec.update({k: v for k, v in info.items() if k in ("http", "etag", "last_modified", "bytes")})
        if not text:
            rec["status"] = "error"
            rec["message"] = info.get("error", "không lấy được nội dung")
            rec["hash"] = prev.get("hash", "")
            rec["snippet"] = prev.get("snippet", "")
            state[sid] = rec
            continue

        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        rec["hash"] = h
        rec["chars"] = len(text)
        rec["snippet"] = text[:SNIPPET]
        rec["status"] = "ok"
        rec["message"] = ""

        if prev.get("hash") and prev["hash"] != h:
            entry = {
                "date": today(), "ts": now_iso(), "id": sid, "market": src["market"],
                "name": src["name"], "url": src["url"],
                "kind": "thay đổi nội dung",
                "diff": diff_snippet(prev.get("snippet", ""), text[:SNIPPET]),
                "chars_before": prev.get("chars", 0), "chars_after": len(text),
            }
            changed_entries.append(entry)
            rec["last_change"] = today()
        elif not prev.get("hash"):
            rec["last_change"] = rec["last_change"] or today()
            changed_entries.append({
                "date": today(), "ts": now_iso(), "id": sid, "market": src["market"],
                "name": src["name"], "url": src["url"], "kind": "bắt đầu theo dõi",
                "diff": [], "chars_before": 0, "chars_after": len(text),
            })
        state[sid] = rec

    log = changed_entries + log
    log = log[:800]

    if dry:
        print(json.dumps({"changed": len(changed_entries), "state_size": len(state)}, ensure_ascii=False))
        return 0

    save_json(STATE_FILE, state)
    save_json(LOG_FILE, log)
    for f in DATA.glob("_tmp_*"):
        f.unlink(missing_ok=True)

    ok = sum(1 for v in state.values() if v.get("status") == "ok")
    err = sum(1 for v in state.values() if v.get("status") == "error")
    man = sum(1 for v in state.values() if v.get("status") in ("manual", "blocked"))
    print(f"Đã kiểm tra {len(state)} nguồn: {ok} bình thường, {err} lỗi, {man} cần kiểm tra thủ công.")
    print(f"Thay đổi phát hiện hôm nay: {len(changed_entries)}")

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        # chỉ báo tin khi có thay đổi nội dung thật; lần chạy đầu ghi "bắt đầu theo dõi" cho
        # cả 20 nguồn, không phải luật đổi, nên không mở issue
        real = [e for e in changed_entries if e["kind"] != "bắt đầu theo dõi"]
        body_lines = [f"- **{e['market']}** · {e['name']} — {e['url']}" for e in real]
        with open(gh_out, "a", encoding="utf-8") as fh:
            fh.write(f"changed={'true' if real else 'false'}\n")
            fh.write(f"count={len(real)}\n")
            fh.write("summary<<EOF\n" + ("\n".join(body_lines) or "Không có thay đổi.") + "\nEOF\n")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="chạy thử, không ghi file")
    a = ap.parse_args()
    sys.exit(run(a.dry_run))
