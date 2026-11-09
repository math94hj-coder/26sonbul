/**
 * LINKFORGE for Teachers — 작품 갤러리 저장소 (Google Apps Script)
 *
 * 설치 방법 (5분)
 * 1) sheet.new 로 새 구글 시트를 만든다. (이름 예: LINKFORGE 갤러리)
 * 2) 메뉴 [확장 프로그램 → Apps Script] → 기본 코드를 지우고 이 파일 내용을 붙여 넣고 저장.
 * 3) [배포 → 새 배포] → 유형: 웹 앱
 *      - 다음 사용자 인증 정보로 실행: 나
 *      - 액세스 권한이 있는 사용자: 모든 사용자
 *    → [배포] → 권한 승인 → 나오는 "웹 앱 URL"(…/exec)을 복사.
 * 4) 저장소 맨 위 config.js 의 LINKFORGE_API = '' 안에 그 URL을 넣는다.
 *
 * 관리
 * - 시트의 '숨김' 열에 아무 글자(예: x)나 적으면 그 작품은 갤러리에 보이지 않는다.
 * - 코드를 고친 뒤에는 [배포 → 배포 관리 → 수정 → 새 버전]으로 다시 배포해야 반영된다.
 *
 * 실시간 대결 점수판 (examples/sonbul-quiz.html 의 '각자 휴대폰 대결', 3번 탭 '실시간 참여' 부탁문으로 만든 웹페이지)
 * - '대전' 시트에 방 코드별 참가자 점수를 저장한다. GET ?room=1234 로 순위를 읽는다.
 * - 연수가 끝난 뒤 '대전' 시트의 행은 지워도 된다.
 * - 학생이 방금 답한 문제 번호(q)와 고른 보기(choice)도 함께 저장해, 교사 화면에서 보기별 응답 수를 보여 줄 수 있다.
 * - 교사 진행(카훗처럼) 방식: POST {action:'host', room, key, q, phase} 로 '진행' 시트에 현재 문제와 단계를 저장하고,
 *   GET ?room=1234 결과의 state 로 학생 화면이 교사 화면을 따라간다. 처음 방을 만든 기기의 key 로만 바꿀 수 있다.
 */
const SHEET_NAME = '갤러리';
const HEADERS = ['id', '등록시각', '이름', '교과', '제목', '소개', '유형', '링크', '삭제키', '숨김', '게시판'];
const LIMITS = { name: 30, subject: 30, title: 60, desc: 200, type: 30, url: 500 };

function sheet_() {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(SHEET_NAME);
    sh.appendRow(HEADERS);
    sh.setFrozenRows(1);
  }
  // 예전에 만든 시트에는 '게시판' 머리글이 없으므로 채워 둔다 (빈 칸 = 원본 연수 갤러리)
  if (!sh.getRange(1, 11).getValue()) sh.getRange(1, 11).setValue('게시판');
  return sh;
}

// 게시판 이름: 영문·숫자만 (예: jeil). 비어 있으면 원본 연수 갤러리
function board_(v) {
  return String(v || '').replace(/[^a-zA-Z0-9_-]/g, '').slice(0, 20);
}

function out_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

// 시트 수식으로 해석되지 않도록 앞에 ' 를 붙이고 길이를 자른다
function clean_(v, max) {
  let s = String(v == null ? '' : v).replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, max);
  if (/^[=+\-@]/.test(s)) s = "'" + s;
  return s;
}

const BATTLE_SHEET = '대전';
const BATTLE_HEADERS = ['방', '참가자id', '닉네임', '점수', '맞힌 수', '푼 문제', '갱신시각', '마지막 문제', '선택'];
const HOST_SHEET = '진행';
const HOST_HEADERS = ['방', '진행키', '문제', '단계', '갱신시각'];

function battleSheet_() {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName(BATTLE_SHEET);
  if (!sh) {
    sh = ss.insertSheet(BATTLE_SHEET);
    sh.appendRow(BATTLE_HEADERS);
    sh.setFrozenRows(1);
  }
  // 예전에 만든 시트에는 '마지막 문제'·'선택' 머리글이 없으므로 채워 둔다
  if (!sh.getRange(1, 8).getValue()) sh.getRange(1, 8, 1, 2).setValues([['마지막 문제', '선택']]);
  return sh;
}

function hostSheet_() {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName(HOST_SHEET);
  if (!sh) {
    sh = ss.insertSheet(HOST_SHEET);
    sh.appendRow(HOST_HEADERS);
    sh.setFrozenRows(1);
  }
  return sh;
}

const PHASES = ['wait', 'question', 'reveal', 'end'];

function hostState_(key) {
  const rows = hostSheet_().getDataRange().getValues().slice(1);
  for (let i = rows.length - 1; i >= 0; i--) {
    if (rows[i][0] === key) return { q: Number(rows[i][2]) || 0, phase: String(rows[i][3] || 'wait'), at: rows[i][4] };
  }
  return { q: 0, phase: 'wait' };
}

function hostUpdate_(d) {
  const key = roomKey_(d.room);
  if (!key) return out_({ ok: false, error: '방 코드는 숫자 4~6자리예요.' });
  const hk = String(d.key || '').replace(/[^a-zA-Z0-9]/g, '').slice(0, 40);
  if (!hk) return out_({ ok: false, error: '진행키가 필요해요.' });
  const q = Math.max(0, Math.min(200, Math.round(Number(d.q) || 0)));
  const phase = PHASES.indexOf(String(d.phase)) >= 0 ? String(d.phase) : 'wait';
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(8000)) return out_({ ok: false, error: '잠시 후 다시 시도해 주세요.' });
  try {
    const sh = hostSheet_();
    const n = sh.getLastRow();
    const rows = n > 1 ? sh.getRange(2, 1, n - 1, 2).getValues() : [];
    for (let i = rows.length - 1; i >= 0; i--) {
      if (rows[i][0] === key) {
        if (rows[i][1] !== 'k' + hk) return out_({ ok: false, error: '이 방은 다른 기기에서 진행 중이에요.' });
        sh.getRange(i + 2, 3, 1, 3).setValues([[q, phase, new Date()]]);
        return out_({ ok: true });
      }
    }
    sh.appendRow([key, 'k' + hk, q, phase, new Date()]);
    return out_({ ok: true });
  } finally {
    lock.releaseLock();
  }
}

// 방 코드는 숫자 4~6자리. 시트에서 숫자로 바뀌지 않도록 'r'을 붙여 저장한다
function roomKey_(v) {
  const digits = String(v || '').replace(/\D/g, '').slice(0, 6);
  return digits.length >= 4 ? 'r' + digits : '';
}

function battleBoard_(room) {
  const key = roomKey_(room);
  if (!key) return out_({ ok: false, error: '방 코드는 숫자 4~6자리예요.' });
  const best = {};
  battleSheet_().getDataRange().getValues().slice(1)
    .filter(function (r) { return r[0] === key; })
    .forEach(function (r) {
      const p = { pid: r[1], nick: r[2], score: Number(r[3]) || 0, correct: Number(r[4]) || 0, done: Number(r[5]) || 0, at: r[6],
                  q: Number(r[7]) || 0, choice: String(r[8] == null ? '' : r[8]) };
      const old = best[p.pid];
      if (!old || p.done > old.done || (p.done === old.done && p.score > old.score)) best[p.pid] = p;
    });
  const players = Object.keys(best).map(function (k) { return best[k]; })
    .sort(function (a, b) { return b.score - a.score || b.correct - a.correct; });
  return out_({ ok: true, room: key.slice(1), players: players, state: hostState_(key) });
}

function battleUpsert_(d) {
  const key = roomKey_(d.room);
  if (!key) return out_({ ok: false, error: '방 코드는 숫자 4~6자리예요.' });
  const pid = 'p' + String(d.pid || '').replace(/[^a-zA-Z0-9]/g, '').slice(0, 24);
  const nick = clean_(d.nick, 12) || '익명';
  const score = Math.max(0, Math.min(100000, Math.round(Number(d.score) || 0)));
  const correct = Math.max(0, Math.min(100, Math.round(Number(d.correct) || 0)));
  const done = Math.max(0, Math.min(100, Math.round(Number(d.done) || 0)));
  const q = Math.max(0, Math.min(200, Math.round(Number(d.q) || 0)));
  const choice = clean_(d.choice, 20);
  const sh = battleSheet_();
  const last = sh.getLastRow();
  const values = last > 1 ? sh.getRange(2, 1, last - 1, 6).getValues() : [];
  for (let i = values.length - 1; i >= 0; i--) {
    if (values[i][0] === key && values[i][1] === pid) {
      // 늦게 도착한 예전 기록이 최신 점수를 덮어쓰지 않도록 푼 문제 수가 줄어드는 갱신은 무시한다
      // 단, 푼 문제 0(다시 입장)은 새 게임 시작이므로 덮어쓴다
      if (done > 0 && done < (Number(values[i][5]) || 0)) return out_({ ok: true, skipped: true });
      sh.getRange(i + 2, 3, 1, 7).setValues([[nick, score, correct, done, new Date(), q, choice]]);
      return out_({ ok: true });
    }
  }
  // 새 참가자 줄 추가만 짧게 잠근다 (동시에 들어온 두 사람이 같은 줄에 쓰지 않도록)
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(8000)) return out_({ ok: false, error: '입장하는 사람이 많아요. 잠시 후 다시 시도해 주세요.' });
  try {
    const n = sh.getLastRow();
    const again = n > 1 ? sh.getRange(2, 1, n - 1, 2).getValues() : [];
    for (let j = again.length - 1; j >= 0; j--) {
      if (again[j][0] === key && again[j][1] === pid) {
        sh.getRange(j + 2, 3, 1, 7).setValues([[nick, score, correct, done, new Date(), q, choice]]);
        return out_({ ok: true });
      }
    }
    sh.appendRow([key, pid, nick, score, correct, done, new Date(), q, choice]);
    return out_({ ok: true });
  } finally {
    lock.releaseLock();
  }
}

function doGet(e) {
  if (e && e.parameter && e.parameter.room) return battleBoard_(e.parameter.room);
  const board = board_(e && e.parameter && e.parameter.board);
  const rows = sheet_().getDataRange().getValues().slice(1);
  const items = rows
    .filter(function (r) { return r[0] && !String(r[9]).trim() && board_(r[10]) === board; })
    .map(function (r) {
      return { id: r[0], at: r[1], name: r[2], subject: r[3], title: r[4], desc: r[5], type: r[6], url: r[7] };
    })
    .reverse();
  return out_({ ok: true, items: items });
}

function doPost(e) {
  let body;
  try { body = JSON.parse((e && e.postData && e.postData.contents) || '{}'); }
  catch (err) { return out_({ ok: false, error: '잘못된 요청이에요.' }); }
  if (body.action === 'host') {
    try { return hostUpdate_(body); } catch (err) { return out_({ ok: false, error: String(err) }); }
  }
  if (body.action === 'battle') {
    try { return battleUpsert_(body); } catch (err) { return out_({ ok: false, error: String(err) }); }
  }
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) return out_({ ok: false, error: '접속이 많아요. 잠시 후 다시 시도해 주세요.' });
  try {
    const d = body;
    const sh = sheet_();

    if (d.action === 'delete') {
      const values = sh.getDataRange().getValues();
      for (let i = 1; i < values.length; i++) {
        if (values[i][0] === d.id && values[i][8] && values[i][8] === d.key) {
          sh.deleteRow(i + 1);
          return out_({ ok: true });
        }
      }
      return out_({ ok: false, error: '삭제할 작품을 찾지 못했어요.' });
    }

    const url = String(d.url || '').trim();
    if (!/^https:\/\/\S+$/.test(url)) return out_({ ok: false, error: '링크는 https:// 로 시작해야 해요.' });
    if (!String(d.title || '').trim()) return out_({ ok: false, error: '작품 제목을 적어 주세요.' });
    if (d.website) return out_({ ok: true, id: 'skip' }); // 자동 등록 봇 차단용 빈칸

    const id = 'g' + Utilities.getUuid().slice(0, 8); // 숫자로 바뀌지 않도록 글자로 시작
    const key = clean_(d.key, 40);
    sh.appendRow([
      id, new Date(),
      clean_(d.name, LIMITS.name), clean_(d.subject, LIMITS.subject), clean_(d.title, LIMITS.title),
      clean_(d.desc, LIMITS.desc), clean_(d.type, LIMITS.type), clean_(url, LIMITS.url),
      key, '', board_(d.board)
    ]);
    return out_({ ok: true, id: id });
  } catch (err) {
    return out_({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}
