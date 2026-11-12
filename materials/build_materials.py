"""함평손불중 연수 강의자료 3가지 PDF를 만든다.

- 강의자료 1 = 1_school_change_review.pdf : '우리 학교 변화 돌아보기-함평손불중학교' (받은 PDF 그대로)
- 강의자료 2 = 2_AI_class_practice.pdf    : '교과별 AI수업실천과정(생성형AI,캔바)_함평손불중' (받은 PDF 그대로, 마무리 인사 포함)
- 강의자료 3 = 3_webpage_making.pdf       : '생성형AI를 활용한 웹페이지 만들기' (webpage_slides.html)

사용법: python build_materials.py <강의자료1 PDF> <강의자료2 PDF>
필요: pip install pypdf qrcode, node + playwright, Pretendard 글꼴 설치
"""
import io
import re
import shutil
import subprocess
import sys
from pathlib import Path

import qrcode
import qrcode.image.svg
from pypdf import PdfReader, PdfWriter, Transformation

HERE = Path(__file__).resolve().parent
SITE = "https://math94hj-coder.github.io/26sonbul/"


def qr_svg(url, size):
    buf = io.BytesIO()
    qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, border=1).save(buf)
    svg = re.sub(r"<\?xml[^>]*\?>", "", buf.getvalue().decode()).strip()
    return re.sub(r'width="[^"]*" height="[^"]*"', f'width="{size}" height="{size}"', svg, count=1)


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
    """크롬(Playwright)으로 HTML을 PDF로 인쇄한다."""
    tmp = HERE / ".build.html"
    tmp.write_text(html, encoding="utf-8")
    subprocess.run(["node", "-e", NODE_PDF, tmp.as_uri(), str(out)], check=True, timeout=180)
    tmp.unlink()


def add_scaled(w, page, width):
    """1440px(=1080pt) 크기로 인쇄된 쪽을 원본 슬라이드 크기(1440pt)에 맞춰 넣는다."""
    s = width / float(page.mediabox.width)
    page.add_transformation(Transformation().scale(s, s))
    page.mediabox.upper_right = (float(page.mediabox.width) * s, float(page.mediabox.height) * s)
    w.add_page(page)


def main():
    src1, src2 = sys.argv[1], sys.argv[2]

    # 강의자료 1: 그대로
    shutil.copyfile(src1, HERE / "1_school_change_review.pdf")

    # 강의자료 2: 그대로
    shutil.copyfile(src2, HERE / "2_AI_class_practice.pdf")

    # 강의자료 3: 웹페이지 만들기 슬라이드
    s = (HERE / "webpage_slides.html").read_text(encoding="utf-8")
    s = s.replace("{{QR_SITE}}", qr_svg(SITE, 230)).replace("{{QR_SMALL}}", qr_svg(SITE, 110))
    assert "{{" not in s
    pdf_from_html(s, HERE / ".slides.pdf")
    w3 = PdfWriter()
    for pg in PdfReader(HERE / ".slides.pdf").pages:
        add_scaled(w3, pg, 1440)
    w3.compress_identical_objects()
    with open(HERE / "3_webpage_making.pdf", "wb") as f:
        w3.write(f)
    (HERE / ".slides.pdf").unlink()
    print("강의자료 3:", len(w3.pages), "쪽")


if __name__ == "__main__":
    main()
