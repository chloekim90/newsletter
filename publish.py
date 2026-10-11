#!/usr/bin/env python3
"""뉴스레터 한 호를 사이트에 올리고 목록·사이트맵을 다시 만듭니다.

  python3 publish.py --date 2026-10-12 --src /path/news_brief36.html \
      --title "삼성전자가 석 달 동안 107조 원을 벌었어요" --summary "미리보기 한 줄"

  python3 publish.py --rebuild      # 글 추가 없이 index·sitemap·고정 페이지만 다시 생성

광고 코드는 partials/ 아래 파일에 넣으면 --rebuild 때 모든 페이지에 들어갑니다.
"""
import argparse, datetime, html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
SITE_NAME = "클로이의 4분 뉴스"
OLD_NAME = "오늘의 4분 뉴스"  # 메일 본문 속 이름. 웹에 올릴 때 SITE_NAME으로 바꿉니다.
INSTA = "lamuneca1124"
SITE_DESC = "평일 아침, 오늘 알아야 할 소식을 4분 안에 읽을 수 있게 정리해요."
CFG = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
BASE = CFG["base_url"].rstrip("/")          # 예: https://example.com
PREFIX = CFG.get("path_prefix", "").rstrip("/")  # 프로젝트 Pages면 "/newsletter", 자체 도메인이면 ""
WD = "월화수목금토일"


def subscribe():
    sub = CFG.get("subscribe")
    if not sub:
        return ""
    return f"""<section class="sub" id="subscribe">
<h2>📮 매일 아침 메일로 받아보기</h2>
<p>평일 아침, 새 호가 나오면 메일로 보내 드려요.</p>
<form action="{sub['action']}" method="POST" target="sub-sink" onsubmit="var f=this;setTimeout(function(){{f.hidden=true;document.getElementById('sub-done').hidden=false}},400)">
<div class="sub-row"><input type="email" name="{sub['entry']}" placeholder="이메일 주소" required autocomplete="email" aria-label="이메일 주소"><button type="submit">구독하기</button></div>
<label class="sub-agree"><input type="checkbox" required> 뉴스레터 발송을 위해 이메일 주소를 수집·이용하는 데 동의합니다. 구독 해지 시까지 보관하며, <a href="{PREFIX}/privacy.html">개인정보처리방침</a>을 따릅니다.</label>
</form>
<p id="sub-done" class="sub-done" hidden>구독 신청이 접수됐어요. 고마워요 🍊</p>
<iframe name="sub-sink" title="구독 신청 전송" hidden></iframe>
<p class="sub-contact">문의사항은 인스타그램 <a href="https://www.instagram.com/{INSTA}/">@{INSTA}</a>로 보내 주세요.</p>
</section>"""


def part(name):
    p = ROOT / "partials" / name
    return p.read_text(encoding="utf-8").strip() if p.exists() else ""


def kdate(d):
    t = datetime.date.fromisoformat(d)
    return f"{t.year}년 {t.month}월 {t.day}일 {WD[t.weekday()]}요일"


def shell(title, desc, path, body, extra_head=""):
    e = html.escape
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{BASE}{PREFIX}{path}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{BASE}{PREFIX}{path}">
<link rel="stylesheet" href="{PREFIX}/assets/site.css">
{part("head.html")}
{extra_head}
</head>
<body>
<header class="site-bar"><div class="site-bar-in">
<a href="{PREFIX}/">🍊 {SITE_NAME}</a>
<nav><a href="{PREFIX}/archive.html">지난 호</a><a class="nav-sub" href="{PREFIX}/#subscribe">구독하기</a></nav>
</div></header>
{body}
<footer class="site-foot">
<a href="{PREFIX}/archive.html">지난 호</a>·<a href="{PREFIX}/about.html">소개</a>·<a href="{PREFIX}/privacy.html">개인정보처리방침</a>
<div>의견·문의는 인스타그램 <a href="https://www.instagram.com/{INSTA}/">@{INSTA}</a></div>
<div>기사 요약은 각 언론사 보도를 바탕으로 직접 쓴 것이며, 원문 저작권은 해당 언론사에 있습니다.</div>
</footer>
</body>
</html>
"""


def load_posts():
    p = ROOT / "posts.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def add_post(date, src, title, summary):
    raw = pathlib.Path(src).read_text(encoding="utf-8")
    styles = "\n".join(re.findall(r"<style[^>]*>.*?</style>", raw, flags=re.S | re.I))
    m = re.search(r"<body[^>]*>(.*)</body>", raw, flags=re.S | re.I)
    inner = m.group(1) if m else raw
    inner = re.sub(r"<script.*?</script>", "", inner, flags=re.S | re.I)
    inner = inner.replace(OLD_NAME, SITE_NAME)
    (ROOT / "posts").mkdir(exist_ok=True)
    (ROOT / "posts" / f"{date}.body.html").write_text(styles + "\n" + inner, encoding="utf-8")
    posts = [p for p in load_posts() if p["date"] != date]
    posts.append({"date": date, "title": title, "summary": summary})
    posts.sort(key=lambda p: p["date"], reverse=True)
    (ROOT / "posts.json").write_text(json.dumps(posts, ensure_ascii=False, indent=1), encoding="utf-8")


def rebuild():
    posts = load_posts()
    e = html.escape
    for i, p in enumerate(posts):
        d = p["date"]
        content = (ROOT / "posts" / f"{d}.body.html").read_text(encoding="utf-8")
        newer = posts[i - 1]["date"] if i > 0 else None
        older = posts[i + 1]["date"] if i + 1 < len(posts) else None
        pager = '<div class="pager">' + \
            (f'<a href="{PREFIX}/posts/{older}.html">← 이전 호</a>' if older else "<span></span>") + \
            (f'<a href="{PREFIX}/posts/{newer}.html">다음 호 →</a>' if newer else "<span></span>") + "</div>"
        body = f'<div class="ad">{part("ad-top.html")}</div>\n<main class="post">\n{content}\n</main>\n{pager}\n{subscribe()}\n<div class="ad">{part("ad-bottom.html")}</div>'
        (ROOT / "posts" / f"{d}.html").write_text(
            shell(f'{p["title"]} | {SITE_NAME}', p.get("summary") or p["title"], f"/posts/{d}.html", body),
            encoding="utf-8")
        if i == 0:  # 첫 화면은 항상 최신호
            (ROOT / "index.html").write_text(
                shell(SITE_NAME, p.get("summary") or SITE_DESC, "/", body), encoding="utf-8")

    if posts:
        items = "\n".join(
            f'<li><a href="{PREFIX}/posts/{p["date"]}.html"><time datetime="{p["date"]}">{kdate(p["date"])}</time>'
            f'<h2>{e(p["title"])}</h2>' + (f'<p>{e(p["summary"])}</p>' if p.get("summary") else "") + "</a></li>"
            for p in posts)
        listing = f'<ul class="list">\n{items}\n</ul>'
    else:
        listing = '<div class="empty">첫 호가 곧 올라와요.</div>'
    body = f'<main class="wrap"><section class="hero"><h1>지난 호</h1><p>{SITE_DESC}</p></section>\n' \
           f'<div class="ad">{part("ad-top.html")}</div>\n{listing}</main>\n{subscribe()}'
    (ROOT / "archive.html").write_text(shell(f"지난 호 | {SITE_NAME}", SITE_DESC, "/archive.html", body), encoding="utf-8")
    if not posts:
        (ROOT / "index.html").write_text(shell(SITE_NAME, SITE_DESC, "/", body), encoding="utf-8")

    for name, title in (("about", "소개"), ("privacy", "개인정보처리방침")):
        src = (ROOT / "pages" / f"{name}.html").read_text(encoding="utf-8")
        body = f'<main class="wrap"><article class="page">{src}</article></main>'
        (ROOT / f"{name}.html").write_text(shell(f"{title} | {SITE_NAME}", title, f"/{name}.html", body), encoding="utf-8")

    urls = [f"{BASE}{PREFIX}/", f"{BASE}{PREFIX}/archive.html"] + [f"{BASE}{PREFIX}/posts/{p['date']}.html" for p in posts] + \
           [f"{BASE}{PREFIX}/about.html", f"{BASE}{PREFIX}/privacy.html"]
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "\n".join(f"<url><loc>{u}</loc></url>" for u in urls) + "\n</urlset>\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}{PREFIX}/sitemap.xml\n", encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date"); ap.add_argument("--src"); ap.add_argument("--title"); ap.add_argument("--summary", default="")
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args()
    if not a.rebuild:
        if not (a.date and a.src and a.title):
            sys.exit("--date, --src, --title 이 필요합니다")
        datetime.date.fromisoformat(a.date)
        add_post(a.date, a.src, a.title, a.summary)
    rebuild()
    print("ok:", len(load_posts()), "posts")
