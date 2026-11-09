"""조대부고 연수용 강의 슬라이드·강의 원고 PDF를 만든다.

- 강의 슬라이드 = [1부] 연수 앞부분 슬라이드 PDF(1~42쪽, 쪽 번호만 n/51로) + [2부] part2_slides.html(1부와 같은 디자인)
- 강의 원고   = 표지 + 1부 원고(part1_lecture.html) + 2부 LINKFORGE 원고

사용법: python build_materials.py <1부 슬라이드 PDF>
필요: pip install pypdf qrcode, node + playwright, Pretendard 글꼴 설치
"""
import base64
import io
import re
import sys
from pathlib import Path

import qrcode
import qrcode.image.svg
from pypdf import PdfReader, PdfWriter, Transformation
import os
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
SITE = "https://math94hj-coder.github.io/26bugo/"
SHORT = "부고.짱.com"
GEM = "https://p.oin2.kr/gj-gem"
TRAINING = "2026 AI·디지털 기반 교육혁신 거점학교 교원연수_조대부고"
WHEN = "2026. 11. 4.(수) 15:30"
WHERE = "조선대학교부속고등학교 3층 아키드실"
WHO = "조선대학교부속중학교 수학 교사 김효진"
INTRO_PAGES = 42  # 43쪽(감사합니다)은 2부 뒤 마무리 슬라이드로 대신한다


def qr_svg(url, size):
    buf = io.BytesIO()
    qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, border=1).save(buf)
    svg = re.sub(r"<\?xml[^>]*\?>", "", buf.getvalue().decode()).strip()
    return re.sub(r'width="[^"]*" height="[^"]*"', f'width="{size}" height="{size}"', svg, count=1)


class Doc:
    def __init__(self, s): self.s = s
    def rep(self, a, b, count=1):
        assert a in self.s, a[:90]
        self.s = self.s.replace(a, b, count)


def local_fonts(d):
    # Pretendard는 설치된 글꼴을 쓴다 (CDN 없이도 같은 결과)
    d.s = re.sub(r'<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard[^>]*>\n', "", d.s)


# ---------------- 2부 슬라이드 (1부와 같은 광주아이온 디자인) ----------------
def data_uri(path):
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def build_slides_html():
    s = (HERE / "part2_slides.html").read_text(encoding="utf-8")
    s = (s.replace("{{STICKER}}", data_uri(HERE / "assets" / "aion_sticker.png"))
          .replace("{{ROBOT}}", data_uri(HERE / "assets" / "robot.png"))
          .replace("{{QR_SITE}}", qr_svg(SITE, 230)).replace("{{QR_SMALL}}", qr_svg(SITE, 110)))
    assert "{{" not in s
    return s


# 1부 슬라이드마다 흰 본문 판의 오른쪽·아래 끝(px, 1440×810 기준). 쪽 번호 덮개가 판 밖으로 나가지 않게
PANEL_EDGE = {1: (1412, 781), 2: (1418, 780), 3: (1418, 780), 4: (1418, 780), 5: (1418, 780), 6: (1414, 781),
              12: (1412, 770), 34: (1403, 781), 35: (1403, 781), 36: (1403, 781)}


def relabel_html(n_pages, total):
    """1부 슬라이드의 'n/43페이지'를 'n/전체페이지'로 덮어쓸 투명 페이지들"""
    pages = []
    for i in range(1, n_pages + 1):
        right, bottom = PANEL_EDGE.get(i, (1412, 774))
        right, bottom = min(right, 1412), min(bottom, 781)
        top = 744
        pages.append(f'<section><div class="lb" style="left:{right - 158}px;top:{top}px;height:{bottom - top}px;'
                     f'line-height:{bottom - top}px">{i}/{total}페이지</div></section>')
    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
@page {{ size: 1440px 810px; margin: 0; }} * {{ margin: 0; padding: 0; }}
section {{ width: 1440px; height: 810px; position: relative; page-break-after: always; }}
section:last-child {{ page-break-after: auto; }}
.lb {{ position: absolute; width: 158px; background: white; text-align: right; padding-right: 8px;
      font: 400 24px 'Pretendard', sans-serif; color: #111; }}
</style></head><body>{"".join(pages)}</body></html>"""


# ---------------- 강의 원고 ----------------
def build_lecture_html():
    d = Doc((HERE / "lecture_src_original.html").read_text(encoding="utf-8"))
    local_fonts(d)
    # 표지
    d.rep('<div class="runhead"><span>2026학년도 AI중점학교 교원역량 강화 연수</span><span>강의 원고</span></div>',
          f'<div class="runhead"><span>{TRAINING}</span><span>강의 원고</span></div>')
    d.rep('<span class="badge">생성형 AI 수업 설계 · 코딩 몰라도 따라갈 수 있어요</span>',
          '<span class="badge">생성형 AI를 활용한 수업자료 제작 · 코딩 몰라도 따라갈 수 있어요</span>')
    d.rep("""        <tr><td>일 시</td><td>2026. 10. 19.(월) 15:30 ~ (35분 내외)</td></tr>
        <tr><td>장 소</td><td>조선대학교부속중학교 1층 온나누리실(자치복합공간)</td></tr>
        <tr><td>대 상</td><td>조선대학교부속중학교 교원</td></tr>
        <tr><td>강 사</td><td>조선대학교부속고등학교 교사 김다은 (정보·컴퓨터)</td></tr>
        <tr><td>준 비 물</td><td>노트북(크롬 브라우저), Gemini 로그인된 계정, 휴대폰(QR 확인용), 다음 주 수업 단원 1개</td></tr>""",
          f"""        <tr><td>일 시</td><td>{WHEN} ~</td></tr>
        <tr><td>장 소</td><td>{WHERE}</td></tr>
        <tr><td>대 상</td><td>조선대학교부속고등학교 교원</td></tr>
        <tr><td>강 사</td><td>{WHO}</td></tr>
        <tr><td>준 비 물</td><td>노트북(크롬 브라우저), <b>광주아이온 계정</b>, 휴대폰(QR 확인용), 다음 주 수업 단원 1개</td></tr>
        <tr><td>구 성</td><td><b>1부</b> 광주아이온·Gemini Pro · AI 활용 유의사항 · 프롬프트 · Canvas·Gems 실습 · 바이브코딩<br><b>2부</b> LINKFORGE 실습 — 아이디어 → 부탁문 → Canvas → 고치기 → 링크·QR 공유</td></tr>""")
    d.rep('<div class="box c-or"><div class="t">① 이해</div><p>수업용 웹페이지가 학습지와 무엇이 다른지, 어떤 종류를 만들 수 있는지 안다.</p></div>',
          '<div class="box c-or"><div class="t">① 이해</div><p>광주아이온 Gemini Pro와 AI 활용 유의사항, 좋은 프롬프트의 구조를 안다.</p></div>')
    d.rep('<p style="font-family:Outfit,sans-serif;font-weight:700;font-size:12pt;color:#0369a1;margin:0.5mm 0">https://richee-pc.github.io/26AI_design/</p>',
          '<p style="font-weight:900;font-size:17pt;margin:0.5mm 0">부고<span style="color:#ea580c">.짱.com</span></p>')
    # 표지 QR 교체
    d.s = re.sub(r'<svg width="24mm" height="24mm"[\s\S]*?</svg>', lambda m: qr_svg(SITE, "24mm"), d.s, count=1)

    # 2부: 시각 대신 '2부' 표시
    for a, b in [
        ("Ⅰ. 오늘 할 일 · 15:30 ~ 15:35", "2부 · Ⅰ. 오늘 할 일"),
        ("Ⅱ. 아이디어 · 15:35 ~ 15:40", "2부 · Ⅱ. 아이디어"),
        ("Ⅲ. 실습 — 부탁문 만들기 · 15:40 ~ 15:43", "2부 · Ⅲ. 실습 — 부탁문 만들기"),
        ("Ⅳ. 실습 — 화면 만들기·고치기 · 15:43 ~ 15:57", "2부 · Ⅳ. 실습 — 화면 만들기·고치기"),
        ("Ⅴ. 공유하기 · Ⅵ. 수업 적용 · 15:57 ~ 16:02", "2부 · Ⅴ. 공유하기 · Ⅵ. 수업 적용"),
        ("심화 (연수 후 선택) · GitHub + Streamlit 배포", "2부 · 심화 (연수 후 선택) · GitHub + Streamlit 배포"),
        ("Ⅶ. 주의사항 · 마무리 · 16:00 ~ 16:05", "2부 · Ⅶ. 주의사항 · 마무리"),
    ]:
        d.rep(a, b)
    d.s = d.s.replace('<div class="runhead"><b>LINKFORGE</b>', '<div class="runhead"><b>2부 · LINKFORGE</b>')
    d.rep("\"선생님들, 반갑습니다. 오늘은 딱 하나만 가져가시면 됩니다. 다음 주 수업에서 학생들에게 보낼 '링크 하나'입니다. (실습 웹페이지 1번 탭의 '조대부중 알아보기 퀴즈' QR을 화면에 띄우고)",
          "\"이제 2부입니다. 2부에서는 딱 하나만 가져가시면 됩니다. 다음 주 수업에서 학생들에게 보낼 '링크 하나'입니다. (실습 웹페이지 1번 탭의 '조대부고 알아보기 퀴즈' QR을 화면에 띄우고)")
    d.rep("오늘은 시간이 짧으니 Gemini Canvas의 공유 링크까지만 가겠습니다.", "2부는 Gemini Canvas의 공유 링크까지 가겠습니다.")
    d.rep('<div class="foot"><span>강사: 조선대학교부속고등학교 교사 김다은</span>', f'<div class="foot"><span>강사: {WHO}</span>')
    d.s = d.s.replace("조대부중", "조대부고")
    d.rep("4번 탭에 6개 분류 42개 + 나만의 고치기 공식", "4번 탭에 6개 분류 46개 + 나만의 고치기 공식")

    # 1부 원고를 표지 뒤에 넣기
    part1 = (HERE / "part1_lecture.html").read_text(encoding="utf-8").replace("{{QR_GEM}}", qr_svg(GEM, "22mm"))
    d.rep("<!-- 2. 오늘 할 일 -->", part1 + "\n<!-- 2. 오늘 할 일 -->")

    # 쪽 번호 다시 매기기
    pages = d.s.count('<section class="page')
    n = 0
    def foot(m):
        nonlocal n
        n += 1
        return f"<span>{n} / {pages}</span></div>\n</section>"
    d.s = re.sub(r"<span>(?:\d+ / 8|\{\{PAGE\}\})</span></div>\n</section>", foot, d.s)
    assert n == pages, (n, pages)
    for w in ["richee", "김다은", "10. 19", "15:35"]:
        assert w not in d.s, w
    return d.s


NODE_PDF = r"""
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto(process.argv[1], { waitUntil: 'load', timeout: 60000 });
  await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(800);
  await p.pdf({ path: process.argv[2], printBackground: true, preferCSSPageSize: true });
  await b.close();
})();
"""


def pdf_from_html(html, out):
    """크롬(Playwright)으로 HTML을 PDF로 인쇄한다. node 와 playwright 가 필요하다."""
    tmp = HERE / ".build.html"
    tmp.write_text(html, encoding="utf-8")
    subprocess.run(["node", "-e", NODE_PDF, tmp.as_uri(), str(out)], check=True, timeout=180)
    tmp.unlink()


def main():
    intro = PdfReader(sys.argv[1])
    pdf_from_html(build_slides_html(), HERE / ".part2.pdf")
    part2 = PdfReader(HERE / ".part2.pdf")
    total = INTRO_PAGES + len(part2.pages)
    pdf_from_html(relabel_html(INTRO_PAGES, total), HERE / ".labels.pdf")
    labels = PdfReader(HERE / ".labels.pdf")
    pdf_from_html(build_lecture_html(), HERE / "AI_lesson_design_script.pdf")

    w = PdfWriter()
    W = float(intro.pages[0].mediabox.width)
    for i in range(INTRO_PAGES):
        pg = intro.pages[i]
        lb = labels.pages[i]
        pg.merge_transformed_page(lb, Transformation().scale(W / float(lb.mediabox.width)))
        w.add_page(pg)
    for pgobj in part2.pages:
        s = W / float(pgobj.mediabox.width)
        pgobj.add_transformation(Transformation().scale(s, s))
        pgobj.mediabox.upper_right = (float(pgobj.mediabox.width) * s, float(pgobj.mediabox.height) * s)
        w.add_page(pgobj)
    w.compress_identical_objects()
    with open(HERE / "AI_lesson_slides.pdf", "wb") as f:
        w.write(f)
    (HERE / ".part2.pdf").unlink()
    (HERE / ".labels.pdf").unlink()
    print("slides", len(w.pages), "pages")


if __name__ == "__main__":
    main()
