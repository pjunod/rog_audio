/* Synthetic AudioContext/DOM only. Each selected case executes once. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const api = require('../tools/physical-latency/emitter.js');

class FakeNode {
  constructor() { this.offset = {value: 1}; this.connected = false; this.started = false; this.stopped = false; }
  connect(destination) { this.connected = true; this.destination = destination; }
  disconnect() { this.connected = false; }
  start(when) { this.started = true; this.startTime = when; }
  stop() { this.stopped = true; }
}
class FakeContext {
  constructor(rate = 48000) {
    this.sampleRate = rate; this.state = 'suspended'; this.currentTime = 10.25;
    this.baseLatency = 0.1; this.outputLatency = undefined;
    this.destination = {}; this.warms = []; this.sources = []; this.closed = false;
  }
  async resume() { this.state = 'running'; }
  async close() { this.closed = true; this.state = 'closed'; if (this.onstatechange) this.onstatechange(); }
  createBuffer(channels, length, rate) {
    return {channels: Array.from({length: channels}, () => new Float32Array(length)), sampleRate: rate,
      copyToChannel(samples, index) { this.channels[index].set(samples); }};
  }
  createConstantSource() { const node = new FakeNode(); this.warms.push(node); return node; }
  createBufferSource() { const node = new FakeNode(); this.sources.push(node); return node; }
}
function fixture(context = new FakeContext()) {
  let time = 1000; const contexts = []; const changes = [];
  const emitter = new api.Emitter({makeContext: options => { contexts.push(options); return context; },
    now: () => time, onChange: state => changes.push(state)});
  return {emitter, context, contexts, changes, advance: amount => { time += amount; }};
}
function press(overrides = {}) {
  return {isTrusted: true, repeat: false, code: 'Space', timeStamp: 1000,
    preventDefault() { this.prevented = true; }, ...overrides};
}
const trustedClick = () => ({isTrusted: true});
const metadata = {systemAlias: 'rog', browserUserAgent: 'synthetic-browser', operatorVerifiedInternalSpeakers: true};

const cases = {
  async no_autoplay_and_invalid_arm() {
    const f = fixture();
    assert.equal(f.contexts.length, 0);
    assert.equal(f.emitter.keydown(press()), false);
    assert.equal(await f.emitter.arm({isTrusted: false}, -60, metadata), false);
    assert.equal(f.contexts.length, 0);
    assert.equal(await f.emitter.arm(trustedClick(), 0, metadata), false);
    assert.equal(f.contexts.length, 0);
    assert.equal(f.emitter.state, 'idle');
    assert.equal(f.emitter.exportLog().physical_latency_ms, null);
  },
  async signal_bounds_taper_and_actual_rate() {
    for (const rate of [8000, 44100, 48000, 96000, 192000]) {
      const samples = api.signal(rate, -30);
      assert.equal(samples.length, Math.round(rate * 0.02));
      assert.equal(samples[0], 0); assert.equal(Math.abs(samples.at(-1)), 0);
      assert.ok(samples.some(x => Math.abs(x) > 0.005));
      assert.ok(samples.every(x => Number.isFinite(x) && Math.abs(x) <= 10 ** (-30 / 20) + 1e-8));
      assert.ok(Math.max(...samples.slice(0, Math.max(1, Math.round(rate * 0.0005))).map(Math.abs)) < 0.005);
    }
    for (const [rate, level] of [[true, -60], [0, -60], [48000, NaN], [48000, -61], [48000, -29]]) {
      assert.throws(() => api.signal(rate, level), RangeError);
    }
    const f = fixture(new FakeContext(44100)); await f.emitter.arm(trustedClick(), -48, metadata);
    assert.equal(f.emitter.buffer.sampleRate, 44100);
    assert.deepEqual(f.emitter.buffer.channels[0], f.emitter.buffer.channels[1]);
    assert.equal(f.emitter.buffer.channels[0].length, 882);
  },
  async trusted_key_repeat_modifiers_and_cooldown() {
    const f = fixture(); await f.emitter.arm(trustedClick(), -60, metadata);
    for (const overrides of [{isTrusted: false}, {repeat: true}, {code: 'Enter'}, {isComposing: true},
      {altKey: true}, {ctrlKey: true}, {metaKey: true}, {shiftKey: true}]) {
      assert.equal(f.emitter.keydown(press(overrides)), false);
    }
    assert.equal(f.context.sources.length, 0);
    assert.equal(f.emitter.keydown(press()), true);
    f.advance(749); assert.equal(f.emitter.keydown(press()), false);
    f.advance(1); assert.equal(f.emitter.keydown(press()), true);
    assert.equal(f.context.sources.length, 2);
    assert.equal(f.emitter.exportLog().events.filter(x => x.kind === 'keypress-not-emitted').length, 1);
    const node = f.context.sources[0]; node.onended();
    assert.equal(node.connected, false);
    assert.equal(f.emitter.sources.has(node), false);
  },
  async warm_stream_log_is_diagnostic_and_export_is_detached() {
    const f = fixture(); await f.emitter.arm(trustedClick(), -42, metadata);
    assert.equal(f.context.warms.length, 1);
    assert.equal(f.context.warms[0].offset.value, 0);
    assert.equal(f.context.warms[0].started, true);
    assert.equal(f.context.sources.length, 0);
    assert.deepEqual(f.contexts, [{latencyHint: 0.1}]);
    f.emitter.keydown(press({timeStamp: Infinity}));
    const log = f.emitter.exportLog();
    assert.equal(log.physical_latency_ms, null);
    assert.equal(log.sessions[0].actualContextSampleRateHz, 48000);
    assert.equal(log.sessions[0].outputLatencySeconds, null);
    assert.equal(log.events.find(x => x.kind === 'keypress-chirp').eventTimeStampMs, null);
    assert.equal(log.events.find(x => x.kind === 'keypress-chirp').contextStartSeconds, 10.25);
    assert.equal(log.limits.powerBaseline, false);
    assert.equal(log.limits.microphoneAccess, false);
    assert.equal(log.limits.keyboardPhysicalOriginVerifiedByBrowser, false);
    log.sessions[0].systemAlias = 'changed'; log.events.length = 0;
    assert.equal(f.emitter.exportLog().sessions[0].systemAlias, 'rog');
    assert.ok(f.emitter.exportLog().events.length > 0);
  },
  async reference_wave_is_actual_preloaded_stereo_signal() {
    const f = fixture(new FakeContext(44100));
    assert.equal(f.emitter.exportReference(), null);
    await f.emitter.arm(trustedClick(), -48, metadata);
    const bytes = f.emitter.exportReference(); const view = new DataView(bytes.buffer);
    assert.equal(Buffer.from(bytes.slice(0, 4)).toString(), 'RIFF');
    assert.equal(Buffer.from(bytes.slice(8, 12)).toString(), 'WAVE');
    assert.equal(view.getUint16(20, true), 3); assert.equal(view.getUint16(22, true), 2);
    assert.equal(view.getUint32(24, true), 44100); assert.equal(view.getUint16(34, true), 32);
    assert.equal(view.getUint32(16, true), 18);
    assert.equal(Buffer.from(bytes.slice(38, 42)).toString(), 'fact');
    assert.equal(view.getUint32(46, true), 882);
    assert.equal(Buffer.from(bytes.slice(50, 54)).toString(), 'data');
    assert.equal(view.getUint32(54, true), 882 * 8);
    assert.equal(bytes.length, 58 + 882 * 8);
    for (let i = 0; i < 882; i++) {
      assert.equal(view.getFloat32(58 + i * 8, true), f.emitter.buffer.channels[0][i]);
      assert.equal(view.getFloat32(62 + i * 8, true), f.emitter.buffer.channels[1][i]);
    }
    bytes[0] = 0; assert.equal(f.emitter.exportReference()[0], 'R'.charCodeAt(0));
    assert.equal(f.context.sources.length, 0);
    await f.emitter.stop(); assert.ok(f.emitter.exportReference());
  },
  async stop_cancels_owned_nodes_without_touching_other_audio() {
    const unrelated = new FakeContext(); unrelated.state = 'running';
    const f = fixture(); await f.emitter.arm(trustedClick(), -60, metadata); f.emitter.keydown(press());
    await f.emitter.stop('hidden');
    assert.equal(f.emitter.state, 'idle'); assert.equal(f.context.closed, true);
    assert.ok([...f.context.warms, ...f.context.sources].every(x => x.stopped && !x.connected));
    assert.equal(unrelated.closed, false); assert.equal(unrelated.state, 'running');
    assert.equal(f.emitter.keydown(press()), false);
    assert.equal(f.emitter.exportLog().events.at(-1).reason, 'hidden');
  },
  async pending_arm_cancel_and_stale_state_event() {
    const first = new FakeContext(); let resolve;
    first.resume = () => new Promise(r => { resolve = r; });
    const f = fixture(first); const pending = f.emitter.arm(trustedClick(), -60, metadata);
    await f.emitter.stop('window-blur'); first.state = 'running'; resolve();
    assert.equal(await pending, false); assert.equal(first.warms.length, 0);
    const second = new FakeContext(); f.emitter.makeContext = () => second;
    await f.emitter.arm(trustedClick(), -60, metadata);
    const oldCallback = second.onstatechange;
    await f.emitter.stop();
    const third = new FakeContext(); f.emitter.makeContext = () => third;
    await f.emitter.arm(trustedClick(), -60, metadata); oldCallback();
    assert.equal(f.emitter.state, 'armed'); assert.equal(third.closed, false);
  },
  async failures_do_not_leave_warm_or_chirp_sources() {
    const bad = new FakeContext(); bad.resume = async () => { throw new Error('synthetic private payload'); };
    const f = fixture(bad); assert.equal(await f.emitter.arm(trustedClick(), -60, metadata), false);
    assert.equal(bad.closed, true); assert.equal(bad.warms.length, 0);
    assert.ok(!JSON.stringify(f.emitter.exportLog()).includes('synthetic private payload'));
    const good = new FakeContext(); good.createBufferSource = () => {
      const node = new FakeNode(); node.start = () => { throw new Error('synthetic failure'); }; good.sources.push(node); return node;
    };
    f.emitter.makeContext = () => good; await f.emitter.arm(trustedClick(), -60, metadata);
    assert.equal(f.emitter.keydown(press()), false);
    await Promise.resolve();
    assert.equal(good.closed, true); assert.ok(good.warms.every(x => x.stopped && !x.connected));
    assert.ok(good.sources.every(x => x.stopped && !x.connected));
  },
  async close_in_progress_blocks_rearm_and_event_limit_stops() {
    const f = fixture(); await f.emitter.arm(trustedClick(), -60, metadata);
    let resolve; f.context.close = () => new Promise(r => { resolve = r; });
    const stopping = f.emitter.stop();
    assert.equal(f.emitter.state, 'stopping');
    assert.equal(await f.emitter.arm(trustedClick(), -60, metadata), false);
    resolve(); await stopping;
    const g = fixture(); await g.emitter.arm(trustedClick(), -60, metadata);
    for (let i = 0; i < api.MAX_EVENTS + 5; i++) {
      g.advance(1000); g.emitter.keydown(press());
      for (const node of [...g.emitter.sources]) node.onended();
    }
    await Promise.resolve();
    assert.equal(g.context.closed, true);
    assert.equal(g.emitter.exportLog().events.length, api.MAX_EVENTS);
    assert.equal(g.emitter.exportLog().events.at(-1).reason, 'event-limit');
  },
  async browser_wiring_focus_and_hidden_disarm_without_autoplay() {
    const nodes = new Map(); const listeners = {};
    for (const id of ['pad', 'status', 'context', 'count', 'arm', 'stop', 'level', 'system', 'verified', 'export', 'reference']) {
      nodes.set(id, {value: id === 'level' ? '-60' : 'rog', checked: true, disabled: false,
        addEventListener(type, fn) { this[type] = fn; }, focus() { document.activeElement = this; }});
    }
    const contexts = [];
    const document = {activeElement: null, hidden: false, getElementById: id => nodes.get(id),
      addEventListener: (type, fn) => { listeners[type] = fn; }};
    const window = {AudioContext: class extends FakeContext { constructor() { super(); contexts.push(this); } },
      addEventListener: (type, fn) => { listeners[type] = fn; }};
    const sandbox = {document, window, ROGPhysicalEmitter: api, performance: {now: () => 1000},
      navigator: {userAgent: 'synthetic-browser'}};
    vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../tools/physical-latency/emitter-ui.js'), 'utf8'), sandbox);
    assert.equal(contexts.length, 0);
    await nodes.get('arm').click(trustedClick());
    const pad = nodes.get('pad'); assert.equal(document.activeElement, pad);
    document.activeElement = nodes.get('system'); pad.keydown(press({target: pad}));
    assert.equal(contexts[0].sources.length, 0);
    document.activeElement = pad; pad.keydown(press({target: pad}));
    assert.equal(contexts[0].sources.length, 1);
    document.hidden = true; listeners.visibilitychange(); await Promise.resolve();
    assert.equal(contexts[0].closed, true);
    assert.equal(nodes.get('arm').disabled, false);
    assert.equal(nodes.get('pad').disabled, true);
  }
};

const name = process.argv[2];
if (!Object.hasOwn(cases, name)) throw new Error('invalid case selector');
cases[name]().then(() => { process.stdout.write(JSON.stringify({case: name, passed: true}) + '\n'); })
  .catch(error => { process.stderr.write(error.stack + '\n'); process.exitCode = 1; });
