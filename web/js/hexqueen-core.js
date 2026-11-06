/*
 * HexQueen core engine: geometry, solvers and puzzle generation.
 *
 * Rules
 * -----
 * A board of radius r has N = 3r(r+1)+1 hex cells and n = 2r+1 coloured
 * regions. Place n queens so that every region, and every line along each of
 * the three hex axes, holds exactly one queen. (There are n lines per axis,
 * so "at most one per line" forces "exactly one per line". Neighbouring hexes
 * always share a line, so queens never touch either.)
 *
 * Every region and every line is a "unit". The four unit families (regions,
 * x-lines, y-lines, z-lines) each partition the board into n units, and each
 * unit holds exactly one queen. All deductions below are phrased over units.
 *
 * Works as a browser global (HexQueenCore), inside a Web Worker
 * (importScripts) and under Node (require) for tests.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.HexQueenCore = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // ------------------------------------------------------------------------
  // Seeded RNG (cyrb128 hash -> sfc32). Deterministic on every JS engine, so
  // a level + seed always produces the same puzzle.
  // ------------------------------------------------------------------------
  function cyrb128(str) {
    let h1 = 1779033703, h2 = 3144134277, h3 = 1013904242, h4 = 2773480762;
    for (let i = 0; i < str.length; i++) {
      const k = str.charCodeAt(i);
      h1 = h2 ^ Math.imul(h1 ^ k, 597399067);
      h2 = h3 ^ Math.imul(h2 ^ k, 2869860233);
      h3 = h4 ^ Math.imul(h3 ^ k, 951274213);
      h4 = h1 ^ Math.imul(h4 ^ k, 2716044179);
    }
    h1 = Math.imul(h3 ^ (h1 >>> 18), 597399067);
    h2 = Math.imul(h4 ^ (h2 >>> 22), 2869860233);
    h3 = Math.imul(h1 ^ (h3 >>> 17), 951274213);
    h4 = Math.imul(h2 ^ (h4 >>> 19), 2716044179);
    h1 ^= (h2 ^ h3 ^ h4); h2 ^= h1; h3 ^= h1; h4 ^= h1;
    return [h1 >>> 0, h2 >>> 0, h3 >>> 0, h4 >>> 0];
  }

  function makeRng(seed) {
    let [a, b, c, d] = cyrb128(String(seed));
    function next() {
      a >>>= 0; b >>>= 0; c >>>= 0; d >>>= 0;
      let t = (a + b) | 0;
      a = b ^ (b >>> 9);
      b = (c + (c << 3)) | 0;
      c = (c << 21) | (c >>> 11);
      d = (d + 1) | 0;
      t = (t + d) | 0;
      c = (c + t) | 0;
      return (t >>> 0) / 4294967296;
    }
    for (let i = 0; i < 12; i++) next();
    return {
      next,
      int: (n) => Math.floor(next() * n),
      pick: (arr) => arr[Math.floor(next() * arr.length)],
      shuffle(arr) {
        for (let i = arr.length - 1; i > 0; i--) {
          const j = Math.floor(next() * (i + 1));
          const t = arr[i]; arr[i] = arr[j]; arr[j] = t;
        }
        return arr;
      },
    };
  }

  // ------------------------------------------------------------------------
  // Geometry
  // ------------------------------------------------------------------------
  const DIRS = [[1, 0, -1], [1, -1, 0], [0, -1, 1], [-1, 0, 1], [-1, 1, 0], [0, 1, -1]];
  const SQRT3 = Math.sqrt(3);
  const geomCache = new Map();

  function popcount(v) {
    v = v - ((v >>> 1) & 0x55555555);
    v = (v & 0x33333333) + ((v >>> 2) & 0x33333333);
    return (((v + (v >>> 4)) & 0x0f0f0f0f) * 0x01010101) >>> 24;
  }
  function lowBit(v) { return 31 - Math.clz32(v & -v); }

  /**
   * Static board geometry for radius r. Cells are ordered row by row
   * (z = -r .. r, top to bottom), left to right within a row, for a
   * pointy-top layout where z-lines are horizontal rows.
   */
  function geometry(radius) {
    if (geomCache.has(radius)) return geomCache.get(radius);
    const r = radius, n = 2 * r + 1;
    const cells = [];
    const index = new Map();
    for (let z = -r; z <= r; z++) {
      for (let x = Math.max(-r, -z - r); x <= Math.min(r, -z + r); x++) {
        const y = -x - z;
        index.set(x + ',' + z, cells.length);
        cells.push({ x, y, z, px: SQRT3 * (x + z / 2), py: 1.5 * z });
      }
    }
    const N = cells.length;
    const W = Math.ceil(N / 32);
    const lx = new Int8Array(N), ly = new Int8Array(N), lz = new Int8Array(N);
    const lines = [[], [], []];
    for (let a = 0; a < 3; a++) for (let u = 0; u < n; u++) lines[a].push([]);
    cells.forEach((c, i) => {
      lx[i] = c.x + r; ly[i] = c.y + r; lz[i] = c.z + r;
      lines[0][lx[i]].push(i); lines[1][ly[i]].push(i); lines[2][lz[i]].push(i);
    });
    const neighbors = cells.map((c) => {
      const out = [];
      for (let d = 0; d < 6; d++) {
        const j = index.get((c.x + DIRS[d][0]) + ',' + (c.z + DIRS[d][2]));
        out.push(j === undefined ? -1 : j); // keep direction order; -1 = off board
      }
      return out;
    });
    // Bitset of cells that share a line with each cell (cell itself included).
    const lineAttack = cells.map((_, i) => {
      const bits = new Uint32Array(W);
      for (const fam of [lines[0][lx[i]], lines[1][ly[i]], lines[2][lz[i]]])
        for (const j of fam) bits[j >>> 5] |= 1 << (j & 31);
      return bits;
    });
    const g = { radius: r, n, N, W, cells, index, lx, ly, lz, lines, neighbors, lineAttack };
    geomCache.set(radius, g);
    return g;
  }

  function cellIndex(geom, x, y, z) {
    if (x + y + z !== 0) return -1;
    const i = geom.index.get(x + ',' + z);
    return i === undefined ? -1 : i;
  }

  // ------------------------------------------------------------------------
  // Puzzle context: unit tables for one region layout.
  // Family 0 = regions, 1 = x-lines (↘), 2 = y-lines (↗), 3 = z-lines (rows).
  // ------------------------------------------------------------------------
  function makeContext(geom, region) {
    const { n, N, W } = geom;
    const reg = Int8Array.from(region);
    const regionCells = [];
    for (let u = 0; u < n; u++) regionCells.push([]);
    for (let i = 0; i < N; i++) regionCells[reg[i]].push(i);
    const unitOf = [reg, geom.lx, geom.ly, geom.lz];
    const unitCells = [regionCells, geom.lines[0], geom.lines[1], geom.lines[2]];
    const regionBits = regionCells.map((cs) => {
      const b = new Uint32Array(W);
      for (const j of cs) b[j >>> 5] |= 1 << (j & 31);
      return b;
    });
    const attack = new Array(N);
    for (let i = 0; i < N; i++) {
      const b = new Uint32Array(W), la = geom.lineAttack[i], rb = regionBits[reg[i]];
      for (let w = 0; w < W; w++) b[w] = la[w] | rb[w];
      attack[i] = b;
    }
    return { geom, n, N, W, region: reg, unitOf, unitCells, attack };
  }

  function attacks(ctx, i, j) {
    return (ctx.attack[i][j >>> 5] >>> (j & 31)) & 1;
  }

  // ------------------------------------------------------------------------
  // Exhaustive solver (solution counting)
  // ------------------------------------------------------------------------
  function findSolutions(geom, region, limit) {
    const { n, N, lx, ly, lz } = geom;
    const cellsOf = [];
    for (let u = 0; u < n; u++) cellsOf.push([]);
    for (let i = 0; i < N; i++) cellsOf[region[i]].push(i);
    const done = new Uint8Array(n);
    const chosen = new Int16Array(n);
    const out = [];
    const cap = limit == null ? Infinity : limit;
    let ux = 0, uy = 0, uz = 0;
    const buf = [];
    for (let d = 0; d <= n; d++) buf.push(new Int16Array(N));

    function rec(depth) {
      if (depth === n) { out.push(Array.from(chosen)); return; }
      let best = -1, bestCount = 1e9;
      const opts = buf[depth];
      for (let u = 0; u < n; u++) {
        if (done[u]) continue;
        let c = 0;
        for (const i of cellsOf[u]) {
          if (!((ux >>> lx[i]) & 1) && !((uy >>> ly[i]) & 1) && !((uz >>> lz[i]) & 1)) c++;
        }
        if (c === 0) return;
        if (c < bestCount) { bestCount = c; best = u; if (c === 1) break; }
      }
      let k = 0;
      for (const i of cellsOf[best]) {
        if (!((ux >>> lx[i]) & 1) && !((uy >>> ly[i]) & 1) && !((uz >>> lz[i]) & 1)) opts[k++] = i;
      }
      done[best] = 1;
      for (let t = 0; t < k; t++) {
        const i = opts[t];
        chosen[best] = i;
        ux |= 1 << lx[i]; uy |= 1 << ly[i]; uz |= 1 << lz[i];
        rec(depth + 1);
        ux &= ~(1 << lx[i]); uy &= ~(1 << ly[i]); uz &= ~(1 << lz[i]);
        if (out.length >= cap) break;
      }
      done[best] = 0;
    }
    rec(0);
    return out;
  }

  function countSolutions(geom, region, limit) {
    return findSolutions(geom, region, limit).length;
  }

  // ------------------------------------------------------------------------
  // Logical solver
  //
  // Techniques, from easiest to hardest. The solver always uses the easiest
  // technique that makes progress, so the hardest tier it needed is a fair
  // difficulty rating.
  //
  //  0 attack   A queen rules out every other cell in its region and lines.
  //  1 single   A unit with one open cell must hold its queen there.
  //  2 confine  Unit A's open cells all lie inside unit B (another family),
  //             so B's queen is A's queen: the rest of B is ruled out.
  //  3 shared   Every open cell of unit A attacks cell c, so wherever A's
  //             queen goes, c is ruled out.
  //  4 pair     k=2 units of one family can only use k units of another
  //             family; those k units are spoken for, so their other cells
  //             are ruled out.
  //  5 set      The same with k=3 or 4.
  //  6 trial    A queen at c would (via tiers 1-2) leave some unit empty.
  //
  // `open` is a Uint8Array over cells: 0 = ruled out, 1 = open, 2 = queen.
  // ------------------------------------------------------------------------
  const TIER_NAMES = ['attack', 'single', 'confine', 'shared', 'pair', 'set', 'trial'];

  function unitStats(ctx, open) {
    const { n, N, unitOf } = ctx;
    const cnt = new Int16Array(4 * n), queen = new Int16Array(4 * n).fill(-1);
    let bad = -1;
    for (let i = 0; i < N; i++) {
      const s = open[i];
      if (s === 0) continue;
      for (let f = 0; f < 4; f++) {
        const k = f * n + unitOf[f][i];
        if (s === 1) cnt[k]++;
        else { if (queen[k] !== -1) bad = k; queen[k] = i; }
      }
    }
    if (bad === -1) {
      for (let k = 0; k < 4 * n; k++) if (queen[k] === -1 && cnt[k] === 0) { bad = k; break; }
    }
    return { cnt, queen, bad };
  }

  /** Place a queen and rule out everything it attacks; returns cells ruled out. */
  function placeQueen(ctx, open, c) {
    const elim = [];
    const a = ctx.attack[c];
    open[c] = 2;
    for (let j = 0; j < ctx.N; j++) {
      if (j !== c && open[j] === 1 && ((a[j >>> 5] >>> (j & 31)) & 1)) { open[j] = 0; elim.push(j); }
    }
    return elim;
  }

  function eliminate(open, cells) { for (const c of cells) open[c] = 0; }

  function unitList(fam, units) { return units.map((u) => [fam, u]); }

  // Per-family masks: masks[f][g][u] = bitmask of g-units touched by open cells of f-unit u.
  function familyMasks(ctx, open) {
    const { n, N, unitOf } = ctx;
    const masks = [];
    for (let f = 0; f < 4; f++) {
      masks.push([]);
      for (let g = 0; g < 4; g++) masks[f].push(f === g ? null : new Int32Array(n));
    }
    for (let i = 0; i < N; i++) {
      if (open[i] !== 1) continue;
      for (let f = 0; f < 4; f++) {
        const uf = unitOf[f][i];
        for (let g = 0; g < 4; g++) if (g !== f) masks[f][g][uf] |= 1 << unitOf[g][i];
      }
    }
    return masks;
  }

  function trySingles(ctx, open, st) {
    const { n, N, unitOf, unitCells } = ctx;
    // Prefer regions, then rows, then diagonals: easiest for people to spot.
    for (const f of [0, 3, 1, 2]) {
      for (let u = 0; u < n; u++) {
        const k = f * n + u;
        if (st.queen[k] !== -1 || st.cnt[k] !== 1) continue;
        const c = unitCells[f][u].find((i) => open[i] === 1);
        const elim = placeQueen(ctx, open, c);
        return { tier: 1, kind: 'single', place: c, elim, units: [[f, u]] };
      }
    }
    return null;
  }

  function trySets(ctx, open, st, k, masks) {
    const { n, N, unitOf } = ctx;
    const famOrder = [0, 3, 1, 2];
    for (const f of famOrder) {
      const live = [];
      for (let u = 0; u < n; u++) if (st.queen[f * n + u] === -1) live.push(u);
      if (k >= live.length) continue;
      for (const g of famOrder) {
        if (g === f) continue;
        const m = masks[f][g];
        const idx = [];
        for (let t = 0; t < k; t++) idx.push(t);
        while (true) {
          let union = 0, setBits = 0;
          for (const t of idx) { union |= m[live[t]]; setBits |= 1 << live[t]; }
          if (popcount(union) === k) {
            const elim = [];
            for (let i = 0; i < N; i++) {
              if (open[i] === 1 && ((union >>> unitOf[g][i]) & 1) && !((setBits >>> unitOf[f][i]) & 1)) elim.push(i);
            }
            if (elim.length) {
              eliminate(open, elim);
              const src = idx.map((t) => live[t]);
              const dst = [];
              for (let v = union; v; v &= v - 1) dst.push(lowBit(v));
              return {
                tier: k === 1 ? 2 : k === 2 ? 4 : 5,
                kind: k === 1 ? 'confine' : 'set',
                k, elim, units: unitList(f, src), targets: unitList(g, dst),
              };
            }
          }
          // next combination
          let t = k - 1;
          while (t >= 0 && idx[t] === live.length - k + t) t--;
          if (t < 0) break;
          idx[t]++;
          for (let s = t + 1; s < k; s++) idx[s] = idx[s - 1] + 1;
        }
      }
    }
    return null;
  }

  function tryShared(ctx, open, st) {
    const { n, N, W, unitCells, unitOf, attack } = ctx;
    const inter = new Uint32Array(W);
    for (const f of [0, 3, 1, 2]) {
      for (let u = 0; u < n; u++) {
        if (st.queen[f * n + u] !== -1) continue;
        const cs = unitCells[f][u].filter((i) => open[i] === 1);
        if (cs.length < 2) continue;
        inter.fill(0xffffffff);
        for (const c of cs) { const a = attack[c]; for (let w = 0; w < W; w++) inter[w] &= a[w]; }
        const elim = [];
        for (let j = 0; j < N; j++) {
          if (open[j] === 1 && unitOf[f][j] !== u && ((inter[j >>> 5] >>> (j & 31)) & 1)) elim.push(j);
        }
        if (elim.length) {
          eliminate(open, elim);
          return { tier: 3, kind: 'shared', elim, units: [[f, u]] };
        }
      }
    }
    return null;
  }

  /** Propagate tiers 1-2 on a scratch copy; returns the failing unit key or -1. */
  function propagateForContradiction(ctx, open) {
    for (let guard = 0; guard < 400; guard++) {
      const st = unitStats(ctx, open);
      if (st.bad !== -1) return st.bad;
      if (trySingles(ctx, open, st)) continue;
      if (trySets(ctx, open, st, 1, familyMasks(ctx, open))) continue;
      return -1;
    }
    return -1;
  }

  function tryTrial(ctx, open) {
    const { N, n } = ctx;
    for (let c = 0; c < N; c++) {
      if (open[c] !== 1) continue;
      const scratch = Uint8Array.from(open);
      placeQueen(ctx, scratch, c);
      const bad = propagateForContradiction(ctx, scratch);
      if (bad !== -1) {
        open[c] = 0;
        const f = Math.floor(bad / n), u = bad % n;
        return { tier: 6, kind: 'trial', elim: [c], units: [[f, u]], cell: c };
      }
    }
    return null;
  }

  function tryAttack(ctx, open) {
    const { N, n, unitOf } = ctx;
    for (let q = 0; q < N; q++) {
      if (open[q] !== 2) continue;
      const elim = [];
      for (let j = 0; j < N; j++) if (open[j] === 1 && attacks(ctx, q, j)) elim.push(j);
      if (elim.length) {
        eliminate(open, elim);
        return { tier: 0, kind: 'attack', cell: q, elim, units: [0, 1, 2, 3].map((f) => [f, unitOf[f][q]]) };
      }
    }
    return null;
  }

  /** Find and apply the easiest deduction available (mutates `open`). */
  function nextStep(ctx, open, maxTier) {
    const st = unitStats(ctx, open);
    if (st.bad !== -1) return { contradiction: true, unit: st.bad };
    let s = tryAttack(ctx, open);
    if (s) return s;
    s = trySingles(ctx, open, st);
    if (s) return s;
    if (maxTier < 2) return null;
    const masks = familyMasks(ctx, open);
    s = trySets(ctx, open, st, 1, masks);
    if (s) return s;
    if (maxTier < 3) return null;
    s = tryShared(ctx, open, st);
    if (s) return s;
    if (maxTier < 4) return null;
    s = trySets(ctx, open, st, 2, masks);
    if (s) return s;
    if (maxTier < 5) return null;
    s = trySets(ctx, open, st, 3, masks) || trySets(ctx, open, st, 4, masks);
    if (s) return s;
    if (maxTier < 6) return null;
    return tryTrial(ctx, open);
  }

  function isSolved(ctx, open) {
    let q = 0;
    for (let i = 0; i < ctx.N; i++) if (open[i] === 2) q++;
    else if (open[i] === 1) return false;
    return q === ctx.n;
  }

  /**
   * Solve by deduction. Returns { solved, contradiction, maxTier, tierCounts,
   * steps (if record), open, remaining }.
   */
  function logicalSolve(ctx, opts = {}) {
    const maxTier = opts.maxTier == null ? 6 : opts.maxTier;
    const open = opts.open ? Uint8Array.from(opts.open) : new Uint8Array(ctx.N).fill(1);
    const steps = [];
    const tierCounts = new Int16Array(7);
    let hardest = 0, contradiction = false;
    for (let guard = 0; guard < 10000; guard++) {
      if (isSolved(ctx, open)) break;
      const s = nextStep(ctx, open, maxTier);
      if (!s) break;
      if (s.contradiction) { contradiction = true; break; }
      tierCounts[s.tier]++;
      if (s.tier > hardest) hardest = s.tier;
      if (opts.record) steps.push(s);
    }
    let remaining = 0;
    for (let i = 0; i < ctx.N; i++) if (open[i] === 1) remaining++;
    return { solved: !contradiction && isSolved(ctx, open), contradiction, maxTier: hardest, tierCounts, steps, open, remaining };
  }

  // ------------------------------------------------------------------------
  // Generation
  // ------------------------------------------------------------------------
  const LEVELS = {
    easy:   { radius: 3, minTier: 1, maxTier: 2, label: 'Easy', minRegion: 1 },
    medium: { radius: 4, minTier: 3, maxTier: 3, label: 'Medium', candidates: 3 },
    hard:   { radius: 5, minTier: 4, maxTier: 4, label: 'Hard', candidates: 4 },
    expert: { radius: 6, minTier: 5, maxTier: 6, label: 'Expert', candidates: 4 },
  };

  function difficultyLabel(tier) {
    if (tier <= 2) return 'Easy';
    if (tier === 3) return 'Medium';
    if (tier === 4) return 'Hard';
    return 'Expert';
  }

  /** Random non-attacking queen layout (one per row, distinct diagonals). */
  function randomQueens(geom, rng) {
    const { n, lines, lx, ly } = geom;
    const rows = lines[2].map((row) => rng.shuffle(row.slice()));
    const pick = new Int16Array(n);
    let ux = 0, uy = 0, nodes = 0;
    function rec(z) {
      if (z === n) return true;
      if (++nodes > 200000) return false;
      for (const i of rows[z]) {
        if ((ux >>> lx[i]) & 1 || (uy >>> ly[i]) & 1) continue;
        ux |= 1 << lx[i]; uy |= 1 << ly[i]; pick[z] = i;
        if (rec(z + 1)) return true;
        ux &= ~(1 << lx[i]); uy &= ~(1 << ly[i]);
      }
      return false;
    }
    return rec(0) ? Array.from(pick) : null;
  }

  /** Grow one contiguous region around each queen, with uneven growth rates. */
  function growRegions(geom, queens, rng, compact = 3) {
    const { N, neighbors } = geom;
    const n = queens.length;
    const region = new Int8Array(N).fill(-1);
    const frontier = [];
    const weight = [];
    for (let k = 0; k < n; k++) {
      frontier.push(new Set());
      const w = 0.25 + rng.next() * 1.75;
      weight.push(w * w);
    }
    queens.forEach((q, k) => { region[q] = k; });
    queens.forEach((q, k) => {
      for (const j of neighbors[q]) if (j >= 0 && region[j] === -1) frontier[k].add(j);
    });
    let left = N - n;
    while (left > 0) {
      let total = 0;
      for (let k = 0; k < n; k++) if (frontier[k].size) total += weight[k];
      if (total === 0) return null;
      let pickW = rng.next() * total, k = 0;
      for (; k < n; k++) {
        if (!frontier[k].size) continue;
        pickW -= weight[k];
        if (pickW <= 0) break;
      }
      if (k === n) k = frontier.findIndex((f) => f.size);
      // Sample a few frontier cells and keep the one most enclosed by the
      // region: regions stay blob-like instead of growing thin tendrils.
      const options = Array.from(frontier[k]);
      let c = -1, bestScore = -1;
      for (let s = 0; s < Math.min(compact, options.length); s++) {
        const cand = options[rng.int(options.length)];
        let own = 0;
        for (const j of neighbors[cand]) if (j >= 0 && region[j] === k) own++;
        if (own > bestScore) { bestScore = own; c = cand; }
      }
      region[c] = k;
      left--;
      for (const j of neighbors[c]) {
        if (j < 0) continue;
        if (region[j] === -1) frontier[k].add(j);
      }
      for (let t = 0; t < n; t++) frontier[t].delete(c);
    }
    return region;
  }

  function connectedWithout(geom, region, reg, removed) {
    const { N, neighbors } = geom;
    let start = -1, total = 0;
    for (let i = 0; i < N; i++) if (region[i] === reg && i !== removed) { total++; if (start < 0) start = i; }
    if (start < 0) return false;
    const seen = new Uint8Array(N);
    const stack = [start];
    seen[start] = 1;
    let count = 1;
    while (stack.length) {
      const c = stack.pop();
      for (const j of neighbors[c]) {
        if (j >= 0 && !seen[j] && j !== removed && region[j] === reg) { seen[j] = 1; count++; stack.push(j); }
      }
    }
    return count === total;
  }

  const SOLUTION_CAP = 48;

  function scorePuzzle(geom, region, cfg) {
    const extra = countSolutions(geom, region, SOLUTION_CAP) - 1;
    if (extra > 0) return { key: [extra, geom.N, 1], tier: 0 };
    const ctx = makeContext(geom, region);
    const res = logicalSolve(ctx, { maxTier: cfg.maxTier });
    if (!res.solved) return { key: [0, res.remaining, 1], tier: 0 };
    const tooEasy = res.maxTier < cfg.minTier ? 1 : 0;
    return { key: [0, 0, tooEasy], tier: res.maxTier, counts: res.tierCounts };
  }

  function cmpKey(a, b) {
    for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return a[i] - b[i];
    return 0;
  }

  /**
   * Generate a puzzle. Options: { level | radius, seed, minTier, maxTier,
   * attempts, steps }. Always returns a unique, logically solvable puzzle;
   * `onTarget` says whether it also met the requested difficulty band.
   */
  function generate(options = {}) {
    const lvl = LEVELS[options.level] || LEVELS.medium;
    const pool = options.candidates || lvl.candidates || 1;
    const seed = options.seed == null ? String(Math.floor(Math.random() * 1e9)) : String(options.seed);
    let best = null;
    for (let k = 0; k < pool; k++) {
      const p = generateOne({ ...options, seed: k ? seed + '/' + k : seed });
      p.seed = seed;
      if (!best || puzzleQuality(p) > puzzleQuality(best)) best = p;
    }
    return best;
  }

  /** Higher is better: on target, many deductions at the hardest tier, few freebies. */
  function puzzleQuality(p) {
    const top = p.tierCounts[p.tier] || 0;
    return (p.onTarget ? 1000 : 0) + 10 * Math.min(top, 6) + (p.tierCounts[3] || 0) - (p.tierCounts[1] || 0) * 0.5;
  }

  function generateOne(options) {
    const lvl = LEVELS[options.level] || LEVELS.medium;
    const cfg = {
      radius: options.radius || lvl.radius,
      minTier: options.minTier || lvl.minTier,
      maxTier: options.maxTier || lvl.maxTier,
      attempts: options.attempts || 40,
      steps: options.steps || 2500,
      minRegion: options.minRegion || lvl.minRegion || 2,
    };
    const seed = options.seed == null ? String(Math.floor(Math.random() * 1e9)) : String(options.seed);
    const rng = makeRng('hexqueen:' + cfg.radius + ':' + cfg.minTier + '-' + cfg.maxTier + ':' + seed);
    const geom = geometry(cfg.radius);
    const { N, n, neighbors } = geom;
    let fallback = null, evaluations = 0;

    for (let attempt = 0; attempt < cfg.attempts; attempt++) {
      const queens = randomQueens(geom, rng);
      if (!queens) continue;
      const isQueen = new Uint8Array(N);
      for (const q of queens) isQueen[q] = 1;
      const region = growRegions(geom, queens, rng);
      if (!region) continue;
      const sizes = new Int16Array(n);
      for (let i = 0; i < N; i++) sizes[region[i]]++;
      if (sizes.some((s) => s < cfg.minRegion)) continue;

      let score = scorePuzzle(geom, region, cfg);
      evaluations++;
      for (let step = 0; step < cfg.steps; step++) {
        if (score.key[0] === 0 && score.key[1] === 0) {
          if (!fallback || (score.key[2] === 0 && fallback.offTarget)) {
            fallback = { region: Int8Array.from(region), queens: queens.slice(), tier: score.tier, offTarget: score.key[2] === 1 };
          }
          if (score.key[2] === 0) break;
        }
        // propose a boundary move
        let move = null;
        for (let tries = 0; tries < 50 && !move; tries++) {
          const c = rng.int(N);
          if (isQueen[c]) continue;
          const src = region[c];
          if (sizes[src] <= cfg.minRegion) continue;
          const targets = [];
          for (const j of neighbors[c]) if (j >= 0 && region[j] !== src && targets.indexOf(region[j]) < 0) targets.push(region[j]);
          if (!targets.length) continue;
          if (!connectedWithout(geom, region, src, c)) continue;
          move = [c, src, targets[rng.int(targets.length)]];
        }
        if (!move) break;
        const [c, src, dst] = move;
        region[c] = dst;
        const next = scorePuzzle(geom, region, cfg);
        evaluations++;
        if (cmpKey(next.key, score.key) <= 0) {
          score = next; sizes[src]--; sizes[dst]++;
        } else {
          region[c] = src;
        }
      }
      if (fallback && !fallback.offTarget) break;
    }
    if (!fallback) throw new Error('Could not generate a puzzle');
    return finalizePuzzle(geom, fallback.region, {
      seed, level: options.level || null, onTarget: !fallback.offTarget, evaluations,
    });
  }

  function finalizePuzzle(geom, region, meta = {}) {
    const ctx = makeContext(geom, region);
    const res = logicalSolve(ctx, { maxTier: 6 });
    const sols = findSolutions(geom, region, 2);
    const solution = sols.length ? sols[0] : null; // solution[regionId] = cell index
    return {
      radius: geom.radius,
      region: Array.from(region),
      solution,
      unique: sols.length === 1,
      logical: res.solved,
      tier: res.maxTier,
      tierCounts: Array.from(res.tierCounts),
      difficulty: difficultyLabel(res.maxTier),
      ...meta,
    };
  }

  /** Build a puzzle from the Python generator's JSON format (spec 230). */
  function fromJSON(obj) {
    const data = typeof obj === 'string' ? JSON.parse(obj) : obj;
    const radius = data.grid_radius;
    if (!Number.isInteger(radius) || radius < 1 || radius > 7) throw new Error('grid_radius must be a whole number from 1 to 7');
    const geom = geometry(radius);
    const region = new Int8Array(geom.N).fill(-1);
    const ids = new Map();
    for (const [key, rid] of Object.entries(data.cell_regions || {})) {
      const nums = key.match(/-?\d+/g);
      if (!nums || nums.length !== 3) throw new Error('Bad cell key ' + key);
      const i = cellIndex(geom, +nums[0], +nums[1], +nums[2]);
      if (i < 0) throw new Error('Cell ' + key + ' is not on a radius-' + radius + ' board');
      if (!ids.has(rid)) ids.set(rid, ids.size);
      region[i] = ids.get(rid);
    }
    if (region.some((r) => r < 0)) throw new Error('Some cells have no region');
    if (ids.size !== geom.n) throw new Error('Expected ' + geom.n + ' regions, found ' + ids.size);
    return finalizePuzzle(geom, region, { seed: 'import', level: null, onTarget: true, imported: true });
  }

  return {
    makeRng, geometry, cellIndex, makeContext, attacks, popcount,
    findSolutions, countSolutions, logicalSolve, nextStep, unitStats,
    LEVELS, TIER_NAMES, difficultyLabel, generate, finalizePuzzle, fromJSON,
    randomQueens, growRegions,
  };
});
