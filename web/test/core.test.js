// Run with: node --test web/test
const test = require('node:test');
const assert = require('node:assert');
const core = require('../js/hexqueen-core.js');

function solutionCells(sol) { return new Set(sol); }

test('every radius 1-7 admits a queen layout', () => {
  const rng = core.makeRng('layouts');
  for (let r = 1; r <= 7; r++) {
    const g = core.geometry(r);
    const q = core.randomQueens(g, rng);
    assert.ok(q, 'radius ' + r);
    const seen = [new Set(), new Set(), new Set()];
    for (const i of q) {
      const c = g.cells[i];
      for (const [a, v] of [[0, c.x], [1, c.y], [2, c.z]]) {
        assert.ok(!seen[a].has(v), 'queens share a line');
        seen[a].add(v);
      }
    }
  }
});

test('deductions never rule out a cell used by any real solution', () => {
  const rng = core.makeRng('soundness');
  let checked = 0;
  for (let trial = 0; trial < 120; trial++) {
    const r = 2 + (trial % 3);
    const g = core.geometry(r);
    const queens = core.randomQueens(g, rng);
    const region = core.growRegions(g, queens, rng);
    // Random region layouts usually have several solutions: perfect for soundness checks.
    const sols = core.findSolutions(g, region, 50);
    const live = new Set();
    for (const s of sols) for (const c of s) live.add(c);
    const ctx = core.makeContext(g, region);
    const res = core.logicalSolve(ctx, { maxTier: 6, record: true });
    for (const step of res.steps) {
      for (const c of step.elim) {
        // A cell may be eliminated only if no solution uses it.
        assert.ok(!live.has(c) || sols.length === 0, `tier ${step.tier} (${step.kind}) eliminated a solution cell`);
      }
    }
    if (sols.length === 1) assert.ok(!res.contradiction);
    checked += res.steps.length;
  }
  assert.ok(checked > 200);
});

test('generated puzzles are unique, logical and match brute force', () => {
  for (const level of Object.keys(core.LEVELS)) {
    for (let s = 0; s < 5; s++) {
      const p = core.generate({ level, seed: 'test-' + s });
      const g = core.geometry(p.radius);
      assert.strictEqual(p.radius, core.LEVELS[level].radius);
      assert.ok(p.unique, `${level}/${s} unique`);
      assert.ok(p.logical, `${level}/${s} logical`);
      const sols = core.findSolutions(g, p.region, 2);
      assert.strictEqual(sols.length, 1);
      const ctx = core.makeContext(g, p.region);
      const res = core.logicalSolve(ctx, { maxTier: 6 });
      const fromLogic = [];
      for (let i = 0; i < g.N; i++) if (res.open[i] === 2) fromLogic.push(i);
      assert.deepStrictEqual(new Set(fromLogic), solutionCells(sols[0]));
      assert.ok(p.onTarget, `${level}/${s} difficulty band`);
      const lvl = core.LEVELS[level];
      assert.ok(p.tier >= lvl.minTier && p.tier <= lvl.maxTier, `${level}/${s} tier ${p.tier}`);
    }
  }
});

test('regions are contiguous and every cell is assigned', () => {
  const p = core.generate({ level: 'hard', seed: 'contig' });
  const g = core.geometry(p.radius);
  for (let reg = 0; reg < g.n; reg++) {
    const cells = [];
    for (let i = 0; i < g.N; i++) if (p.region[i] === reg) cells.push(i);
    assert.ok(cells.length > 0);
    const seen = new Set([cells[0]]);
    const stack = [cells[0]];
    while (stack.length) {
      for (const j of g.neighbors[stack.pop()]) {
        if (j >= 0 && p.region[j] === reg && !seen.has(j)) { seen.add(j); stack.push(j); }
      }
    }
    assert.strictEqual(seen.size, cells.length, 'region ' + reg + ' contiguous');
  }
});

test('the same level and seed always give the same puzzle', () => {
  const a = core.generate({ level: 'medium', seed: 'repeat' });
  const b = core.generate({ level: 'medium', seed: 'repeat' });
  const c = core.generate({ level: 'medium', seed: 'other' });
  assert.deepStrictEqual(a.region, b.region);
  assert.notDeepStrictEqual(a.region, c.region);
});

test('imports the Python generator JSON format', () => {
  const p = core.generate({ level: 'easy', seed: 'json' });
  const g = core.geometry(p.radius);
  const cell_regions = {};
  const region_seeds = {};
  g.cells.forEach((c, i) => { cell_regions[`[${c.x}, ${c.y}, ${c.z}]`] = p.region[i] + 10; });
  p.solution.forEach((cell, reg) => { const c = g.cells[cell]; region_seeds[reg + 10] = [c.x, c.y, c.z]; });
  const imported = core.fromJSON({ grid_radius: p.radius, num_regions: g.n, region_seeds, cell_regions });
  assert.ok(imported.unique && imported.logical);
  assert.deepStrictEqual(new Set(imported.solution), new Set(p.solution));
  assert.throws(() => core.fromJSON({ grid_radius: 3, cell_regions: {} }), /no region/);
});
