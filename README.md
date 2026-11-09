# LINKFORGE for Teachers · 함평손불중

찾아가는 학교컨설팅 교사연수_함평손불중 (장소: 함평손불중학교 컴퓨터실)

- 1차 2026. 10. 13.(화) 15:00 — 생성형AI를 활용한 수업 및 평가 자료 제작
- 2차 2026. 11. 10.(화) 15:00 — Canva를 활용한 수업 및 평가 자료 제작

- 연수 페이지: http://손불.짱.com → https://math94hj-coder.github.io/26sonbul/ (GitHub Pages 켠 뒤)
- 예시 퀴즈: `examples/sonbul-quiz.html` (함평손불중학교 학교소개 기반)
- 예시 퀴즈 2: `examples/ai-quiz.html` (인공지능 기초)
- 강의자료 1: `materials/1_school_change_review.pdf` — 우리 학교 변화 돌아보기-함평손불중학교
- 강의자료 2: `materials/2_AI_class_practice.pdf` — 교과별 AI수업실천과정(생성형AI,캔바)_함평손불중 (마무리 인사 `ai_class_closing.html` 덧붙임)
- 강의자료 3: `materials/3_webpage_making.pdf` — 생성형AI를 활용한 웹페이지 만들기 (`webpage_slides.html`)
- 강의자료 다시 만들기: `python materials/build_materials.py <강의자료1 PDF> <강의자료2 원본 PDF>`
- 원본: [richee-pc/26AI_design](https://github.com/richee-pc/26AI_design) · 조대부고 버전 [math94hj-coder/26bugo](https://github.com/math94hj-coder/26bugo)

## 작품 갤러리 연결 (Google Sheets + Apps Script)

6번 탭 "작품 갤러리"와 예시 퀴즈의 "실시간 대결" 점수판은 구글 시트에 저장됩니다.
주소는 `config.js` 한 곳에만 넣으면 됩니다. (지금은 조대부고 연수와 같은 시트를 쓰고, 게시판 열 값 `sonbul`로 구분합니다.)

1. [sheet.new](https://sheet.new)로 새 구글 시트 만들기 (이름 예: 함평손불중 LINKFORGE 갤러리)
2. **확장 프로그램 → Apps Script** → 기본 코드를 지우고 `materials/gallery_apps_script.gs` 내용을 붙여 넣고 저장(💾)
3. **배포 → 새 배포** → 톱니바퀴에서 **웹 앱** 선택
   - 다음 사용자 인증 정보로 실행: **나**
   - 액세스 권한이 있는 사용자: **모든 사용자**
   - **배포** → 권한 승인(고급 → 안전하지 않은 페이지로 이동 → 허용) → **웹 앱 URL**(`…/exec`) 복사
4. `config.js`의 `window.LINKFORGE_API = '';` 따옴표 안에 URL을 붙여 넣고 커밋

관리
- 작품은 시트의 `갤러리` 탭에 쌓입니다(게시판 열 = `sonbul`). `숨김` 열에 `x`를 적으면 그 작품이 갤러리에서 숨겨집니다.
- 실시간 대결 점수는 `대전` 탭에 쌓이며, 연수가 끝나면 지워도 됩니다.
- Apps Script 코드를 고친 뒤에는 **배포 → 배포 관리 → 수정(연필) → 새 버전**으로 다시 배포해야 반영됩니다.

## GitHub Pages 공개

저장소 **Settings → Pages** → Branch `main`, 폴더 `/ (root)` → Save. 1~2분 뒤 https://math94hj-coder.github.io/26sonbul/ 로 열립니다.
