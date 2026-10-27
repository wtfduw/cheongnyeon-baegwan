"""
새 사진 줄이기 — 관리 화면으로 올린 원본 사진을 홈페이지용 WebP 로 바꾼다

실행:
    cd C:\\projects\\cheongnyeon-baegwan\\_tools
    python process_photos.py            먼저 이것. 무엇을 바꿀지 보여 주기만 하고 파일은 안 쓴다
    python process_photos.py --write    사진을 바꾸고, 사례 파일의 사진 주소도 새 파일로 고친다

GitHub 에서는 .github/workflows/site.yml 이 build_content.py 보다 먼저 --write 로 돌린다.

────────────────────────────────────────────────────────
사장님이 관리 화면(구글 Apps Script)에서 사례에 사진을 올리면
  브라우저가 긴 변 1600px JPEG 로 먼저 줄여 _uploads/ 폴더에 커밋하고,
  content/cases/<페이지>.json 에는 '/_uploads/파일이름' 으로 적힌다.
  (_uploads 는 이름이 밑줄로 시작해서 홈페이지 주소로는 열리지 않는다)

이 파일이 하는 일 — 순서를 바꾸지 않는다
  1. 사진 방향 바로 세우기 (ImageOps.exif_transpose)
     2026-09-21 사진 정보를 먼저 지웠다가 세로 사진 40장 중 9장이 누운 적이 있다. 그래서 방향이 맨 먼저다.
  2. 긴 변을 1200px 로 줄이기 (이미 작으면 그대로)
  3. WebP 품질 80 으로 photos/<페이지>-<날짜>-<번호>.webp 에 저장
     예) 변기 페이지, 2026-10-27 사례의 첫 사진 → photos/toilet-20261027-01.webp
         날짜가 없는 사례는 photos/toilet-case-01.webp. 번호는 이미 있는 파일 다음 번호부터
  4. content/cases/<페이지>.json 의 '/_uploads/…' 주소를 새 파일 주소('/photos/…')로 바꾸기
  5. _uploads/ 의 원본 지우기 (GitHub 커밋 기록에는 남는다)

위치정보(GPS)는 신경 쓰지 않기로 했다(2026-10-27 사용자 결정).
WebP 로 다시 저장할 때 사진 정보(EXIF)는 옮기지 않는다. 색 정보(ICC)만 옮긴다.

멈추는 경우 (아무 파일도 쓰지 않는다)
  - json 에 적힌 올린 사진 파일이 _uploads/ 에 없을 때
  - 읽을 수 없는 사진 형식일 때 (아이폰 HEIC 등 → JPG 로 바꿔 올린다)
────────────────────────────────────────────────────────
"""

import io
import json
import pathlib
import re
import sys

from PIL import Image, ImageOps, UnidentifiedImageError

SITE = pathlib.Path(__file__).resolve().parent.parent
CASES = SITE / "content" / "cases"
UPLOADS = "_uploads/"
PHOTOS = SITE / "photos"
LONG = 1200       # 긴 변 픽셀
QUALITY = 80      # WebP 품질


class Stop(Exception):
    pass


def case_key(case: dict) -> str:
    """사진 이름 가운데 부분: 사례 날짜(20261027) 또는 'case'."""
    day = str(case.get("date") or "").strip()[:10]
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", day)
    return "".join(m.groups()) if m else "case"


def next_name(prefix: str, taken: set) -> str:
    used = [int(m.group(1)) for p in taken if (m := re.fullmatch(re.escape(prefix) + r"-(\d+)\.webp", p))]
    return f"{prefix}-{max(used, default=0) + 1:02d}.webp"


def shrink(src: pathlib.Path):
    """원본 → (WebP 바이트, 원본 크기, 방향 값, 새 크기)"""
    try:
        with Image.open(src) as im:
            im.load()
            orientation = im.getexif().get(0x0112, 1)
            before = im.size
            icc = im.info.get("icc_profile")
            im = ImageOps.exif_transpose(im)              # 1. 방향 먼저
            im.thumbnail((LONG, LONG), Image.Resampling.LANCZOS)   # 2. 긴 변 1200
            alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
            want = "RGBA" if alpha else "RGB"
            if im.mode != want:
                im = im.convert(want)
            buf = io.BytesIO()
            extra = {"icc_profile": icc} if icc else {}
            im.save(buf, "WEBP", quality=QUALITY, method=6, **extra)   # 3. WebP 80
            return buf.getvalue(), before, orientation, im.size
    except UnidentifiedImageError:
        raise Stop(f"{src.name}: 읽을 수 없는 사진 형식입니다 (아이폰 HEIC 등). JPG 로 바꿔 다시 올려 주세요")


def find_uploads():
    """[(json 경로, 페이지, 사례 dict, 사진 dict, 적힌 주소)]"""
    found = []
    for yml in sorted(CASES.glob("*.json")):
        try:
            data = json.loads(yml.read_text(encoding="utf-8")) or []
        except ValueError as e:
            raise Stop(f"{yml.name}: json 모양이 깨졌습니다 ({e})")
        if isinstance(data, dict):
            data = data.get("cases") or []
        for case in data if isinstance(data, list) else []:
            for photo in (case.get("photos") or []) if isinstance(case, dict) else []:
                if not isinstance(photo, dict):
                    continue
                value = str(photo.get("file") or "")
                if value.lstrip("/").startswith(UPLOADS):
                    found.append((yml, yml.stem, case, photo, value))
    return found


def dump_json(data) -> str:
    """관리 화면(Apps Script)의 JSON.stringify(data, null, 2) 와 같은 모양 + 줄바꿈 하나 (LF).
    같은 모양으로 쓰므로 사진 주소 말고는 한 글자도 바뀌지 않는다."""
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def replace_in_json(js: pathlib.Path, mapping: dict) -> str:
    """사례 json 에서 올린 사진 주소만 새 주소로 바꾼다. 다른 칸은 손대지 않는다."""
    data = json.loads(js.read_text(encoding="utf-8")) or []
    cases = (data.get("cases") or []) if isinstance(data, dict) else data
    for case in cases:
        for photo in case.get("photos") or []:
            value = photo.get("file")
            if value in mapping:
                photo["file"] = mapping[value]
            # 바꾼 뒤 확인: 남은 올린 사진 주소가 없어야 한다
            if str(photo.get("file") or "").lstrip("/").startswith(UPLOADS):
                raise Stop(f"{js.name}: 사진 주소를 바꾸지 못했습니다 ({photo.get('file')})")
    return dump_json(data)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    write = "--write" in sys.argv[1:]
    try:
        items = find_uploads()
        taken = {p.name for p in PHOTOS.glob("*.webp")}
        plan = {}          # 원본 경로(사이트 기준) → (새 파일 이름, webp 바이트, 설명)
        per_yml = {}       # json → {적힌 주소: 새 주소}
        for yml, page, case, photo, value in items:
            rel = value.lstrip("/")
            if rel not in plan:
                src = SITE / rel
                if not src.is_file():
                    raise Stop(f"{yml.name}: 올린 사진이 없습니다 ({value})")
                data, before, orient, after = shrink(src)
                name = next_name(f"{page}-{case_key(case)}", taken)
                taken.add(name)
                plan[rel] = (name, data, f"{before[0]}×{before[1]} 방향{orient} → {after[0]}×{after[1]}, {len(data) // 1024}KB")
            per_yml.setdefault(yml, {})[value] = "/photos/" + plan[rel][0]
        new_texts = {yml: replace_in_json(yml, mapping) for yml, mapping in per_yml.items()}
    except Stop as e:
        print(f"멈춤: {e}\n아무 파일도 쓰지 않았습니다.")
        sys.exit(2)

    referenced = set(plan)
    loose = sorted(p.relative_to(SITE).as_posix() for p in (SITE / UPLOADS).glob("*")
                   if p.is_file() and not p.name.startswith(".") and p.relative_to(SITE).as_posix() not in referenced) if (SITE / UPLOADS).is_dir() else []
    if not plan:
        print("줄일 새 사진이 없습니다.")
        if loose:
            print(f"(사례에 쓰이지 않은 올린 파일 {len(loose)}개는 그대로 둡니다: {', '.join(loose[:5])}{' …' if len(loose) > 5 else ''})")
        return
    for rel, (name, _, note) in plan.items():
        print(f"  {rel} → photos/{name}  ({note})")
    for yml in new_texts:
        print(f"  주소 고침: content/cases/{yml.name}")
    if not write:
        print(f"\n새 사진 {len(plan)}장. 아직 아무 파일도 쓰지 않았습니다. 맞으면: python process_photos.py --write")
        sys.exit(1)
    for rel, (name, data, _) in plan.items():
        (PHOTOS / name).write_bytes(data)
    for yml, text in new_texts.items():
        yml.write_bytes(text.encode("utf-8"))   # LF 그대로 (관리 화면이 쓰는 모양과 같게)
    for rel in plan:
        (SITE / rel).unlink()
    print(f"\n새 사진 {len(plan)}장을 photos/ 에 썼고, 원본은 _uploads/ 에서 지웠습니다.")


if __name__ == "__main__":
    main()
