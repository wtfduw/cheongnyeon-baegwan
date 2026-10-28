"""
가격·시공 사례·자주 묻는 질문·서비스 설명·공지 페이지 생성기 (홈 + 서비스 7장, 공지 띠는 개인정보처리방침에도)

실행:
    cd C:\\projects\\cheongnyeon-baegwan\\_tools
    python build_content.py            먼저 이것. 무엇이 바뀌는지 보여 주기만 하고 파일은 안 쓴다
    python build_content.py --write    보여 준 내용이 맞을 때만. 바뀌는 파일만 쓴다

GitHub 에서는 .github/workflows/site.yml 이 main 에 push 될 때마다 --write 로 돌린다.
사장님이 관리 화면(구글 Apps Script)에서 저장하면 content/ 의 json 이 GitHub 에 커밋되고,
그 자동 작업이 이 파일을 돌려 페이지를 다시 만든다.

────────────────────────────────────────────────────────
무엇을 읽어서 무엇을 만드나

  content/prices.json           가격 (원 단위 숫자) + 글자로 바꾼 가격(_text) + 가격 안내 문구(_guide)   ┐
  content/cases/<페이지>.json   시공 사례 (글·사진·블로그)                                              │
  content/faq/<페이지>.json     자주 묻는 질문 (홈 index 포함 8개)                                       ├→ index.html
  content/services.json         홈 서비스 칸의 이름·증상·가격 설명, 서비스 페이지 맨 위 소개 글          │   toilet/index.html … pipe/index.html
  content/notice.json           공지 띠 (켜기/끄기, 문구, 기간)                                          │   (공지 띠는 privacy/index.html 에도)
  _tools/src/<페이지>.html      페이지 원본 틀 (글·디자인, 클로드가 고침)                                 ┘
  사장님은 위 content/ 를 관리 화면 탭(시공사례·가격·자주 묻는 질문·서비스 안내·공지)에서 고친다.

  틀 안의 자리
    {{p.toilet.simple_min:won}}  → 50,000      {{…:man}} → 5 (만원 단위, 틀에는 '{{…:man}}만원')    {{…:num}} → 50000 (JSON-LD 숫자)
    {{CASES}} 줄                 → 그 페이지 시공 사례 목록
    {{FAQ}} 줄                   → 자주 묻는 질문 목록 (홈은 한 줄짜리 모양, 서비스 페이지는 세 줄짜리 모양 — 지금 HTML 그대로)
    {{FAQ_LD}} 줄                → '구글 검색 결과에도 넣기'(search)를 켠 질문만 모은 FAQPage JSON-LD. 하나도 없으면 묶음째 빠진다
    {{s.toilet.name}} 등         → content/services.json 의 글 (name·symptoms·price_note 는 홈 SVCS 자바스크립트 안, intro 는 맨 위 소개 글)
    {{PRICE_GUIDE}} 줄           → 가격 안내 문구. 비어 있으면 줄째 빠진다 (그래서 비어 있으면 지금 HTML 과 한 글자도 다르지 않다)

  가격을 '글자'로 (관리 화면 가격 탭의 [숫자|글자])
    content/prices.json 의 "_text": {"toilet.simple": "상담 후 결정"} 처럼 가격 줄 하나를 글자로 바꾼다.
    가격 줄 이름: 최소·최대 짝이 있으면 앞부분(toilet.simple = simple_min + simple_max), 없으면 그 이름 그대로(toilet.replace_min).
    숫자는 지우지 않고 그대로 둔다(다시 '숫자'로 돌리면 그 숫자가 나온다).
    글자로 바꾼 줄의 가격 자리는 이렇게 바뀐다:
      1) 틀의 {{#num 줄,…}}A{{#else}}B{{/num}} → 모두 숫자면 A, 아니면 B (B 는 없어도 됨 = 빠짐)
         {{#any 줄,…}}A{{/any}} → 하나라도 숫자면 A,  {{#text 줄,…}}A{{/text}} → 하나라도 글자면 A
         제목·설명·og·JSON-LD 처럼 '· 5만원부터' 를 통째로 빼야 하는 곳에 쓴다.
      2) 나머지 가격 덩어리 — '5만원부터', '50,000 ~ 100,000원', '5만원에서 10만원', '10~30만원 이상', '50,000원~' —
         는 덩어리째 그 글자로 바뀐다. (예: '단순 막힘은 5만원에서 10만원입니다' → '단순 막힘은 상담 후 결정입니다')
      3) 그래도 남은 글자 줄의 가격 자리가 있으면 멈춘다(틀에 {{#num}} 을 더 감싸야 한다).
    글자는 10자까지, 한글·영문·숫자·띄어쓰기와 · , . ( ) ~ / + % - 만 (따옴표·꺾쇠가 없어야 HTML·자바스크립트·JSON 어디에 넣어도 안전하다).

  공지 띠: content/notice.json 이 켜져 있으면 17장 + 개인정보처리방침의 머리(상단 고정 묶음) 바로 아래에 한 줄 띠를 넣는다.
    끝나는 날이 지났으면 넣지 않는다. 시작 전·끝난 뒤에는 띠 바로 뒤 작은 스크립트가 방문자 화면에서 숨긴다
    (그래서 다시 만들지 않아도 그날이 되면 보이고, 지나면 사라진다. 한국 시간 기준).
    꺼져 있으면 아무것도 넣지 않는다 = 지금 HTML 과 한 글자도 다르지 않다.
    지역 9장은 build_pages.py 가 이 파일의 notice_block · insert_notice 를 불러 같은 띠를 넣는다.
    개인정보처리방침은 손으로 쓰는 파일이라, 이 파일은 그 안의 공지 띠 묶음(<!-- 공지 띠 … --> ~ <!-- /공지 띠 -->)만 넣고 뺀다.

⚠️ 만들어진 index.html, toilet/index.html 같은 8장을 직접 고치지 않는다.
   다음에 돌리면 틀과 content 내용으로 덮어써진다. 글은 _tools/src/ 의 틀을, 가격·사례 등은 content/ 를 고친다.
   GitHub 자동 작업은 push 에 이 8장(과 지역 9장)을 직접 고친 흔적이 있으면 멈추고 사이트를 바꾸지 않는다.

⚠️ 지역 페이지 9장은 이 파일이 아니라 build_pages.py 가 만든다. 서로 건드리지 않는다(공지 띠 함수만 빌려 간다).

2026-10-27 처음 만들 때 지금 HTML 8장에서 가격 숫자 122곳(57줄)과 사례 24개를 뽑아 옮겼고,
그대로 돌리면 8장이 한 글자도 다르지 않게(바이트까지 같게) 나오는 것을 확인했다.
2026-10-28 자주 묻는 질문(8장 47개, 검색용 34개)·서비스 설명·공지·가격 글자 바꾸기를 더할 때도 같은 확인을 했다.
  - 검색용(JSON-LD) 질문·답은 화면 글과 문장이 다른 곳이 많아 search_q·search_a 에 따로 적었다(비우면 화면 글로).
  - 수전 페이지는 검색용 순서가 화면 순서와 달라 search_order 로 적었다. 관리 화면에서 순서를 바꾸면 이 값은 지워지고 화면 순서를 따른다.
  - 변기 페이지 JSON-LD 의 minPrice·maxPrice(50000·100000)는 가격 파일과 따로 적혀 있어 가격을 바꿔도 안 바뀌던 것을 가격 자리로 바꿨다.
예) 변기 단순 막힘 최소 가격(toilet.simple_min)은 9곳에 나온다:
    홈 SVCS·PRICES, 변기 페이지 제목·설명·og:title·JSON-LD 가격·JSON-LD 질문·가격표·자주 묻는 질문.

사진 크기(width·height)는 사진 파일에서 읽는다. 단 photos/drain-sangmu-05.webp 하나는
파일이 가로(1200×554)인데 페이지에는 세로(554×1200)로 적혀 있어, 지금 모양을 그대로 두려고
content/cases/drain.json 에 width·height 를 따로 적어 두었다. 사진을 바꾸면 그 두 줄을 지운다.
────────────────────────────────────────────────────────

이 파일이 멈추는 경우 (아무 파일도 쓰지 않는다)
  - 가격이 비었거나, 숫자가 아니거나, 1,000원 단위가 아니거나, 최소가 최대보다 큰 경우
  - 글자로 바꾼 가격(_text)·안내 문구(_guide)·자주 묻는 질문·서비스 설명·공지의 모양이나 길이가 규칙에 맞지 않는 경우
    (관리 화면 Code.gs 가 저장 전에 같은 규칙으로 막는다)
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
SERVICES = ("toilet", "sink", "drain", "jet", "faucet", "leak", "pipe")
PRIVACY = "privacy/index.html"          # 손으로 쓰는 파일. 공지 띠 묶음만 넣고 뺀다

PRICE_SLOT = re.compile(r"\{\{p\.([a-z_]+)\.([a-z_]+):(won|man|num)\}\}")
_SLOT = r"\{\{p\.[a-z_]+\.[a-z_]+:(?:won|man)\}\}"
# 가격 덩어리: 50,000원~ / 50,000 ~ 100,000원 / 5만원부터 / 5만원에서 10만원 / 10~30만원 이상
PRICE_RUN = re.compile(_SLOT + r"(?:만원|원)?(?: ?(?:~|에서) ?" + _SLOT + r")?(?:만원|원)(?: 이상|부터| ~|~)?")
BLOCK = re.compile(r"\{\{#(num|any|text) ([a-z_.,]+)\}\}(.*?)(?:\{\{#else\}\}(.*?))?\{\{/\1\}\}", re.S)
SVC_SLOT = re.compile(r"\{\{s\.([a-z]+)\.([a-z_]+)\}\}")
CASES_SLOT = "{{CASES}}\n"
FAQ_SLOT = "{{FAQ}}\n"
FAQ_LD_SLOT = "{{FAQ_LD}}\n"
GUIDE_SLOT = "{{PRICE_GUIDE}}\n"

# 사진 위 작은 표시. 이 셋은 노란색(tag-a), 나머지는 회색(tag-b). build_pages.py 와 같은 규칙
TAG_A = ("작업 후", "고친 자리", "원인")
MORE_TEXT = "이 작업 블로그에서 더 보기 ›"

# 사장님 글 규칙 — 관리 화면 Code.gs 의 같은 이름 숫자와 맞춘다
PRICE_TEXT_OK = re.compile(r"^[0-9A-Za-z가-힣·,.()~/+%\- ]{1,10}$")
GUIDE_MAX, NOTICE_MAX = 120, 100
FAQ_MAX_ITEMS, FAQ_Q_MAX, FAQ_A_MAX = 20, 120, 1500
SVC_NAME_MAX, SVC_SYM_MAX, SVC_SYM_ITEMS, SVC_NOTE_MAX, SVC_INTRO_LINES, SVC_INTRO_LINE_MAX = 20, 40, 6, 60, 3, 80


class Stop(Exception):
    """사장님 데이터에 문제가 있어 멈출 때. 메시지는 그대로 보여 준다."""


def kst_today() -> str:
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()


# ── 파일 읽기 ─────────────────────────────────────────

def read_json(path: pathlib.Path):
    """content/ 의 json 읽기. 모양이 깨졌으면 몇째 줄인지 알려 주고 멈춘다."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        raise Stop(f"{path.relative_to(SITE).as_posix()}: json 모양이 깨졌습니다 ({e})")


def one_line(value, where: str, most: int, required=False) -> str:
    """한 줄 글 검사. 줄바꿈·{{ }} 가 있거나 너무 길면 멈춘다."""
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise Stop(f"{where}: 글이 아닙니다 ({value!r})")
    value = value.strip()
    if "\n" in value or "\r" in value:
        raise Stop(f"{where}: 한 줄로 적어야 합니다")
    if "{{" in value or "}}" in value:
        raise Stop(f"{where}: {{{{ }}}} 는 쓸 수 없습니다")
    if required and not value:
        raise Stop(f"{where}: 비어 있으면 안 됩니다")
    if len(value) > most:
        raise Stop(f"{where}: {most}자까지입니다 (지금 {len(value)}자)")
    return value


def date_or_empty(value, where: str) -> str:
    value = "" if value is None else str(value).strip()
    if not value:
        return ""
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError
        datetime.date.fromisoformat(value)
    except ValueError:
        raise Stop(f"{where}: 날짜 모양이 아닙니다 ({value!r}, 예: 2026-11-01)")
    return value


# ── 가격 ──────────────────────────────────────────────

class Prices:
    """values: {(묶음, 이름): 원}, text: {가격 줄: 글자}, guide: 안내 문구"""

    def __init__(self, values: dict, text: dict, guide: str):
        self.values, self.text, self.guide = values, text, guide

    def row(self, group: str, name: str) -> str:
        return row_of(group, name, self.values)

    def rows(self) -> list:
        out = []
        for g, k in self.values:
            r = self.row(g, k)
            if r not in out:
                out.append(r)
        return out


def row_of(group: str, name: str, keys) -> str:
    """가격 줄 이름. simple_min + simple_max 짝이면 toilet.simple, 짝이 없으면 toilet.replace_min"""
    for mine, other in (("_min", "_max"), ("_max", "_min")):
        if name.endswith(mine) and (group, name[:-4] + other) in keys:
            return f"{group}.{name[:-4]}"
    return f"{group}.{name}"


def load_prices() -> Prices:
    data = read_json(CONTENT / "prices.json") or {}
    if not isinstance(data, dict):
        raise Stop("가격 파일(content/prices.json)이 묶음 모양이 아닙니다")
    problems = []
    clean = {}
    for group, items in data.items():
        if group.startswith("_"):
            if group not in ("_text", "_guide"):
                problems.append(f"{group}: 모르는 칸입니다")
            continue
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
    rows = {row_of(g, k, clean) for g, k in clean}
    text = {}
    raw_text = data.get("_text") or {}
    if not isinstance(raw_text, dict):
        problems.append("_text: 묶음 모양이 아닙니다")
        raw_text = {}
    for row, value in raw_text.items():
        if row not in rows:
            problems.append(f"_text.{row}: 없는 가격 줄입니다")
        elif not isinstance(value, str) or not PRICE_TEXT_OK.match(value) or value != value.strip():
            problems.append(f"_text.{row}: 글자는 10자까지, 한글·영문·숫자·띄어쓰기와 · , . ( ) ~ / + % - 만 됩니다 ({value!r})")
        else:
            text[row] = value
    try:
        guide = one_line(data.get("_guide"), "_guide(가격 안내 문구)", GUIDE_MAX)
    except Stop as e:
        problems.append(str(e))
        guide = ""
    if problems:
        raise Stop("가격 파일(content/prices.json)에 문제가 있습니다:\n    " + "\n    ".join(problems))
    return Prices(clean, text, guide)


def won(value: int) -> str:
    return f"{value:,}"                      # 50000 → 50,000


def man(value: int) -> str:
    if value % 10000 == 0:
        return str(value // 10000)           # 50000 → 5   (틀에서 '5만원')
    return f"{value / 10000:g}"              # 65000 → 6.5 (틀에서 '6.5만원')


def resolve_blocks(text: str, prices: Prices, label: str) -> str:
    """{{#num 줄,…}}A{{#else}}B{{/num}} 등 — 가격 줄이 숫자인지 글자인지에 따라 고른다"""
    known = set(prices.rows())

    def pick(m):
        kind, rows, a, b = m.group(1), m.group(2).split(","), m.group(3), m.group(4) or ""
        bad = [r for r in rows if r not in known]
        if bad:
            raise Stop(f"{label} 틀의 {{{{#{kind} …}}}} 에 없는 가격 줄이 있습니다: {', '.join(bad)}")
        number = [r not in prices.text for r in rows]
        ok = all(number) if kind == "num" else any(number) if kind == "any" else not all(number)
        return a if ok else b

    return BLOCK.sub(pick, text)


def text_runs(text: str, prices: Prices) -> str:
    """글자로 바꾼 가격 줄이 든 가격 덩어리를 그 글자로 바꾼다"""
    if not prices.text:
        return text

    def put(m):
        for g, k, _ in PRICE_SLOT.findall(m.group(0)):
            r = prices.row(g, k)
            if r in prices.text:
                return prices.text[r]
        return m.group(0)

    return PRICE_RUN.sub(put, text)


def fill_prices(text: str, prices: Prices, label: str) -> str:
    missing, stuck = [], []

    def put(m):
        key = (m.group(1), m.group(2))
        if key not in prices.values:
            missing.append(".".join(key))
            return m.group(0)
        if prices.row(*key) in prices.text:
            stuck.append(f"{'.'.join(key)}:{m.group(3)}")
            return m.group(0)
        v = prices.values[key]
        return won(v) if m.group(3) == "won" else man(v) if m.group(3) == "man" else str(v)

    out = PRICE_SLOT.sub(put, text)
    if missing:
        raise Stop(f"{label} 틀에 있는 가격이 content/prices.json 에 없습니다: {', '.join(sorted(set(missing)))}")
    if stuck:
        raise Stop(f"{label}: 글자로 바꾼 가격이 들어갈 수 없는 자리가 남았습니다: {', '.join(sorted(set(stuck)))}"
                   " — 틀의 그 자리를 {{#num …}} 으로 감싸야 합니다")
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


# ── 자주 묻는 질문 ────────────────────────────────────

def faq_text(value, where: str, most: int, prices: Prices, multi: bool, required: bool) -> str:
    """질문·답 글 검사. 가격 자리 {{p.묶음.이름:man|won}} 만 쓸 수 있다."""
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise Stop(f"{where}: 글이 아닙니다 ({value!r})")
    value = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not multi and "\n" in value:
        raise Stop(f"{where}: 한 줄로 적어야 합니다")
    if required and not value:
        raise Stop(f"{where}: 비어 있으면 안 됩니다")
    if len(value) > most:
        raise Stop(f"{where}: {most}자까지입니다 (지금 {len(value)}자)")
    rest = PRICE_SLOT.sub(lambda m: "" if m.group(3) != "num" else m.group(0), value)
    if "{{" in rest or "}}" in rest:
        raise Stop(f"{where}: 가격 자리 말고는 {{{{ }}}} 를 쓸 수 없습니다")
    for g, k, _ in PRICE_SLOT.findall(value):
        if (g, k) not in prices.values:
            raise Stop(f"{where}: 없는 가격입니다 ({g}.{k})")
    return value


def load_faq(name: str, prices: Prices) -> list:
    path = CONTENT / "faq" / f"{name}.json"
    rel = f"content/faq/{name}.json"
    if not path.exists():
        raise Stop(f"{rel}: 파일이 없습니다")
    data = read_json(path)
    if not isinstance(data, list) or not data:
        raise Stop(f"{rel}: 질문 목록 모양이 아니거나 비었습니다 (1개 이상)")
    if len(data) > FAQ_MAX_ITEMS:
        raise Stop(f"{rel}: 질문은 {FAQ_MAX_ITEMS}개까지입니다")
    out = []
    for n, it in enumerate(data, 1):
        where = f"{rel} {n}번째 질문"
        if not isinstance(it, dict):
            raise Stop(f"{where}: 모양이 아닙니다")
        search = it.get("search", False)
        if not isinstance(search, bool):
            raise Stop(f"{where}: search 는 true/false 여야 합니다")
        order = it.get("search_order")
        if order is not None and (isinstance(order, bool) or not isinstance(order, int) or not 0 <= order <= 99):
            raise Stop(f"{where}: search_order 는 0~99 숫자여야 합니다")
        out.append({
            "q": faq_text(it.get("q"), where + " 질문", FAQ_Q_MAX, prices, False, True),
            "a": faq_text(it.get("a"), where + " 답", FAQ_A_MAX, prices, True, True),
            "search": search and name != "index",          # 홈에는 검색용 묶음이 없다
            "search_q": faq_text(it.get("search_q"), where + " 검색용 질문", FAQ_Q_MAX, prices, False, False),
            "search_a": faq_text(it.get("search_a"), where + " 검색용 답", FAQ_A_MAX, prices, True, False),
            "order": order,
        })
    return out


def faq_html(text: str) -> str:
    """질문·답 글 → HTML. **굵게** → <b>, 줄바꿈 → <br> (빈 줄은 <br><br>)"""
    return inline(text).replace("\n", "<br>")


def faq_plain(text: str) -> str:
    """검색용 답을 따로 안 적었을 때: 화면 답에서 ** 와 줄바꿈을 뺀 글"""
    return re.sub(r"\s*\n+\s*", " ", text.replace("**", "")).strip()


def render_faq(items: list, home: bool) -> str:
    q_div = "<div class=\"faq-q\" onclick=\"this.parentElement.classList.toggle('open')\">"
    rows = []
    for i, it in enumerate(items):
        q = f'{q_div}<span>{faq_html(it["q"])}</span><span class="faq-arrow">▾</span></div>'
        a = f'<div class="faq-a">{faq_html(it["a"])}</div>'
        if home:     # 홈: 한 줄짜리, 나타나기 효과 d1·d2·d3 차례
            rows.append(f'      <div class="faq-item rv d{i % 3 + 1} open">{q}{a}</div>')
        else:
            rows += ['      <div class="faq-item open">', f"        {q}", f"        {a}", "      </div>"]
    return "".join(r + "\n" for r in rows)


def ld_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False).replace("</", "<\\/")


def render_faq_ld(items: list) -> str:
    chosen = [(it["order"] if it["order"] is not None else i, i, it) for i, it in enumerate(items) if it["search"]]
    if not chosen:
        return ""
    blocks = []
    for _, _, it in sorted(chosen, key=lambda x: (x[0], x[1])):
        q = it["search_q"] or it["q"].replace("**", "")
        a = re.sub(r"\s*\n+\s*", " ", it["search_a"]) if it["search_a"] else faq_plain(it["a"])
        blocks.append('    {\n      "@type": "Question",\n'
                      f'      "name": {ld_str(q)},\n'
                      '      "acceptedAnswer": {\n        "@type": "Answer",\n'
                      f'        "text": {ld_str(a)}\n'
                      '      }\n    }')
    return ('<script type="application/ld+json">\n{\n  "@context": "https://schema.org",\n  "@type": "FAQPage",\n'
            '  "mainEntity": [\n' + ",\n".join(blocks) + "\n  ]\n}\n</script>\n")


# ── 서비스 설명 글 ────────────────────────────────────

def load_services() -> dict:
    rel = "content/services.json"
    data = read_json(CONTENT / "services.json")
    if not isinstance(data, dict):
        raise Stop(f"{rel}: 묶음 모양이 아닙니다")
    out = {}
    for key in SERVICES:
        s = data.get(key)
        where = f"{rel} {key}"
        if not isinstance(s, dict):
            raise Stop(f"{where}: 없습니다")
        sym = s.get("symptoms")
        if not isinstance(sym, list) or not 1 <= len(sym) <= SVC_SYM_ITEMS:
            raise Stop(f"{where} 증상: 1~{SVC_SYM_ITEMS}줄이어야 합니다")
        intro = s.get("intro")
        if not isinstance(intro, str):
            raise Stop(f"{where} 소개 글: 글이 아닙니다")
        lines = [x.strip() for x in intro.replace("\r\n", "\n").strip().split("\n")]
        if not lines[0] or len(lines) > SVC_INTRO_LINES or any(not x for x in lines):
            raise Stop(f"{where} 소개 글: 1~{SVC_INTRO_LINES}줄, 빈 줄 없이 적어야 합니다")
        out[key] = {
            "name": one_line(s.get("name"), where + " 이름", SVC_NAME_MAX, True),
            "symptoms": [one_line(x, f"{where} 증상 {i}", SVC_SYM_MAX, True) for i, x in enumerate(sym, 1)],
            "price_note": one_line(s.get("price_note"), where + " 가격 설명", SVC_NOTE_MAX),
            "intro": [one_line(x, f"{where} 소개 글 {i}째 줄", SVC_INTRO_LINE_MAX, True) for i, x in enumerate(lines, 1)],
        }
    return out


def js_str(s: str) -> str:
    """자바스크립트 '…' 안에 넣을 글"""
    return (s.replace("\\", "\\\\").replace("'", "\\'").replace("<", "\\x3C")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def put_services(text: str, services: dict, label: str) -> str:
    def put(m):
        key, field = m.group(1), m.group(2)
        s = services.get(key)
        if s is None or field not in ("name", "symptoms", "price_note", "intro"):
            raise Stop(f"{label} 틀에 모르는 서비스 자리가 있습니다: {m.group(0)}")
        if field == "symptoms":
            return ",".join(f"'{js_str(x)}'" for x in s["symptoms"])
        if field == "intro":   # 맨 위 소개 글: 줄마다 <br class="nb">, **굵게** → <strong>
            return '<br class="nb">\n'.join("        " + re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc(x))
                                            for x in s["intro"])
        return js_str(s[field])

    return SVC_SLOT.sub(put, text)


# ── 가격 안내 문구 · 공지 띠 ──────────────────────────

def guide_line(guide: str) -> str:
    if not guide:
        return ""
    return ('    <p class="price-guide rv" style="max-width:640px;margin:16px auto 0;text-align:center;'
            f'font-size:15px;font-weight:700;color:var(--yel);line-height:1.7">{esc(guide)}</p>\n')


def load_notice() -> dict:
    rel = "content/notice.json"
    path = CONTENT / "notice.json"
    if not path.exists():
        return {"on": False, "message": "", "start": "", "end": ""}
    data = read_json(path)
    if not isinstance(data, dict):
        raise Stop(f"{rel}: 묶음 모양이 아닙니다")
    on = data.get("on", False)
    if not isinstance(on, bool):
        raise Stop(f"{rel}: on 은 true/false 여야 합니다")
    n = {"on": on,
         "message": one_line(data.get("message"), rel + " 문구", NOTICE_MAX, on),
         "start": date_or_empty(data.get("start"), rel + " 시작일"),
         "end": date_or_empty(data.get("end"), rel + " 끝나는 날")}
    if n["start"] and n["end"] and n["start"] > n["end"]:
        raise Stop(f"{rel}: 시작일({n['start']})이 끝나는 날({n['end']})보다 늦습니다")
    return n


NOTICE_START = "<!-- 공지 띠 — content/notice.json (관리 화면 '공지' 탭). 끄면 이 묶음째 빠진다 -->\n"
NOTICE_END = "<!-- /공지 띠 -->\n"
NOTICE_AFTER = "</header>\n</div>\n"     # 상단 고정 묶음(site-head)이 끝나는 곳. 18장 모두 한 번씩
NOTICE_OLD = re.compile(re.escape(NOTICE_START) + r".*?" + re.escape(NOTICE_END), re.S)


def notice_block(notice: dict, today: str) -> str:
    """켜져 있고 끝나는 날이 안 지났으면 띠 HTML. 아니면 빈 글."""
    if not notice["on"] or not notice["message"] or (notice["end"] and today > notice["end"]):
        return ""
    return (NOTICE_START +
            f'<div id="site-notice" data-start="{notice["start"]}" data-end="{notice["end"]}" '
            'style="background:var(--yel);color:var(--n900);border-bottom:1px solid rgba(16,35,63,.15)">\n'
            '  <p style="max-width:1100px;margin:0 auto;padding:10px 16px;font-size:14.5px;font-weight:700;'
            'line-height:1.55;text-align:center;word-break:keep-all">'
            '<span style="display:inline-block;margin-right:8px;padding:1px 8px;border-radius:6px;background:var(--n900);'
            'color:var(--yel);font-size:12.5px;vertical-align:1px">알림</span>'
            f'{esc(notice["message"])}</p>\n'
            '</div>\n'
            "<script>(function(){var n=document.getElementById('site-notice'),s=n.getAttribute('data-start'),"
            "e=n.getAttribute('data-end'),t=new Date(Date.now()+324e5).toISOString().slice(0,10);"
            "if((s&&t<s)||(e&&t>e))n.parentNode.removeChild(n);})();</script>\n"   # 한국 시간 오늘이 기간 밖이면 숨김
            + NOTICE_END)


def insert_notice(page: str, block: str, label: str) -> str:
    """지난번 띠 묶음을 빼고, 새 묶음을 머리(site-head) 바로 아래에 넣는다 (빈 글이면 빼기만)"""
    page = NOTICE_OLD.sub("", page)
    if page.count(NOTICE_AFTER) != 1:
        raise Stop(f"{label}: 공지 띠를 넣을 자리(머리 끝 </header></div>)를 하나로 찾지 못했습니다")
    return page.replace(NOTICE_AFTER, NOTICE_AFTER + block, 1)


# ── 페이지 만들기 ─────────────────────────────────────

def read_template(name: str) -> str:
    text = (SRC / f"{name}.html").read_text(encoding="utf-8-sig")   # BOM 이 붙어 저장돼도 괜찮게
    text = text.replace("\r\n", "\n")
    return re.sub(r"^<!--.*?-->\n", "", text, count=1, flags=re.S)  # 틀 맨 위 설명 주석은 빼고


def one_slot(page: str, slot: str, value: str, label: str) -> str:
    n = page.count(slot)
    if n != 1:
        raise Stop(f"{label} 에 {slot.strip()} 줄이 꼭 하나 있어야 합니다 (지금 {n}개)")
    return page.replace(slot, value)


def build(name: str, cases, data: dict) -> str:
    label = f"_tools/src/{name}.html"
    prices = data["prices"]
    page = read_template(name)
    faq = data["faq"][name]
    page = one_slot(page, FAQ_SLOT, render_faq(faq, name == "index"), label)
    if name != "index":
        page = one_slot(page, FAQ_LD_SLOT, render_faq_ld(faq), label)
    page = resolve_blocks(page, prices, label)
    page = text_runs(page, prices)
    page = fill_prices(page, prices, label)
    # 아래는 사장님 글이 가격 처리 뒤에 들어가게 (글 속 {{ }} 가 가격 자리로 읽히지 않게)
    page = put_services(page, data["services"], label)
    if GUIDE_SLOT in page:
        page = one_slot(page, GUIDE_SLOT, guide_line(prices.guide), label)
    if cases is not None:
        page = one_slot(page, CASES_SLOT, render_cases(cases), label)
    return insert_notice(page, data["notice_block"], label)


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


def load_all(today: str = None) -> dict:
    prices = load_prices()
    notice = load_notice()
    return {"prices": prices,
            "faq": {name: load_faq(name, prices) for name, _, _ in PAGES},
            "services": load_services(),
            "notice": notice,
            "notice_block": notice_block(notice, today or kst_today())}


def render_all(today: str = None) -> list:
    """[(라벨, 만들 파일 경로, 내용, 상태)] — 시험(tests)에서도 이 함수를 부른다. today 는 시험용(없으면 한국 오늘)."""
    data = load_all(today)
    out = []
    for name, rel, cases in PAGES:
        page = build(name, cases, data)
        out.append((rel, SITE / rel, page, check(page)))
    path = SITE / PRIVACY            # 손으로 쓰는 파일: 공지 띠 묶음만 넣고 뺀다
    page = insert_notice(path.read_text(encoding="utf-8"), data["notice_block"], PRIVACY)
    out.append((PRIVACY + " (공지 띠만)", path, page, check(page)))
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
