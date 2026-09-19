"""
지역 페이지 생성기

실행:
    cd C:\\projects\\cheongnyeon-baegwan\\_tools
    python build_pages.py

이 폴더(`_tools`)는 이름이 밑줄로 시작해서 GitHub Pages가 웹에 올리지 않는다.
그러면서 git에는 들어가므로 백업되고 다른 컴퓨터에서도 받아 쓸 수 있다.

────────────────────────────────────────────────────────
지역 페이지는 서비스 페이지(/toilet/, /sink/, /jet/)와 역할이 다르다.

  서비스 페이지 : 증상·원인·작업 방법을 자세히 (긴 페이지, 손으로 작성)
  지역 페이지   : "여기도 갑니다"를 증명하는 짧은 페이지 (이 도구가 생성)

이렇게 나눈 이유:
지역 페이지에 작업 방법까지 넣으면 페이지 내용이 거의 같아진다.
그러면 검색엔진이 관문 페이지(doorway page)로 보고 저품질 처리한다.
지역별로 **정말 다른 것**(시공 사례, 동네 이름, 출동 시간)만 넣고
공통 내용은 서비스 페이지로 링크를 보낸다.

내용은 전부 사장님 답변(질문지 40~45번)에서 가져왔다.
────────────────────────────────────────────────────────

새 지역을 추가하려면:
  1. 아래 REGIONS 목록에 덩어리를 하나 더 넣는다
  2. 이 파일을 실행한다
  3. sitemap.xml 도 같이 갱신된다

⚠️ 지역 페이지 내용을 고칠 때는 만들어진 HTML이 아니라 이 파일을 고친다.
   이 도구를 돌리면 기존 페이지도 다시 만들어져 덮어쓰기 때문이다.
"""

import json
import pathlib
import re
import xml.etree.ElementTree as ET

SITE = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = pathlib.Path(__file__).with_name("page-template.html")
BASE = "https://xn--hc0bug19yo4ksghrpb480c.com"
TODAY = "2026-08-15"

# 블로그 글 주소 앞부분. 사례마다 실제 작업 사진을 볼 수 있게 링크를 단다.
B = "https://blog.naver.com/tturobro/"

REGIONS = [
    {
        "slug": "gwangju", "name": "광주", "time": "30분 이내", "priority": "0.8",
        "lead": "광주 전 지역 <em>30분 이내</em>에 도착합니다.",
        "sub": "북구·서구·남구·동구·광산구 어디든 갑니다. 아래는 실제로 다녀온 곳입니다.",
        "areas": "북구 · 서구 · 남구 · 동구 · 광산구",
        "cases": [
            ("북구 일곡동", "아파트 화장실 배수구 역류 — 머리카락이 대량으로 쌓여 있었습니다", B + "224357415004"),
            ("북구 각화동", "아파트 싱크대 역류 — 8년 묵은 기름이 배관을 막고 있었습니다", B + "224314712946"),
            ("서구 상무지구", "식당 하수구 막힘 — 그리스트랩 기름을 마감시간에 맞춰 청소했습니다", B + "224363058471"),
            ("남구 방림동", "아파트 변기 막힘 — 어린이가 넣은 칫솔에 머리카락이 감겨 있었습니다", B + "224334280966"),
            ("동구 계림동", "아파트 싱크대 수전 교체 — 물이 안 나오던 문제를 해결했습니다", B + "224363064225"),
            ("광산구 신가동", "아파트 세탁실 배수 막힘 — 요구르트 병이 배관 끝에 걸려 있었습니다", B + "224334331578"),
            ("광산구 도산동", "단독주택 배관공사 — 변기가 안 내려가 갔는데, 정화조로 나가는 배관이 땅속에서 무너져 있었습니다. 8시간 걸렸습니다",
             "", [("pipe-dosan-01", "작업 전", "변기 물이 내려가지 않았습니다"),
                  ("pipe-dosan-11", "고친 자리", "땅속에서 무너진 배관을 보수했습니다")]),
            ("광산구 첨단", "다세대빌라 배관 청소 — 싱크대 기름이 쌓여 막혔고, P트랩이 아랫층 천장에 있어 천장을 열고 작업했습니다",
             "", [("drain-cheomdan-01", "작업 전", "바닥 배수구가 찌꺼기로 꽉 막혀 있었습니다"),
                  ("drain-cheomdan-06", "작업 후", "물길이 다시 열렸습니다")]),
            ("서구 상무지구", "식당 주방 트렌치 막힘 — 기름때로 꽉 차 있었습니다. 한 시간 만에 끝냈습니다",
             "", [("drain-sangmu-01", "작업 전", "트렌치가 기름때로 덮여 있었습니다"),
                  ("drain-sangmu-10", "작업 후", "기름때를 걷어낸 트렌치입니다")]),
        ],
        "trait": "구도심의 오래된 건물에서 문제가 많습니다. 배관 기울기(구배)가 나빠져 물이 잘 안 빠지거나, 오래된 관에서 누수가 생기는 경우입니다.",
    },
    {
        "slug": "gwangyang", "name": "광양", "time": "1시간 내외", "priority": "0.7",
        "lead": "광양도 갑니다. <em>1시간 내외</em>로 도착합니다.",
        "sub": "아파트부터 관공서까지 작업합니다. 아래는 실제로 다녀온 곳입니다.",
        "areas": "용강리 · 중동 등 광양 전 지역",
        "cases": [
            ("용강리", "아파트 변기 막힘 — 아이가 넣은 아이스크림 팩을 변기 탈거로 찾았습니다", B + "224369838544"),
            ("중동", "아파트 싱크대 역류 — 청소 후 배관 관리법까지 알려드렸습니다", B + "224369811975"),
            ("관공서", "남자화장실 변기 3개가 동시에 막혔는데, 나무뿌리가 원인이었습니다", B + "224300004422"),
        ],
        "trait": "아파트 단지와 관공서·상가가 섞여 있어 작업 규모가 다양합니다. 나무뿌리가 배관으로 파고드는 경우처럼 원인을 찾아야 풀리는 현장이 많습니다.",
    },
    {
        "slug": "yeosu", "name": "여수", "time": "30분~1시간", "priority": "0.7",
        "lead": "여수도 갑니다. <em>30분에서 1시간</em> 안에 도착합니다.",
        "sub": "아파트·주택·상가 모두 작업합니다.",
        "areas": "웅천동 · 문수동 · 여서동 등 여수 전 지역",
        "cases": [
            ("웅천동", "아파트 싱크대 막힘", None),
            ("문수동", "주택 욕실 배수구 막힘", None),
            ("여서동", "변기 막힘", None),
        ],
        "trait": "오래된 건물에서 문제가 많습니다. 배관 기울기가 나빠지거나 누수가 생기는 경우입니다.",
    },
    {
        "slug": "suncheon", "name": "순천", "time": "30분~1시간", "priority": "0.7",
        "lead": "순천도 갑니다. <em>30분에서 1시간</em> 안에 도착합니다.",
        "sub": "식당 주방 배관부터 아파트 싱크대까지 작업합니다.",
        "areas": "연향동 · 조례동 · 신대지구 등 순천 전 지역",
        "cases": [
            ("연향동", "아파트 싱크대 막힘", None),
            ("조례동", "식당 하수구 작업", None),
            ("신대지구", "싱크대 막힘", None),
        ],
        "trait": "신대지구 같은 신도시와 구도심이 섞여 있어 작업 성격이 갈립니다. 오래된 건물은 배관 기울기와 누수 문제가 많습니다.",
    },
    {
        "slug": "mokpo", "name": "목포", "time": "30분~1시간", "priority": "0.7",
        "lead": "목포도 갑니다. <em>30분에서 1시간</em> 안에 도착합니다.",
        "sub": "식당 주방과 가정집 배관 모두 작업합니다. 아래는 실제로 다녀온 곳입니다.",
        "areas": "하당 · 용해동 등 목포 전 지역",
        "cases": [
            ("하당", "아파트 해바라기 수전 교체 — 쓰기 불편하던 것을 일반 샤워수전으로 바꿔드렸습니다", B + "224353347039"),
            ("용해동", "빌라 싱크대 역류 — 걸레받이가 변형될 만큼 진행된 상태였습니다", B + "224310468564"),
            ("시내 상가", "햄버거집 주방 배수구 역류 — 기름으로 가득한 배관을 청소했습니다", B + "224339640810"),
        ],
        "trait": "식당이 많은 상권이라 주방 배관 작업이 잦습니다. 기름이 쌓여 역류하는 경우가 대부분입니다.",
    },
    {
        "slug": "jeonju", "name": "전주", "time": "30분~1시간", "priority": "0.7",
        "lead": "전주도 갑니다. <em>30분에서 1시간</em> 안에 도착합니다.",
        "sub": "하수구 막힘 작업이 특히 많은 지역입니다.",
        "areas": "효자동 · 서신동 · 인후동 등 전주 전 지역",
        "cases": [
            ("효자동", "하수구 막힘 · 싱크대 막힘", None),
            ("서신동", "아파트 하수구 작업", None),
            ("인후동", "하수구 막힘", None),
        ],
        "trait": "오래된 건물에서 문제가 많습니다. 배관 기울기가 나빠지거나 누수가 생기는 경우입니다.",
    },
    {
        "slug": "damyang", "name": "담양", "time": "40분 내외", "priority": "0.6",
        "lead": "담양도 갑니다. <em>40분 내외</em>로 도착합니다.",
        "sub": "집 안 배관뿐 아니라 농수로처럼 굵은 관도 작업합니다.",
        "areas": "담양읍을 비롯한 담양 전 지역",
        "cases": [
            ("농수로", "고압세척 — 배관 안에서 비료포대가 나왔습니다", B + "224310453744"),
        ],
        "trait": "농지와 주거지가 함께 있어 일반 가정 배관 외에 농수로처럼 굵은 관을 다루는 일도 있습니다. 이런 곳은 고압세척 장비가 있어야 합니다.",
    },
    {
        "slug": "hwasun", "name": "화순", "time": "40분 내외", "priority": "0.6",
        "lead": "화순도 갑니다. <em>40분 내외</em>로 도착합니다.",
        "sub": "이른 아침이든 늦은 밤이든 연락 주시면 갑니다.",
        "areas": "화순읍을 비롯한 화순 전 지역",
        "cases": [
            ("화순", "싱크대 역류 — 아침 7시에 긴급 출동했고, 잡채가 배관을 막고 있었습니다", B + "224301717737"),
        ],
        "trait": "광주에서 가까워 이른 아침이나 밤에도 출동합니다. 음식물이 그대로 배관에 들어가 막히는 경우가 많습니다.",
    },
    {
        "slug": "muan", "name": "무안", "time": "1시간 내외", "priority": "0.6",
        "lead": "무안도 갑니다. <em>1시간 내외</em>로 도착합니다.",
        "sub": "원룸·주택 작업을 주로 다녀왔습니다.",
        "areas": "청계읍을 비롯한 무안 전 지역",
        "cases": [
            ("청계읍", "원룸 변기 막힘 — 변기를 탈거해 진짜 원인을 찾았습니다", B + "224316329430"),
            ("청계면", "원룸 빌라 변기 막힘 — 휴지를 한꺼번에 많이 내려보내 변기 끝에 꽉 껴 있었습니다. 고객님 동의를 받고 변기를 탈거해 꺼냈고 30분 걸렸습니다",
             "", [("toilet-muan-01", "작업 전", "변기에 물이 가득 차 내려가지 않았습니다"),
                  ("toilet-muan-04", "원인", "변기 끝에 휴지가 꽉 껴 있었습니다")]),
        ],
        "trait": "원룸과 소형 주택이 많습니다. 세대마다 배관이 짧고 좁아 이물질 하나에도 쉽게 막힙니다.",
    },
]

# 손으로 쓴 페이지들. 사이트맵에만 넣는다.
HANDMADE = [("", "1.0"), ("toilet/", "0.9"), ("sink/", "0.9"), ("drain/", "0.9"),
            ("jet/", "0.9"), ("faucet/", "0.9"), ("leak/", "0.9"), ("pipe/", "0.9")]

# 모든 지역에서 공통으로 나온 이야기 (사장님 답변 40~44번)
INTERIOR = (
    "<strong>인테리어 공사를 하고 나서 막히는 경우가 유독 많습니다.</strong> "
    "공사하는 분들이 시멘트나 방수액을 배수구에 흘려보내는 일이 있는데, "
    "그것이 배관 안에서 굳으면 뚫는 것으로는 해결되지 않습니다. "
    "공사 뒤에 물이 느려졌다면 그 때문일 가능성이 큽니다."
)


def service_ld(region: dict) -> str:
    data = {
        "@context": "https://schema.org", "@type": "Service",
        "serviceType": "배관 막힘 · 하수구 · 누수 출동 수리",
        "name": f"{region['name']} 배관·하수구 막힘 출동",
        "description": f"{region['name']} 전 지역 {region['time']} 출동. 변기·싱크대·하수구 막힘, 고압세척, 누수탐지.",
        "provider": {
            "@type": "Plumber", "name": "청년배관", "telephone": "+82-10-6872-8284",
            "url": f"{BASE}/",
            "address": {"@type": "PostalAddress", "streetAddress": "동운로201번길 20",
                        "addressLocality": "북구", "addressRegion": "전남광주통합특별시",
                        "postalCode": "61258", "addressCountry": "KR"}},
        "areaServed": {"@type": "AdministrativeArea", "name": region["name"]},
    }
    return ('<script type="application/ld+json">\n'
            + json.dumps(data, ensure_ascii=False, indent=2) + "\n</script>")


def shots_html(shots) -> str:
    """사례에 붙는 전/후 사진. (파일이름, 라벨, 한 줄 설명) 목록을 받는다."""
    if not shots:
        return ""
    figs = []
    for name, tag, cap in shots:
        t = f'<span class="tag tag-{"a" if tag in ("작업 후", "고친 자리", "원인") else "b"}">{tag}</span>' if tag else ""
        figs.append(f'          <figure>\n'
                    f'            <img src="../photos/{name}.webp" alt="{cap}" loading="lazy">\n'
                    f'            <figcaption>{t}{cap}</figcaption>\n'
                    f'          </figure>')
    return '\n        <div class="pg-shots">\n' + "\n".join(figs) + '\n        </div>'


def body_html(region: dict) -> str:
    rows = []
    for case in region["cases"]:
        where, what, link = case[0], case[1], case[2]
        shots = case[3] if len(case) > 3 else None
        # 블로그 글이 있으면 링크만 단다. 글을 옮겨 적으면 같은 내용이 두 곳에 있는 것으로
        # 취급돼 홈페이지 쪽이 검색에서 밀린다. 링크는 그런 문제가 없고 사진도 보여줄 수 있다.
        more = (f'<br><a class="pg-case-link" href="{link}" target="_blank" rel="noopener">사진 보기 ›</a>'
                if link else "")
        rows.append(f'      <div class="pg-facts-row">\n'
                    f'        <div class="pg-facts-k">{where}</div>\n'
                    f'        <div class="pg-facts-v">{what}{more}{shots_html(shots)}</div>\n'
                    f'      </div>')
    cases = "\n".join(rows)
    name = region["name"]
    return f'''<!-- 상단 -->
<section class="pg-hero">
  <div class="inner">
    <nav class="pg-crumb" aria-label="현재 위치">
      <a href="../index.html">홈</a> <span>›</span> <span>{name}</span>
    </nav>
    <div class="pg-hero-body">
      <h1>{name} 하수구·배관 막힘<br>{region["lead"]}</h1>
      <p class="pg-hero-sub">{region["sub"]}</p>
      <div class="pg-hero-facts">
        <span class="pg-fact">출동 <em>{region["time"]}</em></span>
        <span class="pg-fact">24시간 <em>연중무휴</em></span>
        <span class="pg-fact">7년 <em>4,000건</em></span>
      </div>
    </div>
  </div>
</section>

<!-- 실제 작업 -->
<section class="sec">
  <div class="inner">
    <div class="rv"><div class="sec-tag">Works</div>
    <div class="sec-ttl">{name}에 다녀온 곳</div></div>
    <div class="pg-facts rv">
{cases}
    </div>
    <div class="pg-note rv" style="margin-top:18px">
      <strong>{region["areas"]}</strong> 어디든 갑니다.
      아파트·주택·상가·식당 모두 작업합니다.
    </div>
  </div>
</section>

<!-- 이 지역 특성 -->
<section class="sec" style="background:var(--paper)">
  <div class="inner">
    <div class="rv"><div class="sec-tag">Local</div>
    <div class="sec-ttl">{name}에서 자주 보는 문제</div></div>
    <div class="pg-note rv">{region["trait"]}</div>
    <div class="pg-note rv d1">{INTERIOR}</div>
  </div>
</section>

<!-- 어떤 작업 -->
<section class="sec">
  <div class="inner">
    <div class="rv"><div class="sec-tag">Service</div>
    <div class="sec-ttl">어떤 작업을 하나요</div></div>
    <p class="pg-note rv" style="margin-bottom:20px">
      증상별로 원인과 작업 방법을 자세히 적어두었습니다. 눌러서 확인해 주세요.
    </p>
    <div class="pg-more rv">
      <a href="../toilet/"><svg class="ic"><use href="#i-toilet"/></svg> 변기 막힘</a>
      <a href="../sink/"><svg class="ic"><use href="#i-sink"/></svg> 싱크대 막힘</a>
      <a href="../jet/"><svg class="ic"><use href="#i-jet"/></svg> 고압 세척</a>
      <a href="../drain/"><svg class="ic"><use href="#i-drain"/></svg> 하수구 막힘</a>
      <a href="../pipe/"><svg class="ic"><use href="#i-wrench"/></svg> 배관 설비</a>
      <a href="../faucet/"><svg class="ic"><use href="#i-faucet"/></svg> 수전 교체</a>
    </div>
  </div>
</section>

<!-- 안내 -->
<section class="sec" style="background:var(--paper)">
  <div class="inner">
    <div class="rv"><div class="sec-tag">Info</div>
    <div class="sec-ttl">{name} 출동 안내</div></div>
    <div class="pg-facts rv">
      <div class="pg-facts-row">
        <div class="pg-facts-k">출동 시간</div>
        <div class="pg-facts-v"><em>{region["time"]}</em></div>
      </div>
      <div class="pg-facts-row">
        <div class="pg-facts-k">운영 시간</div>
        <div class="pg-facts-v">24시간 연중무휴 · 야간 추가요금 없음</div>
      </div>
      <div class="pg-facts-row">
        <div class="pg-facts-k">출장비</div>
        <div class="pg-facts-v">작업을 진행하시면 <em>작업비에 포함</em>됩니다</div>
      </div>
      <div class="pg-facts-row">
        <div class="pg-facts-k">결제</div>
        <div class="pg-facts-v">카드 · 계좌이체 · 간편결제 / 세금계산서 · 현금영수증 발행 가능</div>
      </div>
      <div class="pg-facts-row">
        <div class="pg-facts-k">보증</div>
        <div class="pg-facts-v">배관 막힘 <em>1년</em> · 기름을 많이 쓰거나 배관 기울기가 좋지 않은 곳은 <em>6개월</em></div>
      </div>
      <div class="pg-facts-row">
        <div class="pg-facts-k">정화조</div>
        <div class="pg-facts-v"><em>설치만</em> 합니다. 정화조 <em>청소는 하지 않습니다.</em></div>
      </div>
    </div>
  </div>
</section>

'''


def build(region: dict, template: str) -> str:
    slug, name = region["slug"], region["name"]
    others = [r for r in REGIONS if r["slug"] != slug][:4]
    more = "\n".join(
        f'      <a href="../{r["slug"]}/"><svg class="ic"><use href="#i-drain"/></svg> {r["name"]}</a>'
        for r in others)

    filled = {
        "COMMENT": f"{name} 지역 페이지 — _tools/build_pages.py 가 만든 파일입니다. 직접 고치지 마세요",
        "TITLE": f"{name} 하수구·배관 막힘 | {region['time']} 출동 | 청년배관",
        "DESCRIPTION": f"{name} 전 지역 {region['time']} 출동. 변기·싱크대·하수구 막힘, 고압세척, 누수탐지. {region['areas']}에서 실제 작업한 사례를 확인하세요.",
        "OG_TITLE": f"{name} 하수구·배관 막힘 | {region['time']} 출동",
        "OG_DESC": f"{region['areas']}에서 실제로 작업한 사례를 확인하세요.",
        "URL": f"{BASE}/{slug}/",
        "JSONLD": service_ld(region),
        "SLUG": slug,
        "CTA_H2": f"{name} 어디든, <em>지금 바로</em>",
        "CTA_P": f"{region['time']} 안에 도착합니다. 24시간 연중무휴입니다.",
        "MORE_TITLE": "다른 지역도 갑니다",
        "MORE_LINKS": more,
    }
    page = template
    for key, value in filled.items():
        page = page.replace("{{" + key + "}}", value)
    return page.replace("<!--본문-->\n", body_html(region))


def write_sitemap() -> None:
    rows = []
    for path, priority in HANDMADE + [(r["slug"] + "/", r["priority"]) for r in REGIONS]:
        rows.append(
            f"  <url>\n    <loc>{BASE}/{path}</loc>\n    <lastmod>{TODAY}</lastmod>\n"
            f"    <changefreq>monthly</changefreq>\n    <priority>{priority}</priority>\n  </url>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(rows) + "\n</urlset>\n")
    ET.fromstring(xml)
    (SITE / "sitemap.xml").write_text(xml, encoding="utf-8")
    print(f"\nsitemap.xml · 주소 {len(rows)}개")


def main() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    template = re.sub(r"^<!--.*?-->\n", "", template, count=1, flags=re.S)   # 틀 파일 설명 주석 제거

    for region in REGIONS:
        page = build(region, template)
        out = SITE / region["slug"]
        out.mkdir(exist_ok=True)
        (out / "index.html").write_text(page, encoding="utf-8")

        left = re.findall(r"\{\{(\w+)\}\}", page)
        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
            json.loads(block)
        bad = [t for t in ("div", "section", "nav", "footer", "header", "html", "body")
               if len(re.findall(f"<{t}[ >]", page)) != len(re.findall(f"</{t}>", page))]
        note = "정상" if not bad and not left else f"확인필요 {bad}{left}"
        print(f"  /{region['slug']}/  {page.count(chr(10))+1}줄  {note}")

    write_sitemap()


if __name__ == "__main__":
    main()
