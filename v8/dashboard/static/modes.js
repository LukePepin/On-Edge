// Mode labelling and control gating for the V8 dashboard (pure functions; tested with node).
//
// Principles: replay never enables live controls; a missing or stale stream disables them;
// missing telemetry is labelled unknown, never as zero motion or a safe state.

export const STREAM_STALE_MS = 3000;

/**
 * @param {object} s
 *   view: 'live' | 'replay' | 'campaigns'
 *   liveAvailable: dashboard has an acquisition daemon configured
 *   streamConnected: EventSource open
 *   lastStatusAgeMs: age of the newest status message (null if none)
 *   daemonSimulated: acquisition daemon reports simulated mode
 *   deviceFreshness: 'fresh' | 'stale' | 'missing' | 'invalid' | 'unavailable'
 *   replayOrigin: 'hardware' | 'software_simulation' | null
 */
export function deriveMode(s) {
  if (s.view === 'replay') {
    const sim = s.replayOrigin === 'software_simulation';
    return {
      key: sim ? 'replay-sim' : 'replay',
      badge: sim ? 'REPLAY · SIMULATED DATA' : 'REPLAY · RECORDED DATA',
      tone: sim ? 'sim' : 'replay',
      live: false,
      detail: 'Recorded data. Live controls are disabled in replay.',
    };
  }
  if (!s.liveAvailable) {
    return { key: 'unavailable', badge: 'LIVE UNAVAILABLE', tone: 'off', live: false,
             detail: 'This dashboard has no acquisition daemon configured (replay only).' };
  }
  const age = s.lastStatusAgeMs;
  if (!s.streamConnected || age === null || age === undefined || age > STREAM_STALE_MS) {
    return { key: 'disconnected', badge: 'DISCONNECTED', tone: 'off', live: false,
             detail: 'No current status from the acquisition daemon. Acquisition on the Pi continues ' +
                     'independently; controls are disabled until the stream recovers.' };
  }
  const sim = !!s.daemonSimulated;
  const stale = s.deviceFreshness && s.deviceFreshness !== 'fresh';
  return {
    key: sim ? 'live-sim' : 'live',
    badge: (sim ? 'LIVE · SIMULATED' : 'LIVE · HARDWARE') + (stale ? ' · MONITOR ' + s.deviceFreshness.toUpperCase() : ''),
    tone: stale ? 'stale' : (sim ? 'sim' : 'live'),
    live: true,
    detail: sim ? 'Software simulation: not hardware evidence.' : 'Live hardware acquisition.',
  };
}

const ACTIVE = ['RUNNING', 'AWAITING_CONFIRMATION', 'PAUSED', 'HOLD'];

/**
 * @param {string} action start|pause|resume|abort|confirm|decide|manual|robot_state_cmd|note
 * @param {object} mode result of deriveMode
 * @param {object} runner runner status from the daemon (may be null)
 */
export function controlState(action, mode, runner) {
  if (!mode.live) return { enabled: false, reason: mode.key.startsWith('replay') ? 'replay mode' : 'not connected' };
  const st = runner ? runner.state : null;
  switch (action) {
    case 'start':
      return st === 'IDLE' || st === 'COMPLETED' || st === 'ABORTED'
        ? { enabled: true, reason: '' } : { enabled: false, reason: `runner is ${st}` };
    case 'pause':
      if (runner && runner.pause_requested) return { enabled: false, reason: 'pause already requested' };
      return st === 'RUNNING' || st === 'AWAITING_CONFIRMATION'
        ? { enabled: true, reason: '' } : { enabled: false, reason: `runner is ${st}` };
    case 'resume':
      return st === 'PAUSED' ? { enabled: true, reason: '' } : { enabled: false, reason: `runner is ${st}` };
    case 'abort':
      return ACTIVE.includes(st) ? { enabled: true, reason: '' } : { enabled: false, reason: 'no active campaign' };
    case 'confirm':
      return st === 'AWAITING_CONFIRMATION' ? { enabled: true, reason: '' } : { enabled: false, reason: 'nothing to confirm' };
    case 'decide':
      return st === 'HOLD' && runner.hold ? { enabled: true, reason: '' } : { enabled: false, reason: 'no decision pending' };
    case 'manual':
      return { enabled: true, reason: runner && runner.current ? 'attempt running: departure must be confirmed' : '' };
    case 'robot_state_cmd':
      return runner && runner.current ? { enabled: false, reason: 'not allowed during an attempt' } : { enabled: true, reason: '' };
    case 'note':
      return { enabled: true, reason: '' };
    default:
      return { enabled: false, reason: 'unknown action' };
  }
}

/** Motion label for display: never implies standstill without fresh telemetry. */
export function motionLabel(robot) {
  if (!robot || !robot.capabilities || !robot.capabilities.joint_telemetry) {
    return { text: 'NO ROBOT TELEMETRY (bench)', tone: 'off' };
  }
  const f = robot.joint_freshness;
  if (f !== 'fresh') return { text: `MOTION UNKNOWN (telemetry ${f})`, tone: 'stale' };
  switch (robot.motion_state) {
    case 'moving': return { text: 'MOVING (fresh telemetry)', tone: 'live' };
    case 'still': return { text: 'BELOW STILL THRESHOLD (fresh telemetry; standstill criterion evaluated per attempt)', tone: 'live' };
    case 'transition': return { text: 'CHANGING SPEED', tone: 'live' };
    default: return { text: 'MOTION UNKNOWN', tone: 'stale' };
  }
}

/** D12 wording: what the firmware reported commanding, never an electrical measurement. */
export function outputLabel(d12) {
  if (d12 === 1) return 'D12 commanded HIGH (firmware report; electrical level not measured)';
  if (d12 === 0) return 'D12 commanded LOW (firmware report; electrical level not measured)';
  return 'D12 command state unknown (no report)';
}

/** Model expectation text for narration (explicitly labelled as MODEL). */
export function updatesToCross(alpha, start = 100, threshold = 30) {
  const f32 = (x) => Math.fround(x);
  let t = f32(start);
  const a = f32(alpha);
  for (let n = 1; n < 10000; n++) {
    t = f32(f32(a * 0) + (1.0 - a) * t);
    if (t < threshold) return n;
  }
  return null;
}
