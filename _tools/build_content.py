"""
가격·시공 사례 페이지 생성기 (홈 + 서비스 7장)

실행:
    cd C:\\projects\\cheongnyeon-baegwan\\_tools
    python build_content.py            먼저 이것. 무엇이 바뀌는지 보여 주기만 하고 파일은 안 쓴다
    python build_content.py --write    보여 준 내용이 맞을 때만. 바뀌는 파일만 쓴다

GitHub 에서는 .github/workflows/site.yml 이 main 에 push 될 때마다 --write 로 돌린다.
사장님이 관리 화면(구글 Apps Script)에서 가격이나 사례를 저장하면 content/ 의 json 이 GitHub 에 커밋되고,
그 자동 작업이 이 파일을 돌려 페이지를 다시 만든다.

────────────────────────────────────────────────────────
무엇을 읽어서 무엇을 만드나

  content/prices.json           가격 (원 단위 숫자, 사장님이 고침)        ┐
  content/cases/<페이지>.json   시공 사례 (글·사진·블로그, 사장님이 고침)  ├→ index.html
  _tools/src/<페이지>.html      페이지 원본 틀 (글·디자인, 클로드가 고침)   ┘   toilet/index.html … pipe/index.html

  틀 안의 {{p.toilet.simple_min:won}} 자리에는 50,000 모양으로,
           {{p.toilet.simple_min:man}} 자리에는 5 모양(만원 단위)으로 같은 가격이 들어간다.
  그래서 가격 하나를 고치면 홈 화면 표·서비스 페이지 제목·표·자주 묻는 질문이 한꺼번에 바뀐다.
  틀 안의 {{CASES}} 줄에는 그 페이지의 시공 사례 목록이 들어간다.

⚠️ 만들어진 index.html, toilet/index.html 같은 8장을 직접 고치지 않는다.
   다음에 돌리면 틀과 content 내용으로 덮어써진다. 글은 _tools/src/ 의 틀을, 가격·사례는 content/ 를 고친다.
   GitHub 자동 작업은 push 에 이 8장(과 지역 9장)을 직접 고친 흔적이 있으면 멈추고 사이트를 바꾸지 않는다.

⚠️ 지역 페이지 9장은 이 파일이 아니라 build_pages.py 가 만든다. 서로 건드리지 않는다.

2026-10-27 처음 만들 때 지금 HTML 8장에서 가격 숫자 122곳(57줄)과 사례 24개를 뽑아 옮겼고,
그대로 돌리면 8장이 한 글자도 다르지 않게(바이트까지 같게) 나오는 것을 확인했다.
예) 변기 단순 막힘 최소 가격(toilet.simple_min)은 8곳에 나온다:
    홈 index.html 383·436줄(SVCS·PRICES), 변기 페이지 제목·설명·og:title·JSON-LD 질문·가격표·자주 묻는 질문.

사진 크기(width·height)는 사진 파일에서 읽는다. 단 photos/drain-sangmu-05.webp 하나는
파일이 가로(1200×554)인데 페이지에는 세로(554×1200)로 적혀 있어, 지금 모양을 그대로 두려고
content/cases/drain.json 에 width·height 를 따로 적어 두었다. 사진을 바꾸면 그 두 줄을 지운다.
────────────────────────────────────────────────────────

이 파일이 멈추는 경우 (아무 파일도 쓰지 않는다)
  - 가격이 비었거나, 숫자가 아니거나, 1,000원 단위가 아니거나, 최소가 최대보다 큰 경우
  - 사례 사진 파일이 photos/ 에 없거나, 아직 줄이지 않은 올린 사진(/_uploads/…)이 남아 있는 경우
    → process_photos.py --write 를 먼저 돌린다 (자동 작업은 이 순서로 돈다)
  - 만든 페이지의 태그 짝이 안 맞거나, 채우지 못한 {{…}} 자리가 남은 경우 ("확인필요")
"""

import datetime
import difflib
import html
import json
import pathlib
import re
import sys

from PIL import Image

SITE = pathlib.Path(__file__).resolve().parent.parent
SRC = pathlib.Path(__file__).resolve().parent / "src"
CONTENT = SITE / "content"

# (틀 이름, 만들 파일, 사례 파일 이름 또는 None)
PAGES = [("index", "index.html", None)] + [
    (p, f"{p}/index.html", p) for p in ("toilet", "sink", "drain", "jet", "faucet", "leak", "pipe")]

PRICE_SLOT = re.compile(r"\{\{p\.([a-z_]+)\.([a-z_]+):(won|man)\}\}")
CASES_SLOT = "{{CASES}}\n"

# 사진 위 작은 표시. 이 셋은 노란색(tag-a), 나머지는 회색(tag-b). build_pages.py 와 같은 규칙
TAG_A = ("작업 후", "고친 자리", "원인")
MORE_TEXT = "이 작업 블로그에서 더 보기 ›"


class Stop(Exception):
    """사장님 데이터에 문제가 있어 멈출 때. 메시지는 그대로 보여 준다."""


# ── 파일 읽기 ─────────────────────────────────────────

def read_json(path: pathlib.Path):
    """content/ 의 json 읽기. 모양이 깨졌으면 몇째 줄인지 알려 주고 멈춘다."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        raise Stop(f"{path.relative_to(SITE).as_posix()}: json 모양이 깨졌습니다 ({e})")


# ── 가격 ──────────────────────────────────────────────

def load_prices() -> dict:
    data = read_json(CONTENT / "prices.json") or {}
    if not isinstance(data, dict):
        raise Stop("가격 파일(content/prices.json)이 묶음 모양이 아닙니다")
    problems = []
    clean = {}
    for group, items in data.items():
        if not isinstance(items, dict):
            problems.append(f"{group}: 묶음 모양이 아닙니다")
            continue
        for name, value in items.items():
            where = f"{group}.{name}"
            if isinstance(value, float) and value.is_integer():
                value = int(value)
            if isinstance(value, bool) or not isinstance(value, int):
                problems.append(f"{where}: 숫자가 아닙니다 ({value!r})")
                continue
            if value < 1000 or value > 100_000_000 or value % 1000:
                problems.append(f"{where}: {value:,}원 — 1,000원 단위의 1,000원~1억원 사이 숫자여야 합니다")
                continue
            clean[(group, name)] = value
    for (group, name), low in clean.items():
        if name.endswith("_min"):
            high = clean.get((group, name[:-4] + "_max"))
            if high is not None and low > high:
                problems.append(f"{group}.{name[:-4]}: 최소 {low:,}원이 최대 {high:,}원보다 큽니다")
    if problems:
        raise Stop("가격 파일(content/prices.json)에 문제가 있습니다:\n    " + "\n    ".join(problems))
    return clean


def won(value: int) -> str:
    return f"{value:,}"                      # 50000 → 50,000


def man(value: int) -> str:
    if value % 10000 == 0:
        return str(value // 10000)           # 50000 → 5   (틀에서 '5만원')
    return f"{value / 10000:g}"              # 65000 → 6.5 (틀에서 '6.5만원')


def fill_prices(text: str, prices: dict, label: str) -> str:
    missing = []

    def put(m):
        key = (m.group(1), m.group(2))
        if key not in prices:
            missing.append(".".join(key))
            return m.group(0)
        return won(prices[key]) if m.group(3) == "won" else man(prices[key])

    out = PRICE_SLOT.sub(put, text)
    if missing:
        raise Stop(f"{label} 틀에 있는 가격이 content/prices.json 에 없습니다: {', '.join(sorted(set(missing)))}")
    return out


# ── 시공 사례 ─────────────────────────────────────────

def esc(s: str) -> str:
    return html.escape(s, quote=False)


def attr(s: str) -> str:
    return html.escape(s, quote=True).replace("&#x27;", "'")


def inline(s: str) -> str:
    """사장님 글 → HTML. **굵게** 만 <b> 로 바꾸고 나머지 꺾쇠 등은 글자로 보이게 한다."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(s))


def text_of(value, where: str, required=False) -> str:
    if value is None:
        value = ""
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    if required and not value:
        raise Stop(f"{where}: 비어 있으면 안 됩니다")
    return value


def date_text(value, where: str) -> str:
    """2026-09-10 → 2026년 9월 10일. 비어 있으면 빈 글."""
    if value in (None, ""):
        return ""
    if isinstance(value, datetime.datetime):
        value = value.date()
    if isinstance(value, str):
        try:
            value = datetime.date.fromisoformat(value.strip()[:10])
        except ValueError:
            raise Stop(f"{where}: 날짜 모양이 아닙니다 ({value!r})")
    if not isinstance(value, datetime.date):
        raise Stop(f"{where}: 날짜 모양이 아닙니다 ({value!r})")
    return f"{value.year}년 {value.month}월 {value.day}일"


def photo_size(photo: dict, path: pathlib.Path, where: str):
    w, h = photo.get("width"), photo.get("height")
    if w and h:          # 페이지에 적힌 크기를 따로 적어 둔 사진 (drain 상무지구 05 하나, 아래 설명)
        return int(w), int(h)
    with Image.open(path) as im:
        return im.size


def render_case(case: dict, where: str) -> list:
    if not isinstance(case, dict):
        raise Stop(f"{where}: 사례 모양이 아닙니다")
    day = date_text(case.get("date"), where + " 날짜")
    place = text_of(case.get("place"), where + " 장소")
    if not day and not place:
        raise Stop(f"{where}: 날짜나 장소 중 하나는 있어야 합니다")
    title = text_of(case.get("title"), where + " 제목") or "무엇이 문제였나"
    summary = text_of(case.get("summary"), where + " 내용", required=True)
    paragraphs = [" ".join(p.split("\n")).strip() for p in re.split(r"\n\s*\n", summary) if p.strip()]

    photos = []
    for n, photo in enumerate(case.get("photos") or [], 1):
        pw = f"{where} 사진 {n}"
        if not isinstance(photo, dict):
            raise Stop(f"{pw}: 모양이 아닙니다")
        file = text_of(photo.get("file"), pw + " 파일", required=True).lstrip("/")
        if file.startswith("_uploads/"):
            raise Stop(f"{pw}: 아직 줄이지 않은 올린 사진입니다 ({file}). process_photos.py --write 를 먼저 돌리세요")
        if not file.startswith("photos/"):
            raise Stop(f"{pw}: photos/ 폴더의 사진이 아닙니다 ({file})")
        path = SITE / file
        if not path.is_file():
            raise Stop(f"{pw}: 사진 파일이 없습니다 ({file})")
        caption = text_of(photo.get("caption"), pw + " 설명")
        tag = text_of(photo.get("tag"), pw + " 표시")
        w, h = photo_size(photo, path, pw)
        photos.append((file, caption, tag, w, h))

    # 가로 사진이 하나라도 있으면 가로 배치(case-land). 2026-10-27 지금 사례 24개가 모두 이 규칙을 따른다.
    layout = text_of(case.get("layout"), where + " 배치")
    land = {"land": True, "normal": False}.get(layout, any(w > h for _, _, _, w, h in photos))

    rows = [f'      <article class="case{" case-land" if land else ""} rv">',
            '        <div class="case-hd">',
            f'          <p class="case-where">{esc(" · ".join(x for x in (day, place) if x))}</p>',
            f'          <h3>{esc(title)}</h3>']
    rows += [f'          <p class="case-sum">{inline(p)}</p>' for p in paragraphs]
    rows.append('        </div>')
    facts = [(text_of(f.get("name"), where), text_of(f.get("value"), where))
             for f in (case.get("facts") or []) if isinstance(f, dict)]
    facts = [(k, v) for k, v in facts if k or v]
    if facts:
        rows.append('        <dl class="case-facts">')
        rows += [f'          <div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in facts]
        rows.append('        </dl>')
    if photos:
        rows.append('        <div class="case-shots">')
        for file, caption, tag, w, h in photos:
            tall = ' class="tall"' if land and h > w else ""
            label = f'<span class="tag tag-{"a" if tag in TAG_A else "b"}">{esc(tag)}</span>' if tag else ""
            rows += ['        <figure>',
                     f'          <img{tall} src="../{attr(file)}" alt="{attr(caption)}" loading="lazy" width="{w}" height="{h}">',
                     f'          <figcaption>{label}{esc(caption)}</figcaption>',
                     '        </figure>']
        rows.append('        </div>')
    blog = text_of(case.get("blog"), where + " 블로그 주소")
    if blog:
        if not re.match(r"^https://[^\s\"<>]+$", blog):
            raise Stop(f"{where}: 블로그 주소는 https:// 로 시작해야 합니다 ({blog})")
        rows.append(f'        <p class="case-more"><a class="pg-case-link" href="{attr(blog)}" '
                    f'target="_blank" rel="noopener">{MORE_TEXT}</a></p>')
    rows.append('      </article>')
    return rows


def render_cases(name: str) -> str:
    path = CONTENT / "cases" / f"{name}.json"
    data = read_json(path) if path.exists() else []
    if data is None:
        data = []
    if isinstance(data, dict) and "cases" in data:      # {cases: [...]} 모양으로 바뀌어도 읽는다
        data = data["cases"] or []
    if not isinstance(data, list):
        raise Stop(f"content/cases/{name}.json: 사례 목록 모양이 아닙니다")
    rows = []
    for n, case in enumerate(data, 1):
        rows += render_case(case, f"content/cases/{name}.json 사례 {n}")
    return "".join(r + "\n" for r in rows)


# ── 페이지 만들기 ─────────────────────────────────────

def read_template(name: str) -> str:
    text = (SRC / f"{name}.html").read_text(encoding="utf-8-sig")   # BOM 이 붙어 저장돼도 괜찮게
    text = text.replace("\r\n", "\n")
    return re.sub(r"^<!--.*?-->\n", "", text, count=1, flags=re.S)  # 틀 맨 위 설명 주석은 빼고


def build(name: str, cases: str, prices: dict) -> str:
    page = fill_prices(read_template(name), prices, f"_tools/src/{name}.html")
    if cases is not None:
        if page.count(CASES_SLOT) != 1:
            raise Stop(f"_tools/src/{name}.html 에 {{{{CASES}}}} 줄이 꼭 하나 있어야 합니다")
        page = page.replace(CASES_SLOT, render_cases(cases))
    return page


def check(page: str) -> str:
    left = re.findall(r"\{\{[^}]*\}\}", page)
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
        try:
            json.loads(block)
        except ValueError:
            left.append("JSON-LD")
    bad = [t for t in ("div", "section", "nav", "footer", "header", "html", "body", "article", "figure", "dl")
           if len(re.findall(f"<{t}[ >]", page)) != len(re.findall(f"</{t}>", page))]
    return "정상" if not bad and not left else f"확인필요 {bad}{left}"


PHOTO = re.compile(r'<img\b[^>]*?\ssrc="(?:\.\./)?([^"]+)"')
SHOW = 10   # 파일마다 보여 줄 줄 수 (없어지는 줄·생기는 줄 각각)


def lines_note(title: str, lines: list) -> str:
    rows = [s.strip() for s in lines if s.strip()]
    if not rows:
        return ""
    shown = "".join(f"\n        {s[:120]}{'…' if len(s) > 120 else ''}" for s in rows[:SHOW])
    more = f"\n        … 외 {len(rows) - SHOW}줄" if len(rows) > SHOW else ""
    return f"\n      {title} {len(rows)}줄:{shown}{more}"


def compare(path: pathlib.Path, new: str) -> str:
    """지금 파일과 새로 만든 내용을 견줘 알려준다. 같으면 빈 문자열. (build_pages.py 와 같은 방식)"""
    if not path.exists():
        return "새 파일"
    old = path.read_text(encoding="utf-8")
    if old == new:
        return ""
    gone, came = [], []
    a, b = old.splitlines(), new.splitlines()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag != "equal":
            gone += a[i1:i2]
            came += b[j1:j2]
    note = f"바뀜 +{len(came)}줄 / -{len(gone)}줄"
    lost = sorted(set(PHOTO.findall(old)) - set(PHOTO.findall(new)))
    added = sorted(set(PHOTO.findall(new)) - set(PHOTO.findall(old)))
    if lost:
        note += f"\n      [주의] 빠지는 사진 {len(lost)}장: {', '.join(lost)}"
    if added:
        note += f"\n      들어가는 사진 {len(added)}장: {', '.join(added)}"
    return note + lines_note("없어지는 줄", gone) + lines_note("생기는 줄", came)


def render_all() -> list:
    """[(라벨, 만들 파일 경로, 내용, 상태)] — 시험(tests)에서도 이 함수를 부른다."""
    prices = load_prices()
    out = []
    for name, rel, cases in PAGES:
        page = build(name, cases, prices)
        out.append((rel, SITE / rel, page, check(page)))
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    write = "--write" in sys.argv[1:]
    try:
        outputs = render_all()
    except Stop as e:
        print(f"멈춤: {e}\n아무 파일도 쓰지 않았습니다.")
        sys.exit(2)

    changed, broken = [], []
    for rel, path, text, state in outputs:
        diff = compare(path, text)
        print(f"  {rel}  {text.count(chr(10))}줄  {state}  · {diff or '같음'}")
        if state != "정상":
            broken.append(rel)
        if diff:
            changed.append((path, text))

    if broken:
        print(f"\n확인필요 {len(broken)}개: {', '.join(broken)}. 아무 파일도 쓰지 않았습니다.")
        sys.exit(2)
    if not changed:
        print("\n지금 파일과 모두 같습니다. 쓸 것이 없습니다.")
        return
    if not write:
        print(f"\n바뀌는 파일 {len(changed)}개. 아직 아무 파일도 쓰지 않았습니다.")
        print("내가 고치지 않은 없어지는 줄·생기는 줄이 있으면 쓰지 마세요.")
        print("위 내용이 고친 의도와 맞을 때만 다시 실행: python build_content.py --write")
        sys.exit(1)
    for path, text in changed:
        path.parent.mkdir(exist_ok=True)
        path.write_text(text, encoding="utf-8")   # 줄 끝은 컴퓨터 방식대로 (윈도우 CRLF, GitHub LF) — build_pages.py 와 같음
        print(f"  썼음: {path.relative_to(SITE).as_posix()}")
    print(f"\n{len(changed)}개 파일을 썼습니다.")


if __name__ == "__main__":
    main()
