/* HexQueen game UI. Depends on hexqueen-core.js (window.HexQueenCore). */
(function () {
  'use strict';
  const C = window.HexQueenCore;
  const $ = (sel) => document.querySelector(sel);
  const SVGNS = 'http://www.w3.org/2000/svg';
  const SQRT3 = Math.sqrt(3);

  const COLOR_NAMES = ['Lavender', 'Apricot', 'Sky', 'Mint', 'Butter', 'Coral', 'Slate',
    'Teal', 'Pink', 'Pear', 'Sand', 'Periwinkle', 'Plum'];
  const LEVELS = ['easy', 'medium', 'hard', 'expert'];
  const LEVEL_LABEL = { easy: 'Easy', medium: 'Medium', hard: 'Hard', expert: 'Expert' };
  // Like a newspaper crossword: gentle on Monday, toughest on Saturday.
  const DAILY_BY_WEEKDAY = ['hard', 'easy', 'medium', 'medium', 'hard', 'hard', 'expert'];
  const WEEKDAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  const EMPTY = 0, CROSS = 1, QUEEN = 2;
  // Where people can play, appended to shared results. Embedded hosts such as itch.io run the game
  // in a cross-origin iframe, so its own URL (and any #code in it) is neither visible nor shareable.
  const HOME_URL = '';

  // --------------------------------------------------------------------
  // Persistence (per-viewer convenience only; the game works without it)
  // --------------------------------------------------------------------
  const STORE_KEY = 'hexqueen:v1';
  const DEFAULT_SETTINGS = { autoX: false, conflicts: true, timer: true };
  function loadStore() {
    try { return JSON.parse(localStorage.getItem(STORE_KEY)) || {}; } catch (e) { return {}; }
  }
  let store = normalizeStore(loadStore());
  function normalizeStore(s) {
    return {
      settings: Object.assign({}, DEFAULT_SETTINGS, s.settings || {}),
      stats: s.stats || {},
      daily: s.daily || {},
      games: s.games || {},
      slot: s.slot || null,
      seenRules: !!s.seenRules,
    };
  }
  function save() {
    if (game) store.games[game.slot] = serializeGame();
    try { localStorage.setItem(STORE_KEY, JSON.stringify(store)); } catch (e) { /* storage unavailable */ }
  }

  // --------------------------------------------------------------------
  // Puzzle codes: "hard-k3x9qa", "daily-2026-11-05"
  // --------------------------------------------------------------------
  function dateStr(d) {
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }
  function parseDate(s) { const [y, m, d] = s.split('-').map(Number); return new Date(y, m - 1, d); }
  function randomSeed() {
    const alphabet = 'abcdefghjkmnpqrstuvwxyz23456789';
    let s = '';
    for (let i = 0; i < 6; i++) s += alphabet[Math.floor(Math.random() * alphabet.length)];
    return s;
  }
  function parseCode(code) {
    let m = /^daily-(\d{4}-\d{2}-\d{2})$/.exec(code);
    if (m) {
      const d = parseDate(m[1]);
      if (isNaN(d)) return null;
      return { slot: 'daily', level: DAILY_BY_WEEKDAY[d.getDay()], seed: 'daily:' + m[1], date: m[1], code };
    }
    m = /^(easy|medium|hard|expert)-([a-z0-9]{1,16})$/.exec(code);
    if (m) return { slot: m[1], level: m[1], seed: m[2], code };
    return null;
  }
  // Accepts what people paste: "Hard-K3X9QA", "#hard-k3x9qa", or a whole link ending in "#hard-k3x9qa".
  function normalizeCode(text) {
    let s = String(text || '').trim();
    const hash = s.lastIndexOf('#');
    if (hash >= 0) s = s.slice(hash + 1);
    return s.trim().toLowerCase();
  }

  // --------------------------------------------------------------------
  // Game state
  // --------------------------------------------------------------------
  let game = null;
  const view = { hint: null, focus: -1, keyboard: false, drag: null };
  let els = null; // per-cell SVG elements

  function makeGame(puzzle, info) {
    const geom = C.geometry(puzzle.radius);
    return {
      code: info.code, slot: info.slot, level: info.level, date: info.date || null,
      puzzle, geom, ctx: C.makeContext(geom, puzzle.region),
      marks: new Uint8Array(geom.N), history: [], future: [],
      elapsed: 0, runningSince: null, solved: false, hints: 0, imported: !!puzzle.imported,
    };
  }

  function serializeGame() {
    const g = game;
    return {
      code: g.code, slot: g.slot, marks: Array.from(g.marks).join(''), elapsed: currentElapsed(),
      hints: g.hints, solved: g.solved,
      region: g.imported ? g.puzzle.region : undefined, radius: g.imported ? g.puzzle.radius : undefined,
    };
  }

  function loadPuzzle(code, { fresh = false } = {}) {
    const info = parseCode(code);
    if (!info) return false;
    const puzzle = C.generate({ level: info.level, seed: info.seed });
    startGame(puzzle, info, fresh);
    return true;
  }

  function startGame(puzzle, info, fresh) {
    if (game) { pauseClock(); save(); }
    game = makeGame(puzzle, info);
    const saved = store.games[info.slot];
    if (!fresh && saved && saved.code === info.code && saved.marks && saved.marks.length === game.geom.N) {
      for (let i = 0; i < game.geom.N; i++) game.marks[i] = +saved.marks[i] || 0;
      game.elapsed = saved.elapsed || 0;
      game.hints = saved.hints || 0;
      game.solved = !!saved.solved;
    }
    store.slot = info.slot;
    view.hint = null;
    view.focus = -1;
    buildBoard();
    if (!game.solved) startClock();
    refresh();
    save();
    if (!game.imported) {
      try { if (location.hash !== '#' + game.code) location.replace('#' + game.code); } catch (e) { /* ignore */ }
    }
  }

  function openSlot(slot, { forceNew = false } = {}) {
    if (slot === 'import') {
      const saved = store.games.import;
      if (saved && saved.region) { startImported(saved.radius, saved.region, false); return; }
      slot = 'daily';
    }
    if (slot === 'daily') { loadPuzzle('daily-' + dateStr(new Date())); return; }
    const saved = store.games[slot];
    if (!forceNew && saved && parseCode(saved.code)) { loadPuzzle(saved.code); return; }
    loadPuzzle(slot + '-' + randomSeed(), { fresh: true });
  }

  function startImported(radius, region, fresh) {
    const geom = C.geometry(radius);
    const puzzle = C.finalizePuzzle(geom, region, { seed: 'import', imported: true });
    startGame(puzzle, { code: 'custom', slot: 'import', level: null }, fresh);
  }

  // --------------------------------------------------------------------
  // Clock
  // --------------------------------------------------------------------
  let clockTimer = null;
  function currentElapsed() {
    if (!game) return 0;
    return game.elapsed + (game.runningSince ? Date.now() - game.runningSince : 0);
  }
  function startClock() {
    if (!game || game.solved || game.runningSince || document.hidden) return;
    game.runningSince = Date.now();
    if (!clockTimer) clockTimer = setInterval(renderClock, 250);
  }
  function pauseClock() {
    if (game && game.runningSince) { game.elapsed += Date.now() - game.runningSince; game.runningSince = null; }
    renderClock();
  }
  function fmtTime(ms) {
    const s = Math.floor(ms / 1000), h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
    return (h ? h + ':' + String(m).padStart(2, '0') : m) + ':' + String(sec).padStart(2, '0');
  }
  function renderClock() {
    const t = $('#timer');
    t.textContent = fmtTime(currentElapsed());
    t.classList.toggle('paused', !!game && !game.runningSince && !game.solved);
    t.hidden = !store.settings.timer;
  }
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) { pauseClock(); save(); } else startClock();
  });
  window.addEventListener('pagehide', () => { pauseClock(); save(); });

  // --------------------------------------------------------------------
  // Board rendering
  // --------------------------------------------------------------------
  function hexPoints(cx, cy, s) {
    const pts = [];
    for (let k = 0; k < 6; k++) {
      const a = (Math.PI / 180) * (60 * k - 30);
      pts.push((cx + s * Math.cos(a)).toFixed(4) + ',' + (cy + s * Math.sin(a)).toFixed(4));
    }
    return pts.join(' ');
  }

  // Edge between a cell and its neighbour in direction d (core DIRS order).
  const DIR_OFFSETS = [[1, 0, -1], [1, -1, 0], [0, -1, 1], [-1, 0, 1], [-1, 1, 0], [0, 1, -1]].map(([dx, , dz]) => {
    const ox = SQRT3 * (dx + dz / 2), oy = 1.5 * dz, th = Math.atan2(oy, ox), a1 = th - Math.PI / 6, a2 = th + Math.PI / 6;
    return [Math.cos(a1), Math.sin(a1), Math.cos(a2), Math.sin(a2)];
  });

  function svgEl(tag, attrs, parent) {
    const el = document.createElementNS(SVGNS, tag);
    for (const k in attrs) el.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(el);
    return el;
  }

  /** Draws a board into `svg`; returns per-cell elements. Shared by game and rules demo. */
  function drawBoard(svg, geom, region) {
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    const pad = 0.25;
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const c of geom.cells) {
      minX = Math.min(minX, c.px); maxX = Math.max(maxX, c.px);
      minY = Math.min(minY, c.py); maxY = Math.max(maxY, c.py);
    }
    minX -= SQRT3 / 2 + pad; maxX += SQRT3 / 2 + pad; minY -= 1 + pad; maxY += 1 + pad;
    svg.setAttribute('viewBox', `${minX.toFixed(3)} ${minY.toFixed(3)} ${(maxX - minX).toFixed(3)} ${(maxY - minY).toFixed(3)}`);
    const gBase = svgEl('g', {}, svg);
    const gOver = svgEl('g', {}, svg);
    let inner = '', outer = '';
    geom.cells.forEach((c, i) => {
      geom.neighbors[i].forEach((j, d) => {
        const [x1, y1, x2, y2] = DIR_OFFSETS[d];
        const seg = `M${(c.px + x1).toFixed(4)} ${(c.py + y1).toFixed(4)}L${(c.px + x2).toFixed(4)} ${(c.py + y2).toFixed(4)}`;
        if (j < 0) outer += seg;
        else if (i < j && region[i] !== region[j]) inner += seg;
      });
    });
    svgEl('path', { d: inner, class: 'region-border' }, svg);
    svgEl('path', { d: outer, class: 'outer-border' }, svg);
    const gMarks = svgEl('g', {}, svg);
    const base = [], over = [], marks = [];
    const maxD = geom.radius;
    geom.cells.forEach((c, i) => {
      base.push(svgEl('polygon', { points: hexPoints(c.px, c.py, 1), class: 'cell-base r' + region[i], 'data-i': i }, gBase));
      const o = svgEl('polygon', { points: hexPoints(c.px, c.py, 0.9), class: 'over' }, gOver);
      const dist = Math.max(Math.abs(c.x), Math.abs(c.y), Math.abs(c.z));
      o.style.setProperty('--d', String(dist));
      over.push(o);
      const m = svgEl('use', { href: '#sym-x', x: c.px - 0.5, y: c.py - 0.5, width: 1, height: 1, class: 'mark' }, gMarks);
      m.style.setProperty('--d', String(maxD - dist));
      m.style.display = 'none';
      marks.push(m);
    });
    return { base, over, marks, kind: new Array(geom.N).fill('') };
  }

  function buildBoard() {
    const svg = $('#board');
    svg.classList.remove('won');
    els = drawBoard(svg, game.geom, game.puzzle.region);
    svg.setAttribute('aria-label', `HexQueen board with ${game.geom.n} regions`);
  }

  function setMarkVisual(i, kind) {
    if (els.kind[i] === kind) return;
    els.kind[i] = kind;
    const m = els.marks[i], c = game.geom.cells[i];
    if (!kind) { m.style.display = 'none'; return; }
    m.style.display = '';
    const queenish = kind === 'queen' || kind === 'ghost-queen';
    const size = queenish ? 1.45 : 0.62;
    m.setAttribute('href', queenish ? '#sym-queen' : '#sym-x');
    m.setAttribute('x', (c.px - size / 2).toFixed(4));
    m.setAttribute('y', (c.py - size / 2 + (queenish ? 0.03 : 0)).toFixed(4));
    m.setAttribute('width', size);
    m.setAttribute('height', size);
    m.setAttribute('class', 'mark ' + ({ queen: 'queen', cross: '', auto: 'auto', 'ghost-queen': 'ghost', 'ghost-x': 'ghost' })[kind]);
  }

  // --------------------------------------------------------------------
  // Derived state: attacks and clashes
  // --------------------------------------------------------------------
  function analyse() {
    const { geom, ctx, marks } = game;
    const n = geom.n, N = geom.N;
    const queenCount = new Int16Array(4 * n);
    const queens = [];
    for (let i = 0; i < N; i++) {
      if (marks[i] !== QUEEN) continue;
      queens.push(i);
      for (let f = 0; f < 4; f++) queenCount[f * n + ctx.unitOf[f][i]]++;
    }
    const attacked = new Uint8Array(N);
    for (const q of queens) for (let j = 0; j < N; j++) if (j !== q && C.attacks(ctx, q, j)) attacked[j] = 1;
    const clashCell = new Uint8Array(N), clashQueen = new Uint8Array(N);
    const clashUnits = [];
    for (let k = 0; k < 4 * n; k++) {
      if (queenCount[k] < 2) continue;
      const f = Math.floor(k / n), u = k % n;
      clashUnits.push([f, u]);
      for (const i of ctx.unitCells[f][u]) { clashCell[i] = 1; if (marks[i] === QUEEN) clashQueen[i] = 1; }
    }
    return { queens, attacked, clashCell, clashQueen, clashUnits };
  }

  function refresh() {
    if (!game) return;
    const a = analyse();
    const { N, n } = game.geom;
    const hint = view.hint;
    const src = new Set(hint ? hint.src : []), dst = new Set(hint ? hint.dst : []);
    const ghostX = new Set(hint ? hint.elim : []);
    const ghostQ = hint && hint.place != null ? hint.place : -1;
    const showClash = store.settings.conflicts;
    for (let i = 0; i < N; i++) {
      const m = game.marks[i];
      let kind = '';
      if (i === ghostQ && m !== QUEEN) kind = 'ghost-queen';
      else if (m === QUEEN) kind = 'queen';
      else if (ghostX.has(i) && m !== CROSS) kind = 'ghost-x';
      else if (m === CROSS) kind = 'cross';
      else if (store.settings.autoX && a.attacked[i]) kind = 'auto';
      setMarkVisual(i, kind);
      els.marks[i].classList.toggle('clash', showClash && !!a.clashQueen[i]);
      const o = els.over[i];
      let cls = 'over';
      if (game.solved) cls += ' ripple';
      else if (showClash && a.clashCell[i]) cls += ' clash';
      else if (src.has(i)) cls += ' hl-src';
      else if (dst.has(i)) cls += ' hl-dst';
      if (view.keyboard && i === view.focus) cls += ' focus';
      if (o.getAttribute('class') !== cls) o.setAttribute('class', cls);
    }
    $('#queens-num').textContent = a.queens.length + '/' + n;
    if (!game.solved && a.queens.length === n && a.clashUnits.length === 0) onSolved();
    renderChrome();
  }

  // --------------------------------------------------------------------
  // Chrome: tabs, status, buttons, hint panel
  // --------------------------------------------------------------------
  function puzzleTitle() {
    if (game.slot === 'daily') {
      const d = parseDate(game.date);
      const isToday = game.date === dateStr(new Date());
      return (isToday ? WEEKDAYS[d.getDay()] + "'s puzzle" : MONTHS[d.getMonth()] + ' ' + d.getDate());
    }
    if (game.imported) return 'Custom puzzle';
    return LEVEL_LABEL[game.level] + ' puzzle';
  }

  function renderChrome() {
    document.querySelectorAll('.tab').forEach((t) => t.setAttribute('aria-selected', String(t.dataset.slot === game.slot)));
    const todayDone = !!store.daily[dateStr(new Date())];
    $('#tab-daily .tab-dot').hidden = todayDone;
    $('#status-title').textContent = puzzleTitle();
    const p = game.puzzle;
    const parts = [`${game.geom.n} queens`, `${game.geom.N} cells`];
    if (game.slot === 'daily') parts.unshift(LEVEL_LABEL[game.level]);
    else if (game.imported) parts.unshift(p.difficulty);
    $('#status-sub').textContent = parts.join(' · ');
    $('#puzzle-code').textContent = game.imported ? 'custom' : '#' + game.code;
    $('#btn-code').disabled = game.imported;
    $('#foot-rating').textContent = game.solved ? 'Solved' + (game.hints ? ` with ${game.hints} hint${game.hints > 1 ? 's' : ''}` : '') : '';
    $('#btn-undo').disabled = game.solved || game.history.length === 0;
    $('#btn-clear').disabled = game.solved || !game.marks.some((m) => m);
    $('#btn-hint').disabled = game.solved;
    const newBtn = $('#btn-new');
    newBtn.disabled = game.slot === 'daily' && !game.solved;
    newBtn.title = game.slot === 'daily' ? 'Daily puzzle: one per day' : 'New puzzle';
    newBtn.querySelector('span').textContent = game.slot === 'daily' ? (game.solved ? 'More' : 'New') : 'New';
    renderClock();
    renderHint();
  }

  function swatch(u) {
    return `<span class="swatch r${u}" style="background:var(--r${u})"></span>`;
  }
  function unitName(f, u) {
    if (f === 0) return `${swatch(u)}<strong>${COLOR_NAMES[u]}</strong> region`;
    return ['', 'highlighted ╲ diagonal', 'highlighted ╱ diagonal', 'highlighted row'][f];
  }
  function unitGroupName(units) {
    const f = units[0][0];
    if (f === 0) {
      const names = units.map(([, u]) => `${swatch(u)}<strong>${COLOR_NAMES[u]}</strong>`);
      return joinList(names) + ' regions';
    }
    const word = ['', '╲ diagonals', '╱ diagonals', 'rows'][f];
    return `${units.length} highlighted ${word}`;
  }
  function joinList(items) {
    if (items.length <= 1) return items.join('');
    return items.slice(0, -1).join(', ') + ' and ' + items[items.length - 1];
  }
  function cellsOfUnits(units) {
    const out = [];
    for (const [f, u] of units) for (const i of game.ctx.unitCells[f][u]) out.push(i);
    return out;
  }

  function renderHint() {
    const panel = $('#hint');
    const h = view.hint;
    if (!h || game.solved) { panel.hidden = true; return; }
    panel.hidden = false;
    panel.classList.toggle('warn', !!h.warn);
    $('#hint-label').textContent = h.title;
    $('#hint-text').innerHTML = h.text;
    const apply = $('#hint-apply');
    apply.hidden = !h.apply;
    apply.textContent = h.applyLabel || 'Apply';
  }

  // --------------------------------------------------------------------
  // Hints: explain the next deduction from the player's current position
  // --------------------------------------------------------------------
  const TECHNIQUE_TITLE = {
    attack: 'Clear the lines', single: 'Last spot', confine: 'Boxed in', shared: 'Crossfire',
    set: 'Locked group', trial: 'What if?',
  };

  function computeHint() {
    const { geom, ctx, marks, puzzle } = game;
    const a = analyse();
    if (a.clashUnits.length) {
      const [f, u] = a.clashUnits[0];
      const qs = ctx.unitCells[f][u].filter((i) => marks[i] === QUEEN);
      return {
        warn: true, title: 'Clash', src: qs,
        text: `Two queens share the ${unitName(f, u)}. Each region and line takes exactly one queen.`,
      };
    }
    const solution = new Set(puzzle.solution);
    const wrongQueen = a.queens.find((i) => !solution.has(i));
    if (wrongQueen !== undefined) {
      return {
        warn: true, title: 'Misplaced queen', src: [wrongQueen],
        text: `The highlighted queen in the ${unitName(0, puzzle.region[wrongQueen])} isn't part of the solution.`,
        applyLabel: 'Remove it', apply: () => setCells([[wrongQueen, EMPTY]]),
      };
    }
    const wrongX = puzzle.solution.find((i) => marks[i] === CROSS);
    if (wrongX !== undefined) {
      return {
        warn: true, title: 'Crossed-out queen', src: [wrongX],
        text: `The highlighted cell is crossed out, but the ${unitName(0, puzzle.region[wrongX])}'s queen belongs there.`,
        applyLabel: 'Clear the ×', apply: () => setCells([[wrongX, EMPTY]]),
      };
    }
    const open = new Uint8Array(geom.N);
    for (let i = 0; i < geom.N; i++) {
      open[i] = marks[i] === QUEEN ? 2 : marks[i] === CROSS ? 0 : (store.settings.autoX && a.attacked[i]) ? 0 : 1;
    }
    const step = C.nextStep(ctx, open, 6);
    if (!step || step.contradiction) {
      const missing = puzzle.solution.find((i) => marks[i] !== QUEEN);
      return {
        title: 'Reveal', src: [missing], place: missing,
        text: 'Here is one queen from the solution.',
        applyLabel: 'Place it', apply: () => setCells([[missing, QUEEN]]),
      };
    }
    return describeStep(step);
  }

  function describeStep(s) {
    const title = TECHNIQUE_TITLE[s.kind] || 'Hint';
    const elimApply = () => setCells(s.elim.filter((i) => game.marks[i] === EMPTY).map((i) => [i, CROSS]));
    const plural = s.elim.length === 1 ? 'the marked cell' : `the ${s.elim.length} marked cells`;
    switch (s.kind) {
      case 'attack': {
        return {
          title, src: [s.cell], elim: s.elim, apply: elimApply, applyLabel: 'Cross them out',
          text: `This queen rules out every other cell in its region, its row and both of its diagonals. Cross out ${plural}.`,
        };
      }
      case 'single': {
        const [f, u] = s.units[0];
        return {
          title, src: game.ctx.unitCells[f][u], place: s.place, applyLabel: 'Place the queen',
          apply: () => setCells([[s.place, QUEEN]]),
          text: `The ${unitName(f, u)} has only one open cell left, so its queen goes there.`,
        };
      }
      case 'confine': {
        const [f, u] = s.units[0], [g, v] = s.targets[0];
        const lineWord = ['', '╲ diagonal', '╱ diagonal', 'row'];
        const text = f === 0
          ? `Every open cell of the ${unitName(f, u)} lies in the shaded ${lineWord[g]}. ` +
            `That ${lineWord[g]}'s queen must be the ${COLOR_NAMES[u]} queen, so cross out ${plural}.`
          : `Every open cell of the highlighted ${lineWord[f]} lies in the ${unitName(g, v)}. ` +
            `The ${COLOR_NAMES[v]} queen must sit on that ${lineWord[f]}, so cross out ${plural}.`;
        return {
          title, src: openCells(game.ctx.unitCells[f][u]), dst: game.ctx.unitCells[g][v], elim: s.elim,
          apply: elimApply, applyLabel: 'Cross them out', text,
        };
      }
      case 'shared': {
        const [f, u] = s.units[0];
        return {
          title, src: openCells(game.ctx.unitCells[f][u]), elim: s.elim, apply: elimApply, applyLabel: 'Cross them out',
          text: `Wherever the ${unitName(f, u)}'s queen goes, it attacks ${plural}. They can never hold a queen.`,
        };
      }
      case 'set': {
        const k = s.units.length;
        const word = { 2: 'two', 3: 'three', 4: 'four' }[k];
        const tWord = ['regions', '╲ diagonals', '╱ diagonals', 'rows'][s.targets[0][0]];
        return {
          title: k === 2 ? 'Locked pair' : k === 3 ? 'Locked trio' : 'Locked four',
          src: openCells(cellsOfUnits(s.units)), dst: cellsOfUnits(s.targets), elim: s.elim,
          apply: elimApply, applyLabel: 'Cross them out',
          text: `The ${unitGroupName(s.units)} can only put their queens in the ${word} shaded ${tWord}. ` +
            `Those ${tWord} are spoken for, so cross out ${plural}.`,
        };
      }
      case 'trial': {
        const [f, u] = s.units[0];
        return {
          title, src: [s.cell], dst: game.ctx.unitCells[f][u], elim: s.elim, apply: elimApply, applyLabel: 'Cross it out',
          text: `Suppose the marked cell held a queen. Following the simple rules from there leaves the ${unitName(f, u).replace('highlighted ', 'shaded ')} with nowhere to put its queen, so this cell is ruled out.`,
        };
      }
      default:
        return null;
    }
  }

  function openCells(cells) {
    return cells.filter((i) => game.marks[i] === EMPTY);
  }

  function showHint() {
    if (!game || game.solved) return;
    const h = computeHint();
    if (!h) return;
    view.hint = Object.assign({ src: [], dst: [], elim: [], place: null }, h);
    game.hints++;
    save();
    refresh();
  }

  // --------------------------------------------------------------------
  // Editing with undo
  // --------------------------------------------------------------------
  function setCells(changes, { fromHistory = false } = {}) {
    if (!game || game.solved) return;
    const action = [];
    for (const [i, v] of changes) {
      if (game.marks[i] === v) continue;
      action.push([i, game.marks[i], v]);
      game.marks[i] = v;
    }
    if (!action.length) return;
    if (!fromHistory) { game.history.push(action); game.future.length = 0; }
    afterEdit();
  }

  function afterEdit() {
    view.hint = null;
    startClock();
    refresh();
    save();
  }

  function undo() {
    if (!game || game.solved) return;
    const action = game.history.pop();
    if (!action) return;
    for (let t = action.length - 1; t >= 0; t--) game.marks[action[t][0]] = action[t][1];
    game.future.push(action);
    afterEdit();
  }
  function redo() {
    if (!game || game.solved) return;
    const action = game.future.pop();
    if (!action) return;
    for (const [i, , v] of action) game.marks[i] = v;
    game.history.push(action);
    afterEdit();
  }

  function cycle(i) {
    const m = game.marks[i];
    setCells([[i, m === EMPTY ? CROSS : m === CROSS ? QUEEN : EMPTY]]);
  }

  function clearBoard() {
    const changes = [];
    for (let i = 0; i < game.geom.N; i++) if (game.marks[i]) changes.push([i, EMPTY]);
    if (!changes.length) return;
    setCells(changes);
    toast('Board cleared. Undo brings it back.');
  }

  // --------------------------------------------------------------------
  // Pointer input: tap cycles, drag paints or erases ×
  // --------------------------------------------------------------------
  function cellAtPoint(x, y) {
    const el = document.elementFromPoint(x, y);
    if (!el || !el.hasAttribute('data-i')) return -1;
    return +el.getAttribute('data-i');
  }

  const board = $('#board');
  board.addEventListener('contextmenu', (e) => e.preventDefault());
  board.addEventListener('pointerdown', (e) => {
    if (!game || game.solved) return;
    const t = e.target;
    if (!t.hasAttribute || !t.hasAttribute('data-i')) return;
    const i = +t.getAttribute('data-i');
    view.keyboard = false;
    view.focus = i;
    if (e.button === 2) {
      const m = game.marks[i];
      if (m !== QUEEN) setCells([[i, m === CROSS ? EMPTY : CROSS]]);
      return;
    }
    if (e.button !== 0) return;
    e.preventDefault();
    try { board.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
    const m = game.marks[i];
    view.drag = { id: e.pointerId, start: i, last: i, moved: false, mode: m === EMPTY ? 'paint' : m === CROSS ? 'erase' : null, action: [] };
  });
  board.addEventListener('pointermove', (e) => {
    const d = view.drag;
    if (!d || d.id !== e.pointerId) return;
    const i = cellAtPoint(e.clientX, e.clientY);
    if (i < 0 || i === d.last) return;
    if (!d.moved) { d.moved = true; paint(d, d.start); }
    paint(d, i);
    d.last = i;
  });
  function paint(d, i) {
    if (!d.mode) return;
    const m = game.marks[i];
    if (d.mode === 'paint' && m === EMPTY) { d.action.push([i, EMPTY, CROSS]); game.marks[i] = CROSS; }
    else if (d.mode === 'erase' && m === CROSS) { d.action.push([i, CROSS, EMPTY]); game.marks[i] = EMPTY; }
    else return;
    view.hint = null;
    refresh();
  }
  function endDrag(e) {
    const d = view.drag;
    if (!d || d.id !== e.pointerId) return;
    view.drag = null;
    if (!d.moved) { cycle(d.start); return; }
    if (d.action.length) { game.history.push(d.action); game.future.length = 0; afterEdit(); }
  }
  board.addEventListener('pointerup', endDrag);
  board.addEventListener('pointercancel', endDrag);

  // --------------------------------------------------------------------
  // Keyboard
  // --------------------------------------------------------------------
  function moveFocus(dir) {
    const { geom } = game;
    if (view.focus < 0) { view.focus = Math.floor(geom.N / 2); return; }
    const c = geom.cells[view.focus];
    if (dir === 'left' || dir === 'right') {
      const j = view.focus + (dir === 'left' ? -1 : 1);
      if (j >= 0 && j < geom.N && geom.cells[j].z === c.z) view.focus = j;
      return;
    }
    const z = c.z + (dir === 'up' ? -1 : 1);
    let best = -1, bestD = Infinity;
    geom.cells.forEach((o, j) => {
      if (o.z !== z) return;
      const dd = Math.abs(o.px - c.px);
      if (dd < bestD) { bestD = dd; best = j; }
    });
    if (best >= 0) view.focus = best;
  }

  $('#board-wrap').addEventListener('keydown', (e) => {
    if (!game) return;
    const keys = { ArrowLeft: 'left', ArrowRight: 'right', ArrowUp: 'up', ArrowDown: 'down' };
    if (keys[e.key]) {
      e.preventDefault();
      view.keyboard = true;
      moveFocus(keys[e.key]);
      refresh();
      return;
    }
    if (view.focus < 0 || game.solved || e.ctrlKey || e.metaKey || e.altKey) return;
    const i = view.focus, m = game.marks[i];
    if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); cycle(i); }
    else if (e.key === 'x' || e.key === 'X') setCells([[i, m === CROSS ? EMPTY : CROSS]]);
    else if (e.key === 'q' || e.key === 'Q') setCells([[i, m === QUEEN ? EMPTY : QUEEN]]);
    else if (e.key === 'Backspace' || e.key === 'Delete') setCells([[i, EMPTY]]);
  });
  $('#board-wrap').addEventListener('focus', () => {
    if (view.focus < 0 && game) view.focus = Math.floor(game.geom.N / 2);
  });

  document.addEventListener('keydown', (e) => {
    if (document.querySelector('dialog[open]')) return;
    const tag = (e.target && e.target.tagName) || '';
    if (tag === 'INPUT' || tag === 'TEXTAREA') return;
    const mod = e.ctrlKey || e.metaKey;
    if (mod && (e.key === 'z' || e.key === 'Z')) { e.preventDefault(); if (e.shiftKey) redo(); else undo(); }
    else if (mod && (e.key === 'y' || e.key === 'Y')) { e.preventDefault(); redo(); }
    else if (!mod && !e.altKey && (e.key === 'h' || e.key === 'H')) showHint();
  });

  // --------------------------------------------------------------------
  // Winning and statistics
  // --------------------------------------------------------------------
  function onSolved() {
    pauseClock();
    game.solved = true;
    view.hint = null;
    const ms = currentElapsed();
    const statKey = game.imported ? 'custom' : game.level;
    const st = store.stats[statKey] || (store.stats[statKey] = { solved: 0, total: 0, best: null });
    const first = !(store.games[game.slot] && store.games[game.slot].solved && store.games[game.slot].code === game.code);
    let newBest = false;
    if (first) {
      st.solved++;
      st.total += ms;
      if (st.best == null || ms < st.best) { st.best = ms; newBest = st.solved > 1; }
      if (game.slot === 'daily') store.daily[game.date] = { ms, hints: game.hints };
    }
    save();
    $('#board').classList.add('won');
    refresh();
    const delay = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 150 : 1100;
    setTimeout(() => showWin(ms, newBest), delay);
  }

  function streaks() {
    const days = Object.keys(store.daily).sort();
    let best = 0, run = 0, prev = null;
    for (const d of days) {
      const cur = parseDate(d);
      run = prev && Math.round((cur - prev) / 86400000) === 1 ? run + 1 : 1;
      best = Math.max(best, run);
      prev = cur;
    }
    // current streak: ends today, or yesterday if today isn't solved yet
    let current = 0;
    const t = new Date();
    t.setHours(0, 0, 0, 0);
    if (!store.daily[dateStr(t)]) t.setDate(t.getDate() - 1);
    while (store.daily[dateStr(t)]) { current++; t.setDate(t.getDate() - 1); }
    return { current, best, total: days.length };
  }

  function showWin(ms, newBest) {
    if (!game.solved) return;
    const lvl = game.imported ? game.puzzle.difficulty : LEVEL_LABEL[game.level];
    $('#win-title').textContent = newBest ? 'New best time' : ['Solved', 'Long live the queens', 'The hive is in order', 'Un-bee-lievable'][Math.floor(Math.random() * 4)];
    $('#win-sub').textContent = puzzleTitle() + (game.slot === 'daily' ? ' · ' + lvl : '');
    const st = store.stats[game.imported ? 'custom' : game.level] || {};
    const items = [['Time', fmtTime(ms)], ['Hints', String(game.hints)]];
    if (game.slot === 'daily') items.push(['Streak', String(streaks().current)]);
    else items.push(['Best', st.best != null ? fmtTime(st.best) : '–']);
    $('#win-stats').innerHTML = items.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('');
    $('#win-next').textContent = game.slot === 'daily' ? 'Play Hard' : 'Next puzzle';
    openDialog('#dlg-win');
  }

  function resultText() {
    const ms = currentElapsed();
    const lvl = game.imported ? game.puzzle.difficulty : LEVEL_LABEL[game.level];
    const what = game.slot === 'daily' ? `Daily ${game.date} (${lvl})` : `${lvl} (code ${game.code})`;
    return `🐝 HexQueen ${what}: solved in ${fmtTime(ms)}` + (game.hints ? ` with ${game.hints} hint${game.hints > 1 ? 's' : ''}` : ' with no hints')
      + (HOME_URL ? `\n${HOME_URL}` : '');
  }

  function renderStats() {
    const s = streaks();
    $('#streak').innerHTML = [['Current streak', s.current], ['Best streak', s.best], ['Dailies solved', s.total]]
      .map(([k, v]) => `<div><b>${v}</b><span>${k}</span></div>`).join('');
    const rows = LEVELS.map((l) => [LEVEL_LABEL[l], store.stats[l]]);
    if (store.stats.custom) rows.push(['Custom', store.stats.custom]);
    $('#stats-body').innerHTML = rows.map(([name, st]) => {
      st = st || { solved: 0, total: 0, best: null };
      const avg = st.solved ? fmtTime(st.total / st.solved) : '–';
      return `<tr><td>${name}</td><td>${st.solved}</td><td>${st.best != null ? fmtTime(st.best) : '–'}</td><td>${avg}</td></tr>`;
    }).join('');
  }

  // --------------------------------------------------------------------
  // Dialogs, toasts, copy
  // --------------------------------------------------------------------
  function openDialog(sel) {
    const d = $(sel);
    if (d.open) return;
    try { d.showModal(); } catch (e) { d.setAttribute('open', ''); }
  }
  document.querySelectorAll('dialog').forEach((d) => {
    d.addEventListener('click', (e) => { if (e.target === d) d.close(); }); // click on backdrop
  });

  let toastTimer = null;
  function toast(msg) {
    const t = $('#toast');
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { t.hidden = true; }, 2600);
  }

  function copyText(text, okMsg) {
    const fallback = () => {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      let ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      ta.remove();
      toast(ok ? okMsg : text);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => toast(okMsg), fallback);
    } else fallback();
  }

  function renderRulesDemo() {
    const host = $('#rules-demo');
    if (host.firstChild) return;
    const geom = C.geometry(2);
    const region = new Array(geom.N).fill(6);
    const svg = document.createElementNS(SVGNS, 'svg');
    svg.setAttribute('aria-label', 'A queen in the middle of a small board, attacking its row and both diagonals');
    svg.setAttribute('role', 'img');
    host.appendChild(svg);
    const center = C.cellIndex(geom, 0, 0, 0);
    // regions: a ring split into colours so the picture reads like a real board
    geom.cells.forEach((c, i) => {
      const ang = Math.atan2(c.py, c.px);
      region[i] = i === center ? 0 : [1, 2, 3, 4, 5, 7][Math.floor(((ang + Math.PI) / (2 * Math.PI)) * 6) % 6];
    });
    const e = drawBoard(svg, geom, region);
    geom.cells.forEach((c, i) => {
      const m = e.marks[i];
      if (i === center) {
        m.style.display = '';
        m.setAttribute('href', '#sym-queen');
        m.setAttribute('x', c.px - 0.725); m.setAttribute('y', c.py - 0.7);
        m.setAttribute('width', 1.45); m.setAttribute('height', 1.45);
        m.setAttribute('class', 'mark');
      } else if (geom.lx[i] === geom.lx[center] || geom.ly[i] === geom.ly[center] || geom.lz[i] === geom.lz[center]) {
        m.style.display = '';
        m.setAttribute('x', c.px - 0.31); m.setAttribute('y', c.py - 0.31);
        m.setAttribute('width', 0.62); m.setAttribute('height', 0.62);
        m.setAttribute('class', 'mark auto');
        e.over[i].setAttribute('class', 'over hl-dst');
      }
    });
  }

  // --------------------------------------------------------------------
  // Wiring
  // --------------------------------------------------------------------
  document.querySelectorAll('.tab').forEach((t) => t.addEventListener('click', () => {
    if (game && t.dataset.slot === game.slot) return;
    openSlot(t.dataset.slot);
  }));
  $('#btn-undo').addEventListener('click', undo);
  $('#btn-clear').addEventListener('click', clearBoard);
  $('#btn-hint').addEventListener('click', showHint);
  $('#btn-new').addEventListener('click', () => {
    if (game.slot === 'daily') { openSlot('hard'); return; }
    if (game.imported) { openSlot('medium', { forceNew: true }); return; }
    openSlot(game.slot, { forceNew: true });
  });
  $('#hint-close').addEventListener('click', () => { view.hint = null; refresh(); });
  $('#hint-apply').addEventListener('click', () => { const h = view.hint; if (h && h.apply) h.apply(); });
  $('#btn-code').addEventListener('click', () => {
    $('#code-current-row').hidden = game.imported;
    $('#code-current').textContent = game.imported ? '' : game.code;
    $('#code-input').value = '';
    $('#code-error').hidden = true;
    openDialog('#dlg-code');
  });
  $('#code-copy').addEventListener('click', () => {
    copyText(game.code, 'Puzzle code copied. Paste it under Puzzle codes to play it.');
  });
  $('#code-cancel').addEventListener('click', () => $('#dlg-code').close());
  $('#code-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const raw = $('#code-input').value;
    const code = normalizeCode(raw);
    const err = $('#code-error');
    if (!code) { err.textContent = 'Type or paste a puzzle code first.'; err.hidden = false; return; }
    if (!parseCode(code)) {
      err.textContent = 'That is not a puzzle code. Codes look like hard-k3x9qa or daily-2026-11-07.';
      err.hidden = false;
      return;
    }
    $('#dlg-code').close();
    if (!(game && code === game.code)) loadPuzzle(code);
  });
  $('#btn-rules').addEventListener('click', () => { renderRulesDemo(); openDialog('#dlg-rules'); });
  $('#btn-stats').addEventListener('click', () => { renderStats(); openDialog('#dlg-stats'); });
  $('#btn-settings').addEventListener('click', () => {
    $('#set-autox').checked = store.settings.autoX;
    $('#set-conflicts').checked = store.settings.conflicts;
    $('#set-timer').checked = store.settings.timer;
    $('#import-error').hidden = true;
    $('#reset-confirm').hidden = true;
    openDialog('#dlg-settings');
  });
  $('#dlg-rules').addEventListener('close', () => { store.seenRules = true; save(); });
  [['#set-autox', 'autoX'], ['#set-conflicts', 'conflicts'], ['#set-timer', 'timer']].forEach(([sel, key]) => {
    $(sel).addEventListener('change', (e) => { store.settings[key] = e.target.checked; save(); refresh(); });
  });
  $('#settings-form').addEventListener('submit', (e) => { if (e.submitter && e.submitter.value === 'close') return; e.preventDefault(); });
  $('#import-load').addEventListener('click', () => {
    const err = $('#import-error');
    try {
      const p = C.fromJSON($('#import-json').value);
      if (!p.unique) throw new Error('This puzzle has more than one solution, so it cannot be played fairly.');
      $('#dlg-settings').close();
      startImported(p.radius, p.region, true);
      toast(`Loaded a ${p.difficulty.toLowerCase()} custom puzzle.`);
    } catch (e) {
      err.textContent = e instanceof SyntaxError ? 'That text is not valid JSON. Paste the whole puzzle.json file.' : e.message;
      err.hidden = false;
    }
  });
  $('#reset-stats').addEventListener('click', () => { $('#reset-confirm').hidden = false; });
  $('#reset-no').addEventListener('click', () => { $('#reset-confirm').hidden = true; });
  $('#reset-yes').addEventListener('click', () => {
    store.stats = {}; store.daily = {}; save();
    $('#reset-confirm').hidden = true;
    toast('Statistics erased.');
    refresh();
  });
  $('#win-share').addEventListener('click', () => copyText(resultText(), 'Result copied.'));
  $('#win-next').addEventListener('click', () => {
    $('#dlg-win').close();
    if (game.slot === 'daily') openSlot('hard');
    else if (game.imported) openSlot('medium', { forceNew: true });
    else openSlot(game.slot, { forceNew: true });
  });

  window.addEventListener('hashchange', () => {
    const code = normalizeCode(location.hash);
    if (game && code === game.code) return;
    if (parseCode(code)) loadPuzzle(code);
  });

  // --------------------------------------------------------------------
  // Boot
  // --------------------------------------------------------------------
  function boot(hotData) {
    if (hotData && hotData.store) store = normalizeStore(hotData.store);
    const fromHash = normalizeCode(location.hash);
    if (!(fromHash && loadPuzzle(fromHash))) openSlot(store.slot || 'daily');
    if (!store.seenRules) { renderRulesDemo(); openDialog('#dlg-rules'); }
  }
  const hot = window.claude && window.claude.hot;
  if (hot && hot.snapshot) hot.snapshot(() => { if (game) store.games[game.slot] = serializeGame(); return { store }; });
  if (hot && hot.ready) hot.ready(boot); else boot(hot && hot.data);

  // Exposed for debugging and tests.
  window.HexQueenGame = { get game() { return game; }, showHint, undo, redo, loadPuzzle };
})();
