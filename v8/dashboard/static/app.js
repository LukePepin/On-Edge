// On-Edge V8 dashboard. Display only: every control is a request to the acquisition daemon,
// which owns timing and recording. Plot refresh never affects acquisition.
import { deriveMode, controlState, motionLabel, outputLabel, updatesToCross, STREAM_STALE_MS } from './modes.js';
import { Plot, Timeline } from './plot.js';

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const f1 = (v, d = 1) => (v === null || v === undefined || Number.isNaN(v) ? '—' : Number(v).toFixed(d));
const WL = { ECC: 'ECC key generation', ZKP: 'two scalar multiplications (ZKP-cost proxy)' };

const S = {
  view: 'live', backend: null, info: null, localInfo: null,
  es: null, streamConnected: false, status: null, statusPerf: null,
  live: null,
  replay: { root: null, sessions: [], sid: null, session: null, aid: null, payload: null, cursor: null, playing: false,
            selected: new Set(), excl: null },
  campaigns: { list: [], preview: null, file: null },
  clientId: 'dash-' + Math.random().toString(36).slice(2, 10),
  log: [],
};
S.live = freshLive();

function freshLive() {
  return { upd: [], dev: [], tx: [], joints: [], robot: [], host: [], gaps: [], bad: [], attemptId: null, attemptT0: null };
}

// ------------------------------------------------------------------ backend
async function detectBackend() {
  try {
    const r = await fetch('/api/local/info');
    if (r.ok) {
      S.localInfo = await r.json();
      S.backend = { kind: 'dashboard', live: S.localInfo.live_available, liveBase: '/api/live' };
      return;
    }
  } catch (e) { /* not the dashboard server */ }
  S.backend = { kind: 'daemon', live: true, liveBase: '/api' };        // served by the Pi daemon itself
}

async function api(method, path, body) {
  const r = await fetch(path, { method, headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined });
  let data = null;
  try { data = await r.json(); } catch (e) { /* empty */ }
  if (!r.ok) throw new Error((data && data.error) || `${r.status} ${r.statusText}`);
  return data;
}
const live = (method, path, body) => api(method, `${S.backend.liveBase}/${path}`, body);
const operator = () => ($('operator').value || '').trim();

// ------------------------------------------------------------------ stream
function connectStream() {
  if (!S.backend.live) return;
  if (S.es) S.es.close();
  const es = new EventSource(`${S.backend.liveBase}/stream`);
  S.es = es;
  es.onopen = () => { S.streamConnected = true; };
  es.onerror = () => { S.streamConnected = false; };
  const on = (name, fn) => es.addEventListener(name, (m) => { try { fn(JSON.parse(m.data)); } catch (e) { console.error(e); } });
  on('hello', (info) => { S.info = info; });
  on('status', (st) => { S.status = st; S.statusPerf = performance.now(); onStatus(st); });
  on('device', (ev) => onDevice(ev.data));
  on('joint', (ev) => { S.live.joints.push(ev.data); });
  on('tx', (ev) => { S.live.tx.push(ev.data); addLog(`host ${ev.data.source} sent ${ev.data.cmd}${ev.data.ok ? '' : ' (FAILED)'} [${ev.data.purpose}]`, ev.data.ok ? '' : 'bad'); });
  on('robot', (ev) => { S.live.robot.push(ev.data); addLog(`controller ${ev.data.source} = ${ev.data.name}`, /STOP|FAULT|VIOLATION/.test(ev.data.name) ? 'warn' : ''); });
  on('host', (ev) => { S.live.host.push(ev.data); if (ev.data.event !== 'phase') addLog(`${ev.data.event}${ev.data.status ? ' ' + ev.data.status : ''}${ev.data.reason ? ': ' + ev.data.reason : ''}`); });
  on('runner', (ev) => addLog(`runner → ${ev.data.state}${ev.data.reason ? ' (' + ev.data.reason + ')' : ''}`, ev.data.state === 'HOLD' ? 'warn' : ''));
  on('session', (ev) => addLog(`session: ${ev.data.event}${ev.data.reason ? ' – ' + ev.data.reason : ''}`));
  on('link', (ev) => addLog(`link: ${ev.data.event}${ev.data.error ? ' – ' + ev.data.error : ''}`, ev.data.event === 'link_disconnected' ? 'bad' : ''));
  on('proxy_error', (d) => addLog(`dashboard proxy: ${d.error}`, 'bad'));
}

function onDevice(r) {
  const L = S.live;
  if (r.status !== 'ok') { L.bad.push(r); addLog(`device record ${r.status}${r.problems ? ': ' + r.problems.join('; ') : ''}`, 'bad'); }
  for (const c of r.cont || []) { L.gaps.push({ ...c, rx_mono_ns: r.rx_mono_ns }); addLog(`continuity: ${c.kind} ${JSON.stringify(c).slice(0, 90)}`, 'bad'); }
  if (r.status !== 'ok') return;
  if (r.kind === 'upd' || r.kind === 'legacy_upd') L.upd.push(r);
  else if (['cfg', 'cmd', 'out', 'err', 'boot', 'hello', 'legacy_ready'].includes(r.kind)) {
    L.dev.push(r);
    if (r.kind === 'cmd') addLog(`monitor processed ${r.f.cmd} (cycle ${r.f.cycle})`);
    if (r.kind === 'out') addLog(`monitor commanded D12 ${r.f.level ? 'HIGH' : 'LOW'} (cycle ${r.f.cycle}, trust ${f1(r.f.trust, 2)})`, r.f.level ? '' : 'warn');
    if (r.kind === 'cfg') addLog(`monitor configured: ${r.f.wl} α=${r.f.alpha} (trust 100, D12 high)`);
    if (r.kind === 'err') addLog(`monitor rejected input: ${r.f.code}`, 'bad');
    if (r.kind === 'boot') addLog(`monitor boot record: ${r.f.fw} ${r.f.ver} (${r.f.build})`, 'warn');
  }
}

function onStatus(st) {
  const cur = st.runner && st.runner.current;
  if (cur && cur.attempt_id !== S.live.attemptId) {
    S.live.attemptId = cur.attempt_id;
    S.live.attemptT0 = cur.t_start_mono_ns;
  }
  trimLive(st.t_mono_ns);
  renderHeader();
  if (S.view === 'live') renderLivePanels();
}

function trimLive(nowNs) {
  const keep = nowNs - 180e9;
  const L = S.live;
  for (const k of ['upd', 'dev', 'tx', 'robot', 'host', 'gaps', 'bad']) L[k] = L[k].filter((x) => (x.rx_mono_ns ?? x.t_mono_ns ?? x.t_write_end_mono_ns ?? x.t_request_mono_ns) >= keep);
  L.joints = L.joints.filter((x) => x.rx_mono_ns >= keep);
}

function piNowNs() {
  if (!S.status) return null;
  return S.status.t_mono_ns + (performance.now() - S.statusPerf) * 1e6;
}

function addLog(text, cls = '') {
  const t = new Date().toLocaleTimeString();
  S.log.unshift({ t, text, cls });
  S.log = S.log.slice(0, 300);
  if (S.view === 'live') renderLog();
}

// ------------------------------------------------------------------ header & mode
function currentMode() {
  const st = S.status;
  const age = S.statusPerf === null ? null : performance.now() - S.statusPerf;
  return deriveMode({
    view: S.view === 'replay' ? 'replay' : 'live', liveAvailable: S.backend && S.backend.live,
    streamConnected: S.streamConnected, lastStatusAgeMs: age, daemonSimulated: st ? st.simulated : null,
    deviceFreshness: st ? st.link.freshness : null,
    replayOrigin: S.replay.session ? S.replay.session.meta.data_origin : (S.replay.root === 'sim' ? 'software_simulation' : 'hardware'),
  });
}

function renderHeader() {
  const m = currentMode();
  const b = $('modeBadge');
  b.textContent = m.badge; b.className = 'badge ' + m.tone;
  $('modeDetail').textContent = m.detail + (S.view === 'campaigns' ? ' Campaign selection uses the live acquisition host.' : '');
  const st = S.status;
  const inds = [];
  const age = S.statusPerf === null ? null : performance.now() - S.statusPerf;
  inds.push(ind('Pi daemon', !S.backend.live ? 'not configured' : (S.streamConnected && age !== null && age < STREAM_STALE_MS ? 'connected' : 'no stream'),
                !S.backend.live ? '' : (S.streamConnected && age !== null && age < STREAM_STALE_MS ? 'ok' : 'bad')));
  if (st) {
    const L = st.link;
    inds.push(ind('Monitor', `${L.connected ? L.freshness : 'disconnected'}${L.age_ms !== null && L.age_ms !== undefined ? ' ' + f1(L.age_ms, 0) + ' ms' : ''}`,
                  L.connected && L.freshness === 'fresh' ? 'ok' : 'bad'));
    const R = st.robot;
    inds.push(ind('Joints', R.capabilities.joint_telemetry ? `${R.joint_freshness}${R.joint_age_ms !== null && R.joint_age_ms !== undefined ? ' ' + f1(R.joint_age_ms, 0) + ' ms' : ''}` : 'unavailable',
                  !R.capabilities.joint_telemetry ? '' : R.joint_freshness === 'fresh' ? 'ok' : 'warn'));
    const rec = st.recorder;
    inds.push(ind('Recording', `${rec.healthy ? 'ok' : 'ERROR'} · ${rec.session_id ? 'session open' : 'daemon log only'}`, rec.healthy ? 'ok' : 'bad'));
    inds.push(ind('Operator', st.runner.operator_present ? 'present' : 'no heartbeat', st.runner.operator_present ? 'ok' : 'warn'));
  }
  $('indicators').innerHTML = inds.join('');
}
const ind = (k, v, cls) => `<span class="ind ${cls}"><b>${esc(k)}</b> ${esc(v)}</span>`;

// ------------------------------------------------------------------ live panels
function renderLivePanels() {
  const st = S.status;
  if (!st) return;
  const run = st.runner, m = currentMode();
  const sess = run.session;
  const p = run.progress;
  const cur = run.current;
  let h = '<h3>Campaign</h3>';
  if (!sess) h += `<div class="kv"><span class="k">State</span><span class="state">${esc(run.state)}</span></div><p class="hint">No campaign session open. Select one on the Campaigns tab.</p>`;
  else {
    h += `<div><b>${esc(sess.title)}</b> <span class="pill ${sess.kind}">${esc(sess.kind.toUpperCase())}</span>
          ${sess.simulated ? '<span class="pill sim">SIMULATED</span>' : ''} <span class="pill ${sess.campaign_status}">${esc(sess.campaign_status)}</span></div>
          <div class="hint">${esc(sess.session_id)} · ${esc(sess.procedure)} procedure</div>
          ${sess.kind === 'demonstration' ? '<p class="hint"><b>Demonstration preset — not a complete experimental campaign.</b></p>' : ''}
          <div class="progress"><div style="width:${p ? (100 * (p.completed + p.skipped) / Math.max(1, p.n_trials)) : 0}%"></div></div>
          <div class="kv"><span class="k">State</span><span class="state">${esc(run.state)}</span>
          <span class="k">Progress</span><span>${p.completed} completed · ${p.skipped} skipped · ${p.n_trials} planned · ${p.attempts} attempts</span>
          ${run.state_reason ? `<span class="k">Reason</span><span>${esc(run.state_reason)}</span>` : ''}</div>`;
    if (cur) h += trialBox('Current attempt', cur, cur.phase);
    else if (run.next_trial) h += trialBox('Next planned trial', run.next_trial, null);
    if (run.last_attempt) h += `<div class="hint">Last: ${esc(run.last_attempt.attempt_id)} → <b>${esc(run.last_attempt.status)}</b>${run.last_attempt.reason ? ' – ' + esc(run.last_attempt.reason) : ''}</div>`;
  }
  $('campaignCard').innerHTML = h;

  const c = (a) => controlState(a, m, run);
  let ch = '<h3>Campaign controls</h3>';
  ch += `<div class="row"><button id="bPause" ${dis(c('pause'))}>Pause after this trial</button>
         <button id="bResume" ${dis(c('resume'))}>Resume</button>
         <button id="bAbort" class="danger" ${dis(c('abort'))}>Abort campaign…</button></div>`;
  if (run.state === 'AWAITING_CONFIRMATION') {
    ch += `<div class="hold"><b>Confirm the next trial</b> (${esc(run.next_trial && run.next_trial.trial_id)})<br>
          <label class="check"><input type="checkbox" class="cchk" value="work area clear"> Work area clear</label>
          <label class="check"><input type="checkbox" class="cchk" value="teach-pendant e-stop within reach"> Teach-pendant E-stop within reach</label>
          <label class="check"><input type="checkbox" class="cchk" value="robot state reviewed"> Robot state reviewed (safety mode, program)</label>
          <button id="bConfirm" class="primary" ${dis(c('confirm'))}>Start ${esc(run.next_trial && run.next_trial.trial_id)}</button>
          <div class="hint">Starting re-arms the monitor (configuration raises D12), then runs the trial procedure.</div></div>`;
  }
  if (run.state === 'HOLD' && run.hold) {
    ch += `<div class="hold"><b>Operator decision required</b><br>${esc(run.hold.reason)}
           ${run.hold.warnings ? '<ul class="warnlist">' + run.hold.warnings.map((w) => `<li>${esc(w.code)}</li>`).join('') + '</ul>' : ''}
           <div class="row">${run.hold.allowed.map((d) => `<button data-decide="${d}" ${dis(c('decide'))}>${esc(d)}</button>`).join('')}</div>
           <div class="hint">retry = new attempt of the same planned trial (the failed attempt is kept) · skip = mark this trial skipped · continue = accept and go on</div></div>`;
  }
  $('controlsCard').innerHTML = ch;
  bindControls();

  const man = c('manual');
  document.querySelectorAll('[data-manual]').forEach((b) => { b.disabled = !man.enabled; });
  $('manualNote').textContent = !man.enabled ? `Disabled: ${man.reason}` : (man.reason || '');
  $('noteBtn').disabled = !c('note').enabled;

  const R = st.robot, ml = motionLabel(R);
  let rh = `<h3>Robot</h3><div class="kv"><span class="k">Interface</span><span>${esc(S.info ? S.info.robot_interface : '?')}${R.capabilities.simulated ? ' (SIMULATED)' : ''}</span>
            <span class="k">Motion</span><span><span class="pill">${esc(ml.text)}</span></span>
            <span class="k">Safety mode</span><span>${esc(R.safety_mode ?? (R.capabilities.safety_mode ? 'no report yet' : 'unavailable'))}</span>
            <span class="k">Program</span><span>${R.program_running === null || R.program_running === undefined ? (R.capabilities.program_state ? 'no report yet' : 'unavailable') : R.program_running ? 'running' : 'not running'}</span>
            <span class="k">Monitor output</span><span>${esc(outputLabel(st.link.state.d12))}</span></div>`;
  if (R.capabilities.dashboard) {
    const rs = c('robot_state_cmd');
    rh += `<div class="row"><button data-dash="safetymode">safetymode?</button><button data-dash="programState">programState?</button><button data-dash="robotmode">robotmode?</button></div>
           <div class="row"><button data-dash="play" ${dis(rs)}>play…</button><button data-dash="unlock protective stop" ${dis(rs)}>unlock protective stop…</button></div>
           <div class="hint">State-changing commands need a reason and are recorded. The runner never unlocks protective stops by itself.</div>`;
  }
  $('robotCard').innerHTML = rh;
  document.querySelectorAll('[data-dash]').forEach((b) => b.addEventListener('click', () => dashCmd(b.dataset.dash)));

  renderNarration();
  renderMeasures();
  renderQuality();
}

const dis = (c) => (c.enabled ? '' : `disabled title="${esc(c.reason)}"`);

function trialBox(title, t, phase) {
  return `<h3>${esc(title)}</h3><div class="kv">
    <span class="k">Trial</span><span><b>${esc(t.trial_id)}</b>${t.attempt ? ' · attempt ' + t.attempt : ''}${t.attempt_id ? ' (' + esc(t.attempt_id) + ')' : ''}</span>
    <span class="k">Workload</span><span>${esc(t.workload)} – ${esc(WL[t.workload] || '')}</span>
    <span class="k">EWMA α</span><span>${esc(t.alpha)}</span>
    <span class="k">Injected failure</span><span>${t.failure_ms ? t.failure_ms + ' ms' : 'none (control)'}</span>
    <span class="k">Repetition</span><span>${esc(t.repetition)}</span>
    ${phase ? `<span class="k">Phase</span><span class="state">${esc(phase)}</span>` : ''}</div>`;
}

function bindControls() {
  const b = (id, fn) => { const e = $(id); if (e) e.addEventListener('click', fn); };
  b('bPause', () => act(() => live('POST', 'campaign/pause', { reason: 'operator pause', operator: operator() })));
  b('bResume', () => act(() => live('POST', 'campaign/resume', { operator: operator() })));
  b('bAbort', () => askReason('Abort campaign',
    '<p>This stops the <b>software sequence</b>: the trajectory goal is cancelled if one is active, no further ATTACK/RECOVER is sent, and the monitor is <b>not</b> reconfigured (configuration would raise D12).</p><p><b>It is not an emergency stop and does not confirm the robot is stationary.</b> Use the teach-pendant E-stop for safety.</p>',
    'Abort', (reason) => live('POST', 'campaign/abort', { reason, operator: operator() }), 'danger'));
  b('bConfirm', () => {
    const checks = [...document.querySelectorAll('.cchk')].filter((x) => x.checked).map((x) => x.value);
    if (checks.length < 3) { alertBox('Confirm all three checks before starting the trial.'); return; }
    act(() => live('POST', 'campaign/confirm', { operator: operator(), checks }));
  });
  document.querySelectorAll('[data-decide]').forEach((btn) => btn.addEventListener('click', () =>
    askReason(`Decision: ${btn.dataset.decide}`, '<p>The decision and reason are recorded in the session log.</p>', btn.dataset.decide,
      (reason) => live('POST', 'campaign/decision', { decision: btn.dataset.decide, reason, operator: operator() }))));
}

function dashCmd(cmd) {
  const readOnly = ['safetymode', 'programState', 'robotmode'].includes(cmd);
  const run = async (reason) => { const r = await live('POST', 'robot/dashboard', { cmd, reason, operator: operator() }); addLog(`dashboard ${cmd}: ${r.response}`); };
  if (readOnly) act(() => run(''));
  else askReason(`Robot command: ${cmd}`, `<p>Sends <code>${esc(cmd)}</code> to the UR dashboard server. Only use it when the cell is clear and you intend the robot state to change.</p>`, 'Send', run, 'warn');
}

function manualCmd(cmd) {
  const cur = S.status && S.status.runner.current;
  const body = { cmd, operator: operator(), confirm_departure: !!cur };
  if (cmd === 'CONFIG') { body.workload = $('manWl').value; body.alpha = parseFloat($('manAlpha').value); }
  askReason(`Manual ${cmd}`,
    `<p>Manual commands are recorded and marked as departures from the selected procedure.</p>${cur ? `<p><b>An attempt (${esc(cur.attempt_id)}) is running.</b> Sending now changes that attempt and flags it for review.</p>` : ''}${cmd === 'CONFIG' ? '<p>Configuration resets trust to 100 and commands D12 HIGH.</p>' : ''}`,
    `Send ${cmd}`, (reason) => live('POST', 'manual', { ...body, reason }), 'warn');
}

// ------------------------------------------------------------------ narration & measures
function curAttemptRecords() {
  const L = S.live, t0 = L.attemptT0;
  if (t0 === null || t0 === undefined) return null;
  const since = (x) => (x.rx_mono_ns ?? x.t_write_end_mono_ns ?? x.t_request_mono_ns ?? x.t_mono_ns) >= t0;
  return { upd: L.upd.filter(since), dev: L.dev.filter(since), tx: L.tx.filter(since), robot: L.robot.filter(since), host: L.host.filter(since), gaps: L.gaps.filter(since) };
}

function renderNarration() {
  const st = S.status, run = st.runner, out = [];
  const say = (t, cls = '') => out.push(`<p class="${cls}">${t}</p>`);
  if (st.simulated) say('<b>Software simulation.</b> The monitor, serial link and robot are models; nothing here is hardware evidence.');
  if (!st.link.connected) say('The trust monitor\'s serial link is <b>not connected</b>. The dashboard will not show trust data until it reconnects.');
  const cur = run.current;
  if (!cur) {
    const map = { IDLE: 'No campaign is running.', PAUSED: 'The campaign is paused between trials.', HOLD: 'The campaign is holding for an operator decision.',
                  AWAITING_CONFIRMATION: 'Waiting for the operator to confirm the next robot trial.', COMPLETED: 'The campaign has finished.', ABORTED: 'The campaign was aborted.' };
    say(map[run.state] || `Runner state: ${esc(run.state)}.`);
  } else {
    say(`Trial <b>${esc(cur.trial_id)}</b> (attempt ${cur.attempt}): ${esc(WL[cur.workload] || cur.workload)}, α = ${cur.alpha}, ` +
        `${cur.failure_ms ? 'injected failure ' + cur.failure_ms + ' ms' : 'no injected failure (control)'}.`);
    const r = curAttemptRecords() || { upd: [], dev: [], tx: [], robot: [], host: [] };
    const phaseText = {
      configure: 'Configuring the monitor: this resets trust to 100, clears attack mode and commands D12 high.',
      baseline: 'Baseline: the workload runs and each update uses a normal observation of 100, so trust stays at 100.',
      inject: 'The host is sending ATTACK. The monitor reads commands only between workload cycles, so processing can wait up to one cycle.',
      failure_window: 'Injected failure active: each update that starts while attack mode is set uses a zero observation.',
      observe: 'RECOVER sent. Attack mode clears at the next loop boundary; trust recovers, but D12 stays low (latched) until the next configuration.',
      approach: 'Robot moving to the start pose (phase 1).', settle: 'Waiting for the arm to settle at the start pose.',
      sweep: 'Robot sweep started (phase 2).', confirm_moving: 'Confirming on fresh joint telemetry that the arm is moving before any injection.',
      pre_injection: 'Arm confirmed moving; waiting the planned delay before injection.',
      await_trajectory_end: 'Waiting for the trajectory to finish or be stopped by the controller.',
      waiting_for_program: 'Waiting for the robot program: press Play on the teach pendant if it is paused.',
      no_injection_control: 'Control trial: no ATTACK is sent.',
    };
    if (!cur.failure_ms && cur.phase === 'observe') say('Observation period of a control trial: no ATTACK or RECOVER is sent, so trust should remain at 100.');
    else if (phaseText[cur.phase]) say(phaseText[cur.phase]);
    const att = r.dev.find((d) => d.kind === 'cmd' && d.f.cmd === 'ATTACK' && d.f.prev === 0);
    if (att) {
      const attacked = r.upd.filter((u) => u.f.attack === 1 && u.rx_mono_ns >= att.rx_mono_ns);
      const n = updatesToCross(cur.alpha);
      const lastU = r.upd[r.upd.length - 1];
      say(`The monitor processed ATTACK at cycle ${att.f.cycle}. ${attacked.length} attacked update(s) so far; trust ${lastU ? f1(lastU.f.trust, 2) : '—'}.`);
      say(`MODEL: from 100, α = ${cur.alpha} needs ${n} zero-observation update(s) to fall below 30.`, 'model');
    }
    const cross = r.upd.find((u) => u.f.below === 1);
    if (cross) say(`Trust fell below 30 at cycle ${cross.f.cycle} (trust ${f1(cross.f.trust, 2)}): the firmware reports commanding <b>D12 LOW</b>. The electrical transition itself is not measured by this software.`);
    const sg = r.robot.find((x) => x.source === 'safety_mode' && /SAFEGUARD/.test(x.name));
    if (sg) say('The robot controller reported a <b>safeguard stop</b> (time of host receipt). Standstill is judged afterwards from fresh joint telemetry with the declared criterion.');
  }
  if (st.robot.capabilities.joint_telemetry && st.robot.joint_freshness !== 'fresh') say(`Joint telemetry is <b>${esc(st.robot.joint_freshness)}</b>: motion is unknown, not zero.`);
  $('narration').innerHTML = out.join('');
}

function renderMeasures() {
  const r = curAttemptRecords();
  if (!r) { $('liveMeasures').innerHTML = '<p class="hint">No attempt yet.</p>'; return; }
  const ended = !(S.status.runner.current);
  const att = r.dev.find((d) => d.kind === 'cmd' && d.f.cmd === 'ATTACK' && d.f.prev === 0);
  const cross = r.upd.find((u) => u.f.below === 1);
  const outLow = r.dev.find((d) => d.kind === 'out' && d.f.level === 0);
  const txA = r.tx.find((t) => t.purpose === 'trial_attack' && t.ok);
  const rows = [];
  const add = (k, v, clk) => rows.push(`<span class="k">${esc(k)}</span><span>${v} <span class="hint">${esc(clk || '')}</span></span>`);
  add('Updates this attempt', r.upd.length);
  if (att && cross && att.epoch === cross.epoch) add('ATTACK processed → trust < 30', f1((cross.t_dev_us - att.t_dev_us) / 1000, 1) + ' ms', 'device clock');
  if (att && outLow && att.epoch === outLow.epoch) add('ATTACK processed → D12 LOW command', f1((outLow.t_dev_us - att.t_dev_us) / 1000, 1) + ' ms', 'device clock');
  if (txA && cross) add('host ATTACK sent → crossing report received', f1((cross.rx_mono_ns - txA.t_write_end_mono_ns) / 1e6, 1) + ' ms', 'host clock');
  const per = [];
  for (let i = 1; i < r.upd.length; i++) if (r.upd[i].f.cycle === r.upd[i - 1].f.cycle + 1 && r.upd[i].t0_dev_us) per.push((r.upd[i].t0_dev_us - r.upd[i - 1].t0_dev_us) / 1000);
  if (per.length) add('Device loop period (median)', f1(per.sort((a, b) => a - b)[Math.floor(per.length / 2)], 2) + ' ms', 'device clock');
  if (r.gaps.length) add('Continuity events', `<b style="color:var(--tone-bad)">${r.gaps.length}</b>`);
  $('liveMeasures').innerHTML = (ended ? `<p class="hint">Last attempt ${esc(S.live.attemptId)} (ended). Open it in Replay for the recorded summary.</p>` : '') + `<div class="kv">${rows.join('')}</div>`;
}

function renderQuality() {
  const st = S.status, L = st.link, c = L.counters || {}, cont = L.continuity || {}, rec = st.recorder, bus = st.bus;
  const row = (k, v, bad) => `<span class="k">${esc(k)}</span><span ${bad ? 'style="color:var(--tone-bad);font-weight:650"' : ''}>${esc(v)}</span>`;
  $('quality').innerHTML = `<div class="kv">
    ${row('Monitor link', L.connected ? `${L.description || ''}` : `DISCONNECTED ${L.last_error || ''}`, !L.connected)}
    ${row('Firmware', L.identity ? `${L.identity.fw || '?'} ${L.identity.ver || ''} ${L.identity.build ? '(' + L.identity.build + ')' : ''}` : 'not identified yet', false)}
    ${row('Protocol', L.protocol || '—', L.protocol === 'legacy')}
    ${row('Records received', c.lines || 0)}
    ${row('Missing (sequence)', cont.missing_records || 0, cont.missing_records > 0)}
    ${row('Malformed / invalid', c.not_ok || 0, c.not_ok > 0)}
    ${row('Device resets', cont.resets || 0, cont.resets > 0)}
    ${row('Disconnects', L.disconnects || 0, L.disconnects > 0)}
    ${row('Recorder', rec.healthy ? `ok · ${rec.records_written} records · queue ${rec.queue_depth}` : 'ERROR: ' + (rec.errors || []).join('; '), !rec.healthy)}
    ${row('Disk free', rec.disk_free_bytes ? (rec.disk_free_bytes / 1e9).toFixed(1) + ' GB' : '?', rec.disk_free_bytes && rec.disk_free_bytes < 1e9)}
    ${row('Display events dropped', bus.dropped_for_display || 0)}
    </div><p class="hint">Display decimation never changes the recorded data.</p>`;
}

function renderLog() {
  $('log').innerHTML = S.log.slice(0, 120).map((l) => `<div class="${l.cls}">${esc(l.t)} ${esc(l.text)}</div>`).join('');
}

// ------------------------------------------------------------------ plots
const P = {};
function makePlots() {
  P.trust = new Plot($('pTrust'), { yMin: 0, yMax: 105, yLabel: 'trust' });
  P.exec = new Plot($('pExec'), { yMin: 0, yMax: 300, yLabel: 'ms' });
  P.joint = new Plot($('pJoint'), { yMin: 0, yMax: 1, yLabel: 'rad/s' });
  P.tl = new Timeline($('tLive'));
  P.rTrust = new Plot($('rTrust'), { yMin: 0, yMax: 105, yLabel: 'trust' });
  P.rExec = new Plot($('rExec'), { yMin: 0, yMax: 300, yLabel: 'ms' });
  P.rJoint = new Plot($('rJoint'), { yMin: 0, yMax: 1, yLabel: 'rad/s' });
  P.rTl = new Timeline($('tReplay'));
  P.cTrust = new Plot($('cTrust'), { yMin: 0, yMax: 105, yLabel: 'trust', xLabel: 's' });
  $('legTrust').innerHTML = [['--series-1', 'trust (device reports, at host receipt)'], ['--thr', 'threshold 30 (firmware: trust < 30)'],
    ['--attack', 'device attack mode (ATTACK→RECOVER processed)'], ['--tone-out', 'D12 command (firmware report)'], ['--tone-host', 'host command sent'],
    ['--tone-bad', 'sequence gap / invalid record']].map(([v, t]) => `<span><i style="background:var(${v})"></i>${t}</span>`).join('');
}

function col(v) { return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }

/** Build plot layers from records. tOf(ns) -> seconds on the plot axis. */
function buildLayers(rec, tOf, crit, x1) {
  const upd = rec.upd.map((u) => ({ x: tOf(u.rx_mono_ns), y: u.f.trust, gapBefore: !!(u.cont && u.cont.length) }));
  const bands = [];
  let open = null;
  for (const d of rec.dev) {
    if (d.kind === 'cmd' && d.f.cmd === 'ATTACK' && d.f.prev === 0) open = tOf(d.rx_mono_ns);
    if (d.kind === 'cmd' && d.f.cmd === 'RECOVER' && d.f.prev === 1 && open !== null) { bands.push({ from: open, to: tOf(d.rx_mono_ns) }); open = null; }
    if (d.kind === 'cfg' && open !== null) { bands.push({ from: open, to: tOf(d.rx_mono_ns) }); open = null; }
  }
  if (open !== null) bands.push({ from: open, to: x1 });
  const outs = rec.dev.filter((d) => d.kind === 'out').map((d) => ({ x: tOf(d.rx_mono_ns), label: d.f.level ? 'D12 HIGH cmd' : 'D12 LOW cmd', row: 1 }));
  const txs = rec.tx.filter((t) => t.ok && ['ATTACK', 'RECOVER', 'CONFIG'].includes(t.cmd)).map((t) => ({ x: tOf(t.t_write_end_mono_ns), label: 'host ' + t.cmd, row: 0 }));
  const ticks = rec.gaps.map((g) => ({ x: tOf(g.rx_mono_ns), label: g.kind === 'gap' ? `gap ${g.missing}` : g.kind }))
    .concat(rec.bad.map((b) => ({ x: tOf(b.rx_mono_ns), label: '✕' })));
  const trustLayers = [
    { type: 'band', data: bands, color: col('--attack'), alpha: 0.12, label: 'attack mode' },
    { type: 'hline', y: 30, color: col('--thr'), dash: [5, 4], label: '30' },
    { type: 'vlines', data: txs, color: col('--tone-host'), dash: [2, 3], width: 1 },
    { type: 'vlines', data: outs, color: col('--tone-out'), width: 1.4 },
    { type: 'step', data: upd, color: col('--series-1'), width: 2, markers: 1.8 },
    { type: 'ticks', data: ticks, color: col('--tone-bad') },
  ];
  const ex = rec.upd.filter((u) => u.f.exec_ms !== undefined).map((u) => ({ x: tOf(u.rx_mono_ns), y: u.f.exec_ms }));
  const per = [];
  const devT = (u) => u.t0_dev_us ?? u.t_dev_us;   // workload start (live) or update time (replay)
  for (let i = 1; i < rec.upd.length; i++) {
    const a = rec.upd[i - 1], b = rec.upd[i];
    if (b.f.cycle === a.f.cycle + 1 && devT(a) && devT(b) && a.epoch === b.epoch) per.push({ x: tOf(b.rx_mono_ns), y: (devT(b) - devT(a)) / 1000 });
  }
  const ymax = Math.max(50, ...ex.map((p) => p.y), ...per.map((p) => p.y)) * 1.15;
  const execLayers = { ymax, layers: [
    { type: 'points', data: ex, color: col('--series-2'), radius: 2.4 },
    { type: 'points', data: per, color: col('--series-1'), radius: 1.8 },
    { type: 'vlines', data: txs, color: col('--tone-host'), dash: [2, 3], width: 1 },
  ] };
  return { trustLayers, execLayers, crit };
}

function jointLayers(env, nodata, crit) {
  const vmax = Math.max(0.1, ...env.map((p) => p.hi)) * 1.15;
  return { vmax, layers: [
    { type: 'nodata', data: nodata, label: 'NO FRESH DATA' },
    { type: 'hline', y: crit.still, color: col('--tone-ok'), dash: [4, 4], label: 'still ' + crit.still },
    { type: 'hline', y: crit.move, color: col('--tone-warn'), dash: [4, 4], label: 'moving ' + crit.move },
    { type: 'envelope', data: env, color: col('--series-3') },
  ] };
}

function critOf(tel) {
  tel = tel || {};
  return { still: (tel.standstill || {}).v_still_rad_s ?? 0.01, move: (tel.moving || {}).v_move_rad_s ?? 0.05,
           gap: (tel.standstill || {}).max_gap_ms ?? 40, stale: tel.joint_stale_ms ?? 100 };
}

function drawLive() {
  if (S.view !== 'live' || !S.status) return;
  const now = piNowNs();
  const W = parseFloat($('liveWindow').value);
  const L = S.live;
  let t0, x0, x1, note;
  if (L.attemptT0 && S.status.runner.current) {
    t0 = L.attemptT0; const nowRel = (now - t0) / 1e9;
    x1 = Math.max(W, nowRel + 1); x0 = Math.max(-2, x1 - W); note = `seconds since attempt ${S.status.runner.current.attempt_id} started · host receipt time`;
  } else {
    t0 = now; x0 = -W; x1 = 1; note = 'seconds before now · host receipt time';
  }
  $('liveAxisNote').textContent = note;
  const tOf = (ns) => (ns - t0) / 1e9;
  const crit = critOf(S.status.runner.telemetry_criteria);
  const { trustLayers, execLayers } = buildLayers(L, tOf, crit, x1);
  for (const [p, layers] of [[P.trust, trustLayers], [P.exec, execLayers.layers]]) { p.setX(x0, x1); p.setLayers(layers); }
  P.exec.setY(0, execLayers.ymax);
  P.trust.hoverText = (x) => nearestText(L.upd.map((u) => ({ x: tOf(u.rx_mono_ns), u })), x, (u) => `t=${f1(x, 2)} s\ntrust ${f1(u.f.trust, 2)} cycle ${u.f.cycle}\nattack ${u.f.attack} D12 cmd ${u.f.d12}`);
  // joints: envelope + explicit no-data shading from arrival gaps and staleness
  const js = L.joints.filter((j) => tOf(j.rx_mono_ns) >= x0 - 1);
  const env = js.filter((j) => j.valid && j.vmax !== null).map((j) => ({ x: tOf(j.t_mono_ns || j.rx_mono_ns), lo: j.vmax_lo ?? j.vmax, hi: j.vmax_hi ?? j.vmax }));
  const nodata = [];
  const gapLimit = Math.max(0.15, crit.stale / 1000 * 1.5);
  let prev = x0;
  for (const j of js) { const t = tOf(j.rx_mono_ns); if (t - prev > gapLimit) nodata.push({ from: prev, to: t }); prev = t; }
  if (S.status.robot.capabilities.joint_telemetry && tOf(now) - prev > gapLimit) nodata.push({ from: prev, to: x1 });
  if (!S.status.robot.capabilities.joint_telemetry) nodata.splice(0, nodata.length, { from: x0, to: x1 });
  const jl = jointLayers(env, nodata, crit);
  P.joint.setX(x0, x1); P.joint.setY(0, jl.vmax); P.joint.setLayers(jl.layers);
  P.trust.draw(); P.exec.draw(); P.joint.draw();
  const r = curAttemptRecords();
  P.tl.setX(x0, x1);
  P.tl.lanes = timelineLanes(r ? { ...r, tOf } : null);
  P.tl.draw();
}

function nearestText(pts, x, fmtFn) {
  let best = null;
  for (const p of pts) if (!best || Math.abs(p.x - x) < Math.abs(best.x - x)) best = p;
  return best && Math.abs(best.x - x) < 1.5 ? fmtFn(best.u) : null;
}

function timelineLanes(r) {
  const lanes = [{ name: 'Host command sent', events: [] }, { name: 'Monitor processed', events: [] }, { name: 'Trust update < 30', events: [] },
    { name: 'D12 command (fw)', events: [] }, { name: 'Electrical D12', events: [{ x: null }] }, { name: 'Controller report', events: [] },
    { name: 'Motion (telemetry)', events: [] }];
  if (!r) return lanes;
  const t = r.tOf;
  for (const x of r.tx) if (x.ok) lanes[0].events.push({ x: t(x.t_write_end_mono_ns), label: x.cmd, tone: 'host' });
  for (const d of r.dev) {
    if (d.kind === 'cmd') lanes[1].events.push({ x: t(d.rx_mono_ns), label: d.f.cmd + ' (cycle ' + d.f.cycle + ')', tone: 'dev' });
    if (d.kind === 'cfg') lanes[1].events.push({ x: t(d.rx_mono_ns), label: 'config', tone: 'dev' });
    if (d.kind === 'out') lanes[3].events.push({ x: t(d.rx_mono_ns), label: d.f.level ? 'HIGH' : 'LOW', tone: 'out' });
  }
  const cross = r.upd.find((u) => u.f.below === 1);
  if (cross) lanes[2].events.push({ x: t(cross.rx_mono_ns), label: 'cycle ' + cross.f.cycle + ' trust ' + f1(cross.f.trust, 2), tone: 'out' });
  for (const x of r.robot) lanes[5].events.push({ x: t(x.rx_mono_ns), label: x.name, tone: 'ctl' });
  for (const h of r.host) {
    if (h.event === 'moving_confirmed') lanes[6].events.push({ x: t(h.t_window_start_mono_ns || h.t_mono_ns), label: 'moving confirmed', tone: 'motion' });
    if (h.event === 'trajectory' && ['accepted', 'aborted', 'succeeded'].includes(h.status)) lanes[6].events.push({ x: t(h.t_mono_ns), label: `traj ${h.phase} ${h.status}`, tone: 'motion' });
  }
  lanes[4].name = 'Electrical D12 (not measured)';
  return lanes;
}

// ------------------------------------------------------------------ replay
async function loadRoots() {
  const sel = $('rpRoot');
  const opts = [];
  if (S.localInfo) for (const [k, v] of Object.entries(S.localInfo.roots)) opts.push([`local:${k}`, `Local ${k === 'sim' ? 'simulated data' : 'hardware mirror'} (${v.path})`]);
  if (S.backend.live) opts.push(['pi', 'Acquisition host (direct, read-only)']);
  sel.innerHTML = opts.map(([v, t]) => `<option value="${v}">${esc(t)}</option>`).join('');
  S.replay.root = sel.value;
  $('rpSync').disabled = !(S.localInfo && S.backend.live);
}

function replayBase() {
  const r = S.replay.root;
  if (r === 'pi') return `${S.backend.liveBase}/sessions`;
  return `/api/replay/${r.split(':')[1]}/sessions`;
}

async function loadSessions() {
  try {
    const d = await api('GET', replayBase());
    S.replay.sessions = d.sessions;
    $('rpSessions').innerHTML = d.sessions.length ? d.sessions.map((s) => `<div class="item ${s.session_id === S.replay.sid ? 'sel' : ''}" data-sid="${esc(s.session_id)}">
      <b>${esc(s.title || s.campaign_id)}</b> <span class="pill ${esc(s.kind)}">${esc(s.kind)}</span> ${s.simulated ? '<span class="pill sim">SIM</span>' : ''}<br>
      <span class="hint">${esc(s.session_id)} · ${s.n_attempts} attempts · ${esc(s.state)}</span></div>`).join('') : '<p class="hint">No sessions in this data root.</p>';
    document.querySelectorAll('#rpSessions .item').forEach((e) => e.addEventListener('click', () => loadSession(e.dataset.sid)));
  } catch (e) { $('rpSessions').innerHTML = `<p class="hint">Cannot list sessions: ${esc(e.message)}</p>`; }
}

async function loadSession(sid) {
  S.replay.sid = sid; S.replay.selected.clear();
  const d = await api('GET', `${replayBase()}/${encodeURIComponent(sid)}`);
  S.replay.session = d;
  renderHeader();
  loadSessions();
  renderSessionTable();
}

function renderSessionTable() {
  const d = S.replay.session;
  if (!d) return;
  const m = d.meta;
  $('rpSessionHead').innerHTML = `<h3>${esc(m.title || d.session_id)} <span class="pill ${esc(m.kind)}">${esc((m.kind || '').toUpperCase())}</span>
    ${m.simulated ? '<span class="pill sim">SIMULATED DATA</span>' : ''} <span class="pill ${esc(m.campaign_status)}">${esc(m.campaign_status)}</span></h3>
    <div class="hint">${esc(d.session_id)} · ${esc(m.procedure)} · ${esc(m.data_origin)} · plan ${esc((m.plan_sha256 || '').slice(0, 12))}…
    ${d.end ? ' · ended ' + esc(d.end.final_state) : d.recovered ? ' · INTERRUPTED (recovered)' : ' · open'}</div>
    ${m.kind === 'demonstration' ? '<p class="hint"><b>Demonstration preset — not a complete experimental campaign.</b></p>' : ''}`;
  const showEx = $('rpShowExcluded').checked;
  const rows = d.attempts.filter((a) => showEx || !(a.exclusions && a.exclusions.length)).map((a) => {
    const iv = a.key_intervals || {};
    const v = iv.device_attack_to_cross ? f1(iv.device_attack_to_cross.value_ms, 1) : '—';
    const ex = a.exclusions && a.exclusions.length;
    return `<tr class="${a.attempt_id === S.replay.aid ? 'sel' : ''} ${ex ? 'excluded' : ''}" data-aid="${esc(a.attempt_id)}">
      <td><input type="checkbox" class="cmpchk" value="${esc(a.attempt_id)}" ${S.replay.selected.has(a.attempt_id) ? 'checked' : ''}></td>
      <td>${esc(a.attempt_id)}</td><td>${esc(a.condition_id)}</td><td>${esc(a.status)}</td>
      <td>${esc(a.outcome ? a.outcome.crossing : '—')}</td><td class="num">${v}</td>
      <td>${(a.quality_warnings || []).length ? (a.quality_warnings.length + ' ⚠') : ''}</td>
      <td>${a.departures && a.departures.length ? 'departure' : ''}</td><td>${ex ? 'excluded: ' + esc(a.exclusions.join(',')) : ''}</td></tr>`;
  });
  $('rpAttempts').innerHTML = `<table><thead><tr><th></th><th>attempt</th><th>condition</th><th>status</th><th>crossing</th>
    <th>ATTACK→<30 (device ms)</th><th>quality</th><th>procedure</th><th>manual exclusion</th></tr></thead><tbody>${rows.join('')}</tbody></table>`;
  const c = d.exclusion_counts;
  $('rpCounts').textContent = c ? `${c.included} included · ${c.excluded} excluded · ${c.total} attempts` : '';
  document.querySelectorAll('#rpAttempts tr[data-aid]').forEach((tr) => tr.addEventListener('click', (e) => { if (!e.target.classList.contains('cmpchk')) loadAttempt(tr.dataset.aid); }));
  document.querySelectorAll('.cmpchk').forEach((cb) => cb.addEventListener('change', () => { cb.checked ? S.replay.selected.add(cb.value) : S.replay.selected.delete(cb.value); }));
}

async function loadAttempt(aid) {
  S.replay.aid = aid;
  S.replay.payload = await api('GET', `${replayBase()}/${encodeURIComponent(S.replay.sid)}/attempts/${encodeURIComponent(aid)}`);
  S.replay.cursor = null; S.replay.playing = false; $('rpPlay').textContent = '▶ Play'; $('rpScrub').value = 1000;
  renderSessionTable();
  renderReplaySummary();
  renderExclusion();
  drawReplay();
}

function replayRecords(p, upTo) {
  const s = p.series, keep = (t) => upTo === null || t <= upTo;
  const ns = (t) => Math.round(t * 1e9);   // series are already relative seconds; map to pseudo-ns
  const t0 = p.start && p.start.t_mono_ns;
  const absToNs = (abs) => (abs && t0 ? abs - t0 : null);
  return {
    upd: s.updates.filter((u) => keep(u.t)).map((u) => ({ rx_mono_ns: ns(u.t), t0_dev_us: null, epoch: u.epoch, t_dev_us: u.t_dev_us,
      f: { trust: u.trust, cycle: u.cycle, attack: u.attack, below: u.below, d12: u.d12, exec_ms: u.exec_ms } })),
    dev: s.device_events.filter((e) => keep(e.t)).map((e) => ({ kind: e.kind, rx_mono_ns: ns(e.t), f: e.f, t_dev_us: e.t_dev_us })),
    tx: s.commands.filter((c) => keep(c.t)).map((c) => ({ ...c, t_write_end_mono_ns: ns(c.t) })),
    robot: s.robot_state.filter((r) => keep(r.t)).map((r) => ({ ...r, rx_mono_ns: ns(r.t) })),
    host: s.host_events.filter((h) => keep(h.t)).map((h) => ({ ...h, t_mono_ns: ns(h.t), t_window_start_mono_ns: absToNs(h.t_window_start_mono_ns) })),
    gaps: s.continuity.filter((g) => keep(g.t)).map((g) => ({ ...g, rx_mono_ns: ns(g.t) })),
    bad: s.invalid_records.filter((b) => keep(b.t)).map((b) => ({ ...b, rx_mono_ns: ns(b.t) })),
  };
}

function drawReplay() {
  const p = S.replay.payload;
  if (!p) return;
  const s = p.series;
  const end = Math.max(1, ...s.updates.map((u) => u.t), ...s.commands.map((c) => c.t || 0), ...(s.joints.envelope.map((e) => e.t)));
  const cur = S.replay.cursor;
  const rec = replayRecords(p, cur);
  const tOf = (ns) => ns / 1e9;
  const crit = critOf(p.start.telemetry_config);
  const { trustLayers, execLayers } = buildLayers(rec, tOf, crit, end);
  for (const [pl, layers] of [[P.rTrust, trustLayers], [P.rExec, execLayers.layers]]) { pl.setX(-0.2, end + 0.2); pl.setLayers(layers); pl.cursor = cur; }
  P.rExec.setY(0, execLayers.ymax);
  const env = s.joints.envelope.filter((e) => cur === null || e.t <= cur).map((e) => ({ x: e.t, lo: e.lo, hi: e.hi }));
  const nodata = s.joints.gaps.map((g) => ({ from: g.from, to: g.to }));
  if (!s.joints.samples) nodata.push({ from: -0.2, to: end + 0.2 });
  const jl = jointLayers(env, nodata, crit);
  P.rJoint.setX(-0.2, end + 0.2); P.rJoint.setY(0, jl.vmax); P.rJoint.setLayers(jl.layers); P.rJoint.cursor = cur;
  P.rTrust.hoverText = (x) => nearestText(rec.upd.map((u) => ({ x: tOf(u.rx_mono_ns), u })), x, (u) => `t=${f1(x, 2)} s\ntrust ${f1(u.f.trust, 2)} cycle ${u.f.cycle}\nattack ${u.f.attack} D12 cmd ${u.f.d12}`);
  P.rTrust.draw(); P.rExec.draw(); P.rJoint.draw();
  P.rTl.setX(-0.2, end + 0.2); P.rTl.lanes = timelineLanes({ ...rec, tOf }); P.rTl.draw();
  const m = S.replay.session.meta;
  $('rpTitle').textContent = `${p.attempt_id} · ${p.start.condition_id || ''} · ${p.status}${m.simulated ? ' · SIMULATED' : ''}`;
  S.replay.end = end;
}

function renderReplaySummary() {
  const p = S.replay.payload, sm = p.summary;
  if (!sm) { $('rpSummary').innerHTML = '<p class="hint">No summary.</p>'; return; }
  const iv = Object.entries(sm.key_intervals || {}).map(([k, v]) => `<tr><td>${esc(k)}</td><td class="num">${f1(v.value_ms, 2)}</td>
      <td>${v.range_ms ? f1(v.range_ms[0], 2) + '…' + f1(v.range_ms[1], 2) : ''}</td><td>${esc(v.clock)}</td></tr>`).join('');
  const o = sm.outcome || {};
  const mc = sm.model_check;
  const mo = sm.motion || {};
  $('rpSummary').innerHTML = `<div class="kv">
      <span class="k">Status</span><span><b>${esc(p.status)}</b>${p.end && p.end.reason ? ' – ' + esc(p.end.reason) : ''}</span>
      <span class="k">Injection</span><span>${esc(o.injection)}</span>
      <span class="k">Crossing</span><span>${esc(o.crossing)}${o.crossing_relative_to_recover ? ' (' + esc(o.crossing_relative_to_recover) + ')' : ''}</span>
      <span class="k">D12 LOW commanded</span><span>${o.out_low_commanded ? 'yes (firmware report)' : 'no'}</span>
      <span class="k">Attacked updates</span><span>${esc(sm.attacked_updates_to_cross ?? '—')} ${mc ? `<span class="hint">MODEL expects ${esc(mc.attacked_updates_to_cross_expected)}${mc.agrees === false ? ' — DISAGREES' : ''}</span>` : ''}</span>
      <span class="k">Records</span><span>${sm.records.device_ok_v8} ok · ${sm.records.not_ok} invalid · ${sm.records.missing_by_sequence} missing</span>
      ${mo.applicable ? `<span class="k">Moving before injection</span><span>${esc(mo.moving_before_injection ? mo.moving_before_injection.status : '—')}</span>
      <span class="k">Standstill (criterion)</span><span>${esc(mo.standstill_after_out_low ? mo.standstill_after_out_low.status + ' – ' + mo.standstill_after_out_low.reason : '—')}</span>` : ''}
    </div>
    <h3>Intervals</h3><table><thead><tr><th>interval</th><th>ms</th><th>range</th><th>clock</th></tr></thead><tbody>${iv || '<tr><td colspan=4 class="hint">none</td></tr>'}</tbody></table>
    ${(sm.quality_warnings || []).length ? '<h3>Acquisition-quality warnings</h3><ul class="warnlist">' + sm.quality_warnings.map((w) => `<li>${esc(w.code)} ${esc(JSON.stringify(w).slice(0, 120))}</li>`).join('') + '</ul>' : '<p class="hint">No acquisition-quality warnings.</p>'}
    ${(sm.notes || []).map((n) => `<p class="hint">${esc(n)}</p>`).join('')}
    <p class="notmeasured">Not measured by this software: ${esc((sm.not_measured_by_this_software || []).join('; '))}</p>
    ${p.summary_computed_on_read ? '<p class="hint">Summary computed on read (no summary.json recorded).</p>' : ''}`;
}

async function renderExclusion() {
  const p = S.replay.payload, root = S.replay.root;
  if (!p || !root.startsWith('local:')) { $('rpExclusion').innerHTML = '<p class="hint">Exclusions are managed on local copies (copy sessions from the Pi first).</p>'; return; }
  const key = root.split(':')[1];
  const d = await api('GET', `/api/exclusions/${key}?session_id=${encodeURIComponent(S.replay.sid)}&attempt_id=${encodeURIComponent(p.attempt_id)}`);
  const active = d.state[`${S.replay.sid}/${p.attempt_id}`] || [];
  $('rpExclusion').innerHTML = `<div class="kv"><span class="k">Current</span><span>${active.length ? 'EXCLUDED from ' + esc(active.join(', ')) : 'included'}</span></div>
    <div class="row"><select id="exScope"><option value="all">all analyses and plots</option><option value="comparison_plots">comparison plots only</option>
    <option value="timing_analysis">timing analysis only</option><option value="motion_analysis">motion analysis only</option></select></div>
    <div class="row"><button id="exBtn">Exclude…</button><button id="reBtn" ${active.length ? '' : 'disabled'}>Restore…</button></div>
    <h3>History</h3>${d.history.length ? '<ul class="warnlist" style="color:var(--fg)">' + d.history.map((h) => `<li style="color:var(--fg)">${esc(h.t_utc)} <b>${esc(h.action)}</b> [${esc(h.scopes.join(','))}] by ${esc(h.operator)}: ${esc(h.reason)}</li>`).join('') + '</ul>' : '<p class="hint">No exclusion history.</p>'}`;
  $('exBtn').addEventListener('click', () => askReason('Exclude attempt', '<p>The attempt stays in the dataset; this records an analyst decision that can be restored later.</p>', 'Exclude',
    async (reason) => { await api('POST', `/api/exclusions/${key}`, { action: 'exclude', session_id: S.replay.sid, attempt_id: p.attempt_id, reason, operator: operator(), scopes: [$('exScope').value] }); await loadSession(S.replay.sid); renderExclusion(); }));
  $('reBtn').addEventListener('click', () => askReason('Restore attempt', '<p>Restoring records a new event; the exclusion history is kept.</p>', 'Restore',
    async (reason) => { await api('POST', `/api/exclusions/${key}`, { action: 'restore', session_id: S.replay.sid, attempt_id: p.attempt_id, reason, operator: operator() }); await loadSession(S.replay.sid); renderExclusion(); }));
}

async function compareSelected() {
  const ids = [...S.replay.selected];
  if (ids.length < 2) { alertBox('Select at least two attempts (checkboxes) to compare.'); return; }
  const loads = await Promise.all(ids.map((a) => api('GET', `${replayBase()}/${encodeURIComponent(S.replay.sid)}/attempts/${encodeURIComponent(a)}`)));
  const palette = ['--series-1', '--series-2', '--series-3', '--tone-sim', '--tone-warn', '--tone-bad', '--tone-info', '--tone-ok'];
  const layers = [{ type: 'hline', y: 30, color: col('--thr'), dash: [5, 4], label: '30' }, { type: 'vlines', data: [{ x: 0, label: 'ATTACK processed (device)' }], color: col('--tone-dev') }];
  const rows = [];
  let xmax = 1;
  loads.forEach((p, i) => {
    const a = p.summary && p.summary.events.D_ATTACK;
    if (!a) { rows.push(`<tr><td>${esc(p.attempt_id)}</td><td colspan=5 class="hint">no device ATTACK event (control or legacy): not aligned</td></tr>`); return; }
    const data = p.series.updates.filter((u) => u.t_dev_us && u.epoch === a.epoch).map((u) => ({ x: (u.t_dev_us - a.t_dev_us) / 1e6, y: u.trust }));
    xmax = Math.max(xmax, ...data.map((d) => d.x));
    layers.push({ type: 'step', data, color: col(palette[i % palette.length]), width: 1.8, markers: 1.6 });
    const iv = p.summary.key_intervals || {};
    rows.push(`<tr><td><span style="color:var(${palette[i % palette.length]})">■</span> ${esc(p.attempt_id)}</td><td>${esc(p.start.condition_id)}</td>
      <td class="num">${iv.device_attack_to_cross ? f1(iv.device_attack_to_cross.value_ms, 1) : '—'}</td><td class="num">${esc(p.summary.attacked_updates_to_cross ?? '—')}</td>
      <td class="num">${p.summary.updates.loop_period_ms ? f1(p.summary.updates.loop_period_ms.median, 2) : '—'}</td><td>${esc(p.summary.outcome.crossing)}</td></tr>`);
  });
  P.cTrust.setX(-0.5, xmax + 0.2); P.cTrust.setLayers(layers);
  $('rpCompare').hidden = false;
  P.cTrust.draw();
  $('cTable').innerHTML = `<table><thead><tr><th>attempt</th><th>condition</th><th>ATTACK→<30 ms (device)</th><th>attacked updates</th><th>loop period median ms</th><th>crossing</th></tr></thead><tbody>${rows.join('')}</tbody></table>
    <p class="hint">x-axis: device time relative to the monitor processing ATTACK (same clock within each attempt). Excluded attempts can still be selected here; exclusions apply to analyses you run on the data.</p>`;
}

function replayTick() {
  if (!S.replay.playing || !S.replay.payload) return;
  const speed = parseFloat($('rpSpeed').value);
  const now = performance.now();
  const dt = (now - (S.replay.lastTick || now)) / 1000 * speed;
  S.replay.lastTick = now;
  S.replay.cursor = Math.min(S.replay.end, (S.replay.cursor ?? 0) + dt);
  $('rpScrub').value = Math.round(1000 * S.replay.cursor / S.replay.end);
  if (S.replay.cursor >= S.replay.end) { S.replay.playing = false; $('rpPlay').textContent = '▶ Play'; }
  drawReplay();
}

async function doSync() {
  $('rpSyncNote').textContent = 'Copying…';
  try {
    const r = await api('POST', '/api/sync', {});
    const s = r.sessions;
    $('rpSyncNote').innerHTML = `${esc(r.simulated_source ? 'SIMULATED source → local sim root' : 'hardware source → local mirror')}: ` +
      s.map((x) => `${esc(x.session_id)}: ${x.skipped ? esc(x.skipped) : `${x.copied} copied, ${x.unchanged} unchanged${x.conflicts.length ? ', CONFLICTS: ' + esc(x.conflicts.join(', ')) : ''}`}`).join('<br>');
    loadSessions();
  } catch (e) { $('rpSyncNote').textContent = 'Copy failed: ' + e.message; }
}

// ------------------------------------------------------------------ campaigns
async function loadCampaigns() {
  if (!S.backend.live) { $('cgList').innerHTML = '<p class="hint">No acquisition host configured.</p>'; return; }
  try {
    const d = await live('GET', 'campaigns');
    S.campaigns.list = d.campaigns;
    $('cgList').innerHTML = d.campaigns.map((c) => `<div class="item ${c.file === S.campaigns.file ? 'sel' : ''}" data-file="${esc(c.file)}">
       <b>${esc(c.title || c.file)}</b><br><span class="pill ${esc(c.kind)}">${esc(c.kind)}</span> <span class="pill ${esc(c.status)}">${esc(c.status)}</span>
       <span class="hint">${esc(c.procedure)} · ${c.valid ? c.n_trials + ' trials' : 'INVALID'}</span></div>`).join('');
    document.querySelectorAll('#cgList .item').forEach((e) => e.addEventListener('click', () => previewCampaign(e.dataset.file)));
  } catch (e) { $('cgList').innerHTML = `<p class="hint">Cannot list campaigns: ${esc(e.message)}</p>`; }
}

async function previewCampaign(file) {
  S.campaigns.file = file;
  const d = await live('GET', `campaigns/${encodeURIComponent(file)}`);
  S.campaigns.preview = d;
  loadCampaigns();
  if (!d.valid) { $('cgPreview').innerHTML = `<h3>${esc(file)}: invalid</h3><ul class="warnlist">${d.problems.map((p) => `<li>${esc(p)}</li>`).join('')}</ul>`; return; }
  const p = d.plan, cfg = p.normalized_config;
  const conds = p.conditions.map((c) => `<tr><td>${esc(c.condition_id)}</td><td>${esc(c.workload)}</td><td>${c.alpha}</td><td>${c.failure_ms || 'control'}</td>
      <td class="num">${c.repetitions}</td><td class="num">${esc(c.model.attacked_updates_to_cross)}</td><td>${esc(c.model.expectation)}</td><td class="hint">${esc(c.purpose)}</td></tr>`).join('');
  const trials = p.trials.map((t) => `${t.trial_id}:${t.condition_id}${t.injection_jitter_ms ? '+' + t.injection_jitter_ms : ''}`).join('  ');
  const st = controlState('start', currentMode(), S.status && S.status.runner);
  $('cgPreview').innerHTML = `<h3>${esc(p.title)} <span class="pill ${esc(p.kind)}">${esc(p.kind.toUpperCase())}</span> <span class="pill ${esc(p.status)}">${esc(p.status)}</span></h3>
    <p>${esc(cfg.purpose)}</p>
    ${p.kind === 'demonstration' ? '<p><b>Demonstration preset — not a complete experimental campaign.</b></p>' : ''}
    <div class="kv"><span class="k">Procedure</span><span>${esc(p.procedure)}</span>
      <span class="k">Matrix</span><span>${p.n_conditions} conditions · ${p.n_trials} trials · est. ${f1(p.estimated_duration_s / 60, 1)} min</span>
      <span class="k">Ordering</span><span>${esc(p.ordering.method)}${p.ordering.seed === null || p.ordering.seed === undefined ? ' · not randomized' : ' · seed ' + esc(p.ordering.seed) + ' (' + esc(p.ordering.prng) + ')'}</span>
      <span class="k">Plan hash</span><span><code>${esc(p.plan_sha256)}</code></span>
      <span class="k">Trial timing</span><span>baseline ${cfg.trial.baseline_ms} ms + jitter ≤${cfg.trial.injection_jitter_ms} ms · post-RECOVER ${cfg.trial.post_recover_ms} ms · ATTACK ${cfg.trial.attack_resend_interval_ms ? 'resent every ' + cfg.trial.attack_resend_interval_ms + ' ms' : 'sent once'}</span>
      <span class="k">Progression</span><span>${esc(cfg.progression.mode)}${cfg.progression.pause_on_operator_disconnect ? ' · pauses if the dashboard disconnects' : ''}</span></div>
    ${(d.warnings || []).map((w) => `<p class="hold">${esc(w)}</p>`).join('')}
    <h3>Conditions <span class="hint">MODEL columns: firmware recurrence + historical period summaries; expectations, not results</span></h3>
    <div class="table-wrap"><table><thead><tr><th>id</th><th>workload</th><th>α</th><th>failure ms</th><th>reps</th><th>MODEL n</th><th>MODEL expectation</th><th>purpose</th></tr></thead><tbody>${conds}</tbody></table></div>
    <h3>Trial order (id:condition+jitter ms)</h3><p class="hint" style="word-break:break-word">${esc(trials)}</p>
    ${cfg.confounds ? '<h3>Known confounds</h3><ul>' + cfg.confounds.map((c) => `<li>${esc(c)}</li>`).join('') + '</ul>' : ''}
    <h3>Start</h3>
    <label class="check"><input type="checkbox" id="ackMatrix"> I reviewed the full matrix and trial order above</label>
    ${p.procedure === 'robot' ? '<label class="check"><input type="checkbox" id="ackMotion"> Robot motion is authorized for this session and the cell is prepared</label>' : ''}
    <div class="row"><button id="cgStart" class="primary" ${dis(st)}>Start campaign</button><span class="hint">${esc(st.reason)}</span></div>`;
  $('cgStart').addEventListener('click', async () => {
    if (!$('ackMatrix').checked) { alertBox('Confirm that you reviewed the matrix.'); return; }
    if (!operator()) { alertBox('Enter your name in the Operator field.'); return; }
    const acks = ['matrix_reviewed'];
    if (p.procedure === 'robot') { if (!$('ackMotion').checked) { alertBox('Robot procedures need the motion authorization checkbox.'); return; } acks.push('robot_motion_authorized'); }
    await act(() => live('POST', 'campaign/start', { file, plan_sha256: p.plan_sha256, operator: operator(), acknowledgements: acks }));
    setView('live');
  });
}

// ------------------------------------------------------------------ modal helpers
function askReason(title, bodyHtml, okLabel, fn, cls = 'primary') {
  $('modalTitle').textContent = title;
  $('modalBody').innerHTML = `${bodyHtml}<label>Reason (recorded)<textarea id="mReason"></textarea></label>${operator() ? '' : '<p class="hint">Tip: enter your name in the Operator field so it is recorded.</p>'}`;
  $('modalActions').innerHTML = `<button id="mCancel">Cancel</button><button id="mOk" class="${cls}">${esc(okLabel)}</button>`;
  $('modal').hidden = false;
  $('mCancel').onclick = () => { $('modal').hidden = true; };
  $('mOk').onclick = async () => {
    const reason = $('mReason').value.trim();
    if (reason.length < 4) { $('mReason').focus(); return; }
    $('modal').hidden = true;
    await act(() => fn(reason));
  };
}
function alertBox(text) {
  $('modalTitle').textContent = 'Note';
  $('modalBody').innerHTML = `<p>${esc(text)}</p>`;
  $('modalActions').innerHTML = '<button id="mOk2" class="primary">OK</button>';
  $('modal').hidden = false;
  $('mOk2').onclick = () => { $('modal').hidden = true; };
}
async function act(fn) {
  try { const r = await fn(); if (r && r.note) addLog(r.note); return r; }
  catch (e) { alertBox('Request refused: ' + e.message); addLog('request refused: ' + e.message, 'bad'); }
}

// ------------------------------------------------------------------ views & boot
function setView(v) {
  S.view = v;
  document.querySelectorAll('.tabs button[data-view]').forEach((b) => b.classList.toggle('active', b.dataset.view === v));
  for (const k of ['live', 'replay', 'campaigns']) $('view-' + k).hidden = k !== v;
  renderHeader();
  if (v === 'live') { renderLivePanels(); renderLog(); }
  if (v === 'replay') { loadSessions(); drawReplay(); }
  if (v === 'campaigns') loadCampaigns();
}

async function boot() {
  await detectBackend();
  try { $('operator').value = localStorage.getItem('onedge_operator') || ''; } catch (e) { /* storage unavailable */ }
  $('operator').addEventListener('change', () => { try { localStorage.setItem('onedge_operator', operator()); } catch (e) { /* ignore */ } });
  document.querySelectorAll('.tabs button[data-view]').forEach((b) => b.addEventListener('click', () => setView(b.dataset.view)));
  document.querySelectorAll('[data-manual]').forEach((b) => b.addEventListener('click', () => manualCmd(b.dataset.manual)));
  $('noteBtn').addEventListener('click', () => { const t = $('noteText').value.trim(); if (t) act(() => live('POST', 'note', { text: t, operator: operator() })).then(() => { $('noteText').value = ''; }); });
  $('rpRoot').addEventListener('change', () => { S.replay.root = $('rpRoot').value; S.replay.sid = null; S.replay.session = null; loadSessions(); renderHeader(); });
  $('rpRefresh').addEventListener('click', loadSessions);
  $('rpSync').addEventListener('click', doSync);
  $('rpShowExcluded').addEventListener('change', renderSessionTable);
  $('rpCompareBtn').addEventListener('click', compareSelected);
  $('rpPlay').addEventListener('click', () => {
    if (!S.replay.payload) return;
    S.replay.playing = !S.replay.playing; S.replay.lastTick = performance.now();
    if (S.replay.playing && (S.replay.cursor === null || S.replay.cursor >= S.replay.end)) S.replay.cursor = 0;
    $('rpPlay').textContent = S.replay.playing ? '❚❚ Pause' : '▶ Play';
  });
  $('rpScrub').addEventListener('input', () => { const v = parseInt($('rpScrub').value, 10); S.replay.cursor = v >= 1000 ? null : v / 1000 * (S.replay.end || 1); S.replay.playing = false; $('rpPlay').textContent = '▶ Play'; drawReplay(); });
  $('cgRefresh').addEventListener('click', loadCampaigns);
  makePlots();
  await loadRoots();
  connectStream();
  setInterval(() => { if (S.backend.live) fetch(`${S.backend.liveBase}/heartbeat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ client_id: S.clientId }) }).catch(() => {}); }, 2000);
  setInterval(renderHeader, 1000);
  let last = 0;
  const loop = (t) => { if (t - last > 120) { last = t; drawLive(); replayTick(); } requestAnimationFrame(loop); };
  requestAnimationFrame(loop);
  window.addEventListener('resize', () => { drawLive(); drawReplay(); });
  setView('live');
}
boot();
