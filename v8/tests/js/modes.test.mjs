// node --test v8/tests/js/  (Node 18+). Tests the dashboard's mode labelling and control gating.
import test from 'node:test';
import assert from 'node:assert/strict';
import { deriveMode, controlState, motionLabel, outputLabel, updatesToCross } from '../../dashboard/static/modes.js';

const liveBase = { view: 'live', liveAvailable: true, streamConnected: true, lastStatusAgeMs: 400,
                   daemonSimulated: false, deviceFreshness: 'fresh', replayOrigin: null };

test('replay never enables live controls, even with a healthy live stream', () => {
  const m = deriveMode({ ...liveBase, view: 'replay', replayOrigin: 'hardware' });
  assert.equal(m.live, false);
  assert.match(m.badge, /REPLAY/);
  for (const a of ['start', 'pause', 'resume', 'abort', 'confirm', 'decide', 'manual', 'robot_state_cmd', 'note']) {
    const c = controlState(a, m, { state: 'RUNNING', hold: { allowed: ['retry'] }, current: {} });
    assert.equal(c.enabled, false, a);
    assert.equal(c.reason, 'replay mode');
  }
});

test('simulated data is labelled in live and replay', () => {
  assert.match(deriveMode({ ...liveBase, daemonSimulated: true }).badge, /SIMULATED/);
  assert.match(deriveMode({ ...liveBase, view: 'replay', replayOrigin: 'software_simulation' }).badge, /SIMULATED/);
  assert.equal(deriveMode({ ...liveBase, daemonSimulated: true }).tone, 'sim');
});

test('a missing or stale stream disables controls and says DISCONNECTED', () => {
  for (const s of [{ streamConnected: false }, { lastStatusAgeMs: 10000 }, { lastStatusAgeMs: null }]) {
    const m = deriveMode({ ...liveBase, ...s });
    assert.equal(m.key, 'disconnected');
    assert.equal(m.live, false);
    assert.equal(controlState('abort', m, { state: 'RUNNING' }).enabled, false);
  }
  const m = deriveMode({ ...liveBase, liveAvailable: false });
  assert.equal(m.key, 'unavailable');
});

test('stale monitor data is flagged in the badge', () => {
  const m = deriveMode({ ...liveBase, deviceFreshness: 'stale' });
  assert.match(m.badge, /MONITOR STALE/);
  assert.equal(m.tone, 'stale');
});

test('runner-state gating', () => {
  const m = deriveMode(liveBase);
  assert.equal(controlState('start', m, { state: 'IDLE' }).enabled, true);
  assert.equal(controlState('start', m, { state: 'RUNNING' }).enabled, false);
  assert.equal(controlState('pause', m, { state: 'RUNNING' }).enabled, true);
  assert.equal(controlState('pause', m, { state: 'RUNNING', pause_requested: 'x' }).enabled, false);
  assert.equal(controlState('resume', m, { state: 'PAUSED' }).enabled, true);
  assert.equal(controlState('abort', m, { state: 'HOLD' }).enabled, true);
  assert.equal(controlState('abort', m, { state: 'COMPLETED' }).enabled, false);
  assert.equal(controlState('confirm', m, { state: 'AWAITING_CONFIRMATION' }).enabled, true);
  assert.equal(controlState('decide', m, { state: 'HOLD', hold: { allowed: ['retry'] } }).enabled, true);
  assert.equal(controlState('robot_state_cmd', m, { state: 'RUNNING', current: { attempt_id: 'T1_A1' } }).enabled, false);
  assert.match(controlState('manual', m, { state: 'RUNNING', current: { attempt_id: 'T1_A1' } }).reason, /departure/);
});

test('missing telemetry is never presented as standstill or zero motion', () => {
  const caps = { joint_telemetry: true };
  assert.match(motionLabel({ capabilities: caps, joint_freshness: 'stale', motion_state: 'still' }).text, /UNKNOWN/);
  assert.match(motionLabel({ capabilities: caps, joint_freshness: 'missing', motion_state: 'still' }).text, /UNKNOWN/);
  assert.match(motionLabel({ capabilities: { joint_telemetry: false } }).text, /NO ROBOT TELEMETRY/);
  const fresh = motionLabel({ capabilities: caps, joint_freshness: 'fresh', motion_state: 'still' }).text;
  assert.doesNotMatch(fresh, /STANDSTILL$/);
  assert.match(fresh, /criterion evaluated per attempt/);
});

test('D12 wording is a firmware report, not an electrical measurement', () => {
  assert.match(outputLabel(0), /commanded LOW.*not measured/);
  assert.match(outputLabel(null), /unknown/);
});

test('update-count model matches the firmware recurrence', () => {
  assert.equal(updatesToCross(0.1), 12);
  assert.equal(updatesToCross(0.3), 4);
  assert.equal(updatesToCross(0.5), 2);
});
