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

REGIONS = [
    {
        "slug": "gwangju", "name": "광주", "time": "30분 이내", "priority": "0.8",
        "lead": "사업장이 광주 북구에 있습니다. 시내 어디든 <em>30분 이내</em>에 도착합니다.",
        "sub": "북구·서구·남구·동구·광산구 전 지역, 상가·아파트·주택을 가리지 않습니다.",
        "areas": "북구 · 서구 · 남구 · 동구 · 광산구",
        "cases": [
            ("북구", "사업장이 있는 곳입니다. 가장 빨리 도착합니다"),
            ("서구 · 남구", "상무지구, 봉선동 등 아파트와 상가 작업이 많습니다"),
            ("동구 · 광산구", "오래된 주택과 신도시 아파트가 섞여 있어 작업이 다양합니다"),
        ],
        "trait": "구도심의 오래된 건물에서 문제가 많습니다. 배관 기울기(구배)가 나빠져 물이 잘 안 빠지거나, 오래된 관에서 누수가 생기는 경우입니다.",
    },
    {
        "slug": "yeosu", "name": "여수", "time": "30분~1시간", "priority": "0.7",
        "lead": "여수도 갑니다. <em>30분에서 1시간</em> 안에 도착합니다.",
        "sub": "아파트·주택·상가 모두 작업합니다. 아래는 실제로 다녀온 곳입니다.",
        "areas": "웅천동 · 문수동 · 여서동 등 여수 전 지역",
        "cases": [
            ("웅천동", "아파트 싱크대 막힘"),
            ("문수동", "주택 욕실 배수구 막힘"),
            ("여서동", "변기 막힘"),
        ],
        "trait": "오래된 건물에서 문제가 많습니다. 배관 기울기가 나빠지거나 누수가 생기는 경우입니다.",
    },
    {
        "slug": "suncheon", "name": "순천", "time": "30분~1시간", "priority": "0.7",
        "lead": "순천도 갑니다. <em>30분에서 1시간</em> 안에 도착합니다.",
        "sub": "식당 주방 배관부터 아파트 싱크대까지 작업합니다.",
        "areas": "연향동 · 조례동 · 신대지구 등 순천 전 지역",
        "cases": [
            ("연향동", "아파트 싱크대 막힘"),
            ("조례동", "식당 하수구 작업"),
            ("신대지구", "싱크대 막힘"),
        ],
        "trait": "신대지구 같은 신도시와 구도심이 섞여 있어 작업 성격이 갈립니다. 오래된 건물은 배관 기울기와 누수 문제가 많습니다.",
    },
    {
        "slug": "mokpo", "name": "목포", "time": "30분~1시간", "priority": "0.7",
        "lead": "목포도 갑니다. <em>30분에서 1시간</em> 안에 도착합니다.",
        "sub": "식당 하수구와 가정집 배관 모두 작업합니다.",
        "areas": "하당동 · 용해동 · 연산동 등 목포 전 지역",
        "cases": [
            ("하당동", "식당 하수구 작업"),
            ("용해동", "싱크대 막힘"),
            ("연산동", "변기 막힘"),
        ],
        "trait": "오래된 건물에서 문제가 많습니다. 배관 기울기가 나빠지거나 누수가 생기는 경우입니다.",
    },
    {
        "slug": "jeonju", "name": "전주", "time": "30분~1시간", "priority": "0.7",
        "lead": "전주도 갑니다. <em>30분에서 1시간</em> 안에 도착합니다.",
        "sub": "하수구 막힘 작업이 특히 많은 지역입니다.",
        "areas": "효자동 · 서신동 · 인후동 등 전주 전 지역",
        "cases": [
            ("효자동", "하수구 막힘 · 싱크대 막힘"),
            ("서신동", "아파트 하수구 작업"),
            ("인후동", "하수구 막힘"),
        ],
        "trait": "오래된 건물에서 문제가 많습니다. 배관 기울기가 나빠지거나 누수가 생기는 경우입니다.",
    },
]

# 손으로 쓴 페이지들. 사이트맵에만 넣는다.
HANDMADE = [("", "1.0"), ("toilet/", "0.9"), ("sink/", "0.9"), ("jet/", "0.9")]

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


def body_html(region: dict) -> str:
    cases = "\n".join(
        f'      <div class="pg-facts-row">\n'
        f'        <div class="pg-facts-k">{where}</div>\n'
        f'        <div class="pg-facts-v">{what}</div>\n'
        f'      </div>'
        for where, what in region["cases"])
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
    <div class="sec-ttl">{name}에서 실제로 한 작업</div></div>
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
      <a href="../index.html#services"><svg class="ic"><use href="#i-drain"/></svg> 하수구 막힘</a>
      <a href="../index.html#services"><svg class="ic"><use href="#i-wrench"/></svg> 배관 설비</a>
      <a href="../index.html#services"><svg class="ic"><use href="#i-faucet"/></svg> 수전 교체</a>
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
        <div class="pg-facts-v">24시간 연중무휴 · 저녁 8시 이후는 야간 요금 2만원 추가</div>
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
