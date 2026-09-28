// Small canvas time-series plots for the V8 dashboard (no external libraries).
//
// Layers are drawn in order. Missing data is never drawn as values: 'line' and 'step'
// layers break at null values and at explicit gap intervals; 'nodata' layers shade
// periods without fresh telemetry.

function cssVar(name, fallback) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

export class Plot {
  constructor(canvas, opts = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.opts = Object.assign({ yMin: 0, yMax: 100, yLabel: '', xLabel: 's', padL: 46, padR: 10, padT: 10, padB: 22 }, opts);
    this.x0 = 0; this.x1 = 30;
    this.layers = [];
    this.cursor = null;
    this.hover = null;
    canvas.addEventListener('mousemove', (e) => {
      const r = canvas.getBoundingClientRect();
      this.hover = { px: e.clientX - r.left, py: e.clientY - r.top };
      this.onHover && this.onHover(this.pxToX(this.hover.px));
      this.draw();
    });
    canvas.addEventListener('mouseleave', () => { this.hover = null; this.draw(); });
  }

  setX(x0, x1) { this.x0 = x0; this.x1 = Math.max(x1, x0 + 1e-3); }
  setY(yMin, yMax) { this.opts.yMin = yMin; this.opts.yMax = yMax; }
  setLayers(layers) { this.layers = layers; }

  resize() {
    const dpr = window.devicePixelRatio || 1;
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    if (this.canvas.width !== Math.round(w * dpr) || this.canvas.height !== Math.round(h * dpr)) {
      this.canvas.width = Math.round(w * dpr);
      this.canvas.height = Math.round(h * dpr);
    }
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.w = w; this.h = h;
  }

  xToPx(x) { const o = this.opts; return o.padL + (x - this.x0) / (this.x1 - this.x0) * (this.w - o.padL - o.padR); }
  pxToX(px) { const o = this.opts; return this.x0 + (px - o.padL) / (this.w - o.padL - o.padR) * (this.x1 - this.x0); }
  yToPx(y) { const o = this.opts; return o.padT + (1 - (y - o.yMin) / (o.yMax - o.yMin)) * (this.h - o.padT - o.padB); }

  draw() {
    if (!this.canvas.isConnected) return;
    this.resize();
    const c = this.ctx, o = this.opts;
    const fg = cssVar('--fg-muted', '#667'), grid = cssVar('--grid', '#e3e6ea');
    c.clearRect(0, 0, this.w, this.h);
    c.font = '11px system-ui, sans-serif';
    c.strokeStyle = grid; c.fillStyle = fg; c.lineWidth = 1;
    const yTicks = 4;
    for (let i = 0; i <= yTicks; i++) {
      const y = o.yMin + (o.yMax - o.yMin) * i / yTicks, py = this.yToPx(y);
      c.beginPath(); c.moveTo(o.padL, py); c.lineTo(this.w - o.padR, py); c.stroke();
      c.textAlign = 'right'; c.textBaseline = 'middle';
      c.fillText(fmt(y), o.padL - 4, py);
    }
    const span = this.x1 - this.x0;
    const step = niceStep(span / 6);
    c.textAlign = 'center'; c.textBaseline = 'top';
    for (let x = Math.ceil(this.x0 / step) * step; x <= this.x1; x += step) {
      const px = this.xToPx(x);
      c.beginPath(); c.moveTo(px, o.padT); c.lineTo(px, this.h - o.padB); c.stroke();
      c.fillText(fmt(x) + (o.xLabel ? ' ' + o.xLabel : ''), px, this.h - o.padB + 4);
    }
    c.save();
    c.beginPath(); c.rect(o.padL, o.padT, this.w - o.padL - o.padR, this.h - o.padT - o.padB); c.clip();
    for (const L of this.layers) this.drawLayer(L);
    if (this.cursor !== null) {
      const px = this.xToPx(this.cursor);
      c.strokeStyle = cssVar('--accent', '#2b6cb0'); c.lineWidth = 1.5;
      c.beginPath(); c.moveTo(px, o.padT); c.lineTo(px, this.h - o.padB); c.stroke();
    }
    c.restore();
    if (o.yLabel) {
      c.save(); c.fillStyle = fg; c.translate(11, (this.h - o.padB + o.padT) / 2); c.rotate(-Math.PI / 2);
      c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(o.yLabel, 0, 0); c.restore();
    }
    if (this.hover && this.hoverText) {
      const t = this.hoverText(this.pxToX(this.hover.px));
      if (t) {
        c.fillStyle = cssVar('--tooltip-bg', 'rgba(20,24,31,0.88)');
        const lines = t.split('\n');
        const wmax = Math.max(...lines.map((l) => c.measureText(l).width)) + 10;
        const bx = Math.min(this.hover.px + 10, this.w - wmax - 4), by = 6;
        c.fillRect(bx, by, wmax, 14 * lines.length + 6);
        c.fillStyle = cssVar('--tooltip-fg', '#fff'); c.textAlign = 'left'; c.textBaseline = 'top';
        lines.forEach((l, i) => c.fillText(l, bx + 5, by + 4 + 14 * i));
      }
    }
  }

  drawLayer(L) {
    const c = this.ctx, o = this.opts;
    const color = L.color || cssVar('--series-1', '#2b6cb0');
    c.strokeStyle = color; c.fillStyle = color; c.lineWidth = L.width || 1.6;
    c.setLineDash(L.dash || []);
    const top = o.padT, bot = this.h - o.padB;
    switch (L.type) {
      case 'band': {                       // [{from, to}] shaded intervals
        c.globalAlpha = L.alpha || 0.14;
        for (const b of L.data) {
          const a = this.xToPx(b.from), z = this.xToPx(b.to === null || b.to === undefined ? this.x1 : b.to);
          c.fillRect(a, top, Math.max(1, z - a), bot - top);
        }
        c.globalAlpha = 1;
        if (L.label) { c.font = '10px system-ui'; c.textBaseline = 'top'; c.textAlign = 'left';
          for (const b of L.data) c.fillText(L.label, this.xToPx(b.from) + 3, top + 2); }
        break;
      }
      case 'nodata': {                     // hatched: no fresh data
        c.save(); c.globalAlpha = 0.35; c.strokeStyle = cssVar('--nodata', '#9aa3ad'); c.lineWidth = 1;
        for (const b of L.data) {
          const a = this.xToPx(b.from), z = this.xToPx(b.to === null || b.to === undefined ? this.x1 : b.to);
          c.beginPath(); c.rect(a, top, Math.max(1, z - a), bot - top); c.clip();
          for (let x = a - (bot - top); x < z; x += 7) { c.beginPath(); c.moveTo(x, bot); c.lineTo(x + (bot - top), top); c.stroke(); }
        }
        c.restore();
        if (L.label) { c.fillStyle = cssVar('--fg-muted', '#667'); c.font = '10px system-ui'; c.textBaseline = 'bottom';
          for (const b of L.data) if (this.xToPx(b.to ?? this.x1) - this.xToPx(b.from) > 40) c.fillText(L.label, this.xToPx(b.from) + 3, bot - 2); }
        break;
      }
      case 'hline': {
        const py = this.yToPx(L.y);
        c.beginPath(); c.moveTo(o.padL, py); c.lineTo(this.w - o.padR, py); c.stroke();
        if (L.label) { c.font = '10px system-ui'; c.textAlign = 'right'; c.textBaseline = 'bottom'; c.fillText(L.label, this.w - o.padR - 2, py - 2); }
        break;
      }
      case 'vlines': {                     // [{x, label}]
        c.font = '10px system-ui'; c.textAlign = 'left'; c.textBaseline = 'top';
        for (const v of L.data) {
          const px = this.xToPx(v.x);
          c.beginPath(); c.moveTo(px, top); c.lineTo(px, bot); c.stroke();
          if (v.label) c.fillText(v.label, px + 2, top + 2 + (v.row || 0) * 11);
        }
        break;
      }
      case 'step':                         // [{x, y}] hold value until next point; null breaks
      case 'line': {
        let pen = false, lastPy = null;
        c.beginPath();
        for (const p of L.data) {
          if (p.y === null || p.y === undefined || p.gapBefore) { pen = false; if (p.y === null || p.y === undefined) continue; }
          const px = this.xToPx(p.x), py = this.yToPx(p.y);
          if (!pen) { c.moveTo(px, py); pen = true; }
          else if (L.type === 'step') { c.lineTo(px, lastPy); c.lineTo(px, py); }
          else c.lineTo(px, py);
          lastPy = py;
        }
        c.stroke();
        if (L.markers) for (const p of L.data) if (p.y !== null && p.y !== undefined) {
          c.beginPath(); c.arc(this.xToPx(p.x), this.yToPx(p.y), L.markers, 0, 2 * Math.PI); c.fill();
        }
        break;
      }
      case 'points': {
        const r = L.radius || 2.2;
        for (const p of L.data) if (p.y !== null && p.y !== undefined) {
          c.beginPath(); c.arc(this.xToPx(p.x), this.yToPx(p.y), r, 0, 2 * Math.PI); c.fill();
        }
        break;
      }
      case 'envelope': {                   // [{x, lo, hi}] min/max per display bucket; gapBefore breaks
        c.globalAlpha = 0.9;
        for (const p of L.data) {
          const px = this.xToPx(p.x), a = this.yToPx(p.hi), b = this.yToPx(p.lo);
          c.fillRect(px - 0.75, a, 1.5, Math.max(1, b - a));
        }
        c.globalAlpha = 1;
        break;
      }
      case 'ticks': {                      // [{x, label}] short markers at the top (e.g. sequence gaps)
        c.font = '10px system-ui'; c.textAlign = 'center'; c.textBaseline = 'top';
        for (const t of L.data) {
          const px = this.xToPx(t.x);
          c.beginPath(); c.moveTo(px, top); c.lineTo(px, top + 10); c.stroke();
          if (t.label) c.fillText(t.label, px, top + 11);
        }
        break;
      }
    }
    c.setLineDash([]);
  }
}

function niceStep(raw) {
  const p = Math.pow(10, Math.floor(Math.log10(Math.max(raw, 1e-9))));
  const n = raw / p;
  return (n < 1.5 ? 1 : n < 3.5 ? 2 : n < 7.5 ? 5 : 10) * p;
}

function fmt(v) {
  const a = Math.abs(v);
  if (a >= 100) return v.toFixed(0);
  if (a >= 10) return v.toFixed(1).replace(/\.0$/, '');
  return v.toFixed(2).replace(/\.?0+$/, '');
}

/** Lane timeline of labelled events: lanes = [{name, events:[{x, label, tone}]}] */
export class Timeline {
  constructor(canvas) {
    this.canvas = canvas; this.ctx = canvas.getContext('2d');
    this.x0 = 0; this.x1 = 30; this.lanes = []; this.padL = 118; this.padR = 10;
  }
  setX(x0, x1) { this.x0 = x0; this.x1 = Math.max(x1, x0 + 1e-3); }
  xToPx(x) { return this.padL + (x - this.x0) / (this.x1 - this.x0) * (this.w - this.padL - this.padR); }
  draw() {
    if (!this.canvas.isConnected) return;
    const dpr = window.devicePixelRatio || 1;
    const w = this.canvas.clientWidth, laneH = 24, h = Math.max(40, this.lanes.length * laneH + 8);
    this.canvas.style.height = h + 'px';
    this.canvas.width = Math.round(w * dpr); this.canvas.height = Math.round(h * dpr);
    const c = this.ctx; c.setTransform(dpr, 0, 0, dpr, 0, 0); this.w = w;
    c.clearRect(0, 0, w, h);
    c.font = '11px system-ui, sans-serif';
    this.lanes.forEach((lane, i) => {
      const y = 4 + i * laneH;
      c.fillStyle = cssVar('--lane', 'rgba(127,127,127,0.07)'); c.fillRect(this.padL, y, w - this.padL - this.padR, laneH - 4);
      c.fillStyle = cssVar('--fg-muted', '#667'); c.textAlign = 'right'; c.textBaseline = 'middle';
      c.fillText(lane.name, this.padL - 6, y + (laneH - 4) / 2);
      let lastLabelEnd = -1e9;
      for (const e of lane.events) {
        if (e.x === null || e.x === undefined) continue;
        const px = this.xToPx(e.x);
        c.fillStyle = cssVar('--tone-' + (e.tone || 'info'), '#2b6cb0');
        c.beginPath(); c.moveTo(px, y + 2); c.lineTo(px + 5, y + 10); c.lineTo(px, y + 18); c.lineTo(px - 5, y + 10); c.closePath(); c.fill();
        if (e.label && px + 8 > lastLabelEnd) {
          c.fillStyle = cssVar('--fg', '#222'); c.textAlign = 'left';
          c.fillText(e.label, px + 8, y + 10);
          lastLabelEnd = px + 12 + c.measureText(e.label).width;
        }
      }
    });
  }
}
