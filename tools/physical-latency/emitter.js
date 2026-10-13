/* Local diagnostic emitter. No capture, network or physical-latency inference. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.ROGPhysicalEmitter = api;
})(globalThis, function () {
  'use strict';
  const SIGNAL = Object.freeze({durationSeconds: 0.02, rampSeconds: 0.002,
    lowHz: 750, highHz: 3000});
  const MIN_GAP_MS = 750;
  const MAX_EVENTS = 2000;
  const LATENCY_HINT_SECONDS = 0.1;
  const finite = value => typeof value === 'number' && Number.isFinite(value) ? value : null;

  function signal(sampleRate, levelDb) {
    if (!Number.isInteger(sampleRate) || sampleRate < 8000 || sampleRate > 192000 ||
        finite(levelDb) === null || levelDb < -60 || levelDb > -30) {
      throw new RangeError('invalid signal parameters');
    }
    const length = Math.round(sampleRate * SIGNAL.durationSeconds);
    const ramp = Math.max(1, Math.round(sampleRate * SIGNAL.rampSeconds));
    const samples = new Float32Array(length);
    const amplitude = 10 ** (levelDb / 20);
    for (let i = 0; i < length; i++) {
      const t = i / sampleRate;
      const edge = Math.min(1, i / ramp, (length - 1 - i) / ramp);
      const envelope = 0.5 - 0.5 * Math.cos(Math.PI * edge);
      const phase = 2 * Math.PI * (SIGNAL.lowHz * t +
        (SIGNAL.highHz - SIGNAL.lowHz) * t * t / (2 * SIGNAL.durationSeconds));
      samples[i] = amplitude * envelope * Math.sin(phase);
    }
    return samples;
  }

  function referenceWave(samples, sampleRate) {
    // Non-PCM WAVE includes an extended format and fact sample count.
    const bytes = new Uint8Array(58 + samples.length * 8);
    const view = new DataView(bytes.buffer);
    const label = (offset, value) => { for (let i = 0; i < value.length; i++) bytes[offset + i] = value.charCodeAt(i); };
    label(0, 'RIFF'); view.setUint32(4, bytes.length - 8, true); label(8, 'WAVE');
    label(12, 'fmt '); view.setUint32(16, 18, true); view.setUint16(20, 3, true);
    view.setUint16(22, 2, true); view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 8, true); view.setUint16(32, 8, true); view.setUint16(34, 32, true);
    view.setUint16(36, 0, true);
    label(38, 'fact'); view.setUint32(42, 4, true); view.setUint32(46, samples.length, true);
    label(50, 'data'); view.setUint32(54, samples.length * 8, true);
    for (let i = 0; i < samples.length; i++) {
      view.setFloat32(58 + i * 8, samples[i], true);
      view.setFloat32(62 + i * 8, samples[i], true);
    }
    return bytes;
  }

  class Emitter {
    constructor({makeContext, now, onChange = () => {}}) {
      this.makeContext = makeContext;
      this.now = now;
      this.onChange = onChange;
      this.state = 'idle';
      this.generation = 0;
      this.context = null;
      this.warm = null;
      this.buffer = null;
      this.reference = null;
      this.sources = new Set();
      this.events = [];
      this.sessions = [];
      this.lastChirp = -Infinity;
      this.notice = 'Not armed. No audio context has been created.';
    }

    update(notice) {
      this.notice = notice;
      this.onChange({state: this.state, notice, events: this.events.length,
        hasReference: this.reference !== null,
        session: this.sessions.length ? {...this.sessions.at(-1)} : null});
    }

    record(kind, fields = {}) {
      if (this.events.length >= MAX_EVENTS) return false;
      this.events.push({sequence: this.events.length + 1, kind,
        pageNowMs: finite(this.now()), ...fields});
      return true;
    }

    async arm(event, levelDb, metadata = {}) {
      if (!event || event.isTrusted !== true || this.state !== 'idle') return false;
      if (this.events.length >= MAX_EVENTS - 2) {
        this.update('Event limit reached. Export this log and reload for a new set.');
        return false;
      }
      const generation = ++this.generation;
      this.state = 'arming';
      this.update('Starting the owned silent warm stream. No chirp yet.');
      try {
        // Validate level before creating any browser audio resource.
        signal(48000, levelDb);
        const context = this.makeContext({latencyHint: LATENCY_HINT_SECONDS});
        this.context = context;
        await context.resume();
        if (generation !== this.generation || this.state !== 'arming') return false;
        if (context.state !== 'running') throw new Error('context not running');
        const samples = signal(context.sampleRate, levelDb);
        const buffer = context.createBuffer(2, samples.length, context.sampleRate);
        buffer.copyToChannel(samples, 0);
        buffer.copyToChannel(samples, 1);
        this.buffer = buffer;
        this.reference = referenceWave(samples, context.sampleRate);
        const warm = context.createConstantSource();
        this.warm = warm;
        warm.offset.value = 0;
        warm.connect(context.destination);
        warm.start();
        this.lastChirp = -Infinity;
        this.sessions.push({session: this.sessions.length + 1,
          systemAlias: ['rog', 'thinkpad', 'm4-air'].includes(metadata.systemAlias) ? metadata.systemAlias : 'unspecified',
          browserUserAgent: String(metadata.browserUserAgent || '').slice(0, 512),
          operatorVerifiedInternalSpeakers: metadata.operatorVerifiedInternalSpeakers === true,
          requestedLatencyHintSeconds: LATENCY_HINT_SECONDS,
          actualContextSampleRateHz: context.sampleRate, levelDb,
          referenceWaveFormat: 'stereo-little-endian-ieee-float32-wav',
          baseLatencySeconds: finite(context.baseLatency),
          outputLatencySeconds: finite(context.outputLatency),
          outputRoute: 'existing-default-not-programmatically-verified',
          timingScope: 'browser-diagnostic-estimates-not-physical-delay'});
        this.state = 'armed';
        context.onstatechange = () => {
          if (this.context === context && this.state === 'armed' && context.state !== 'running') this.stop('context-not-running');
        };
        this.record('armed', {session: this.sessions.length});
        this.update('Armed. Focus the test pad and press Space once. Switching windows disarms.');
        return true;
      } catch (_) {
        if (generation === this.generation) {
          await this.stop('arm-failed');
          this.record('arm-failed');
          this.update('Audio could not start. No chirp emitted; check browser support and arm again.');
        }
        return false;
      }
    }

    keydown(event) {
      if (this.state !== 'armed' || !event || event.isTrusted !== true ||
          event.repeat || event.isComposing || event.code !== 'Space' ||
          event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return false;
      event.preventDefault();
      if (this.context.state !== 'running') {
        this.stop('context-not-running');
        return false;
      }
      if (this.events.length >= MAX_EVENTS - 1) {
        this.stop('event-limit');
        return false;
      }
      const pageNowMs = this.now();
      if (pageNowMs - this.lastChirp < MIN_GAP_MS) {
        this.record('keypress-not-emitted', {reason: 'minimum-gap', eventTimeStampMs: finite(event.timeStamp)});
        this.update('Presses must be at least 750 ms apart; this press emitted no chirp.');
        return false;
      }
      let source = null;
      try {
        source = this.context.createBufferSource();
        source.buffer = this.buffer;
        source.connect(this.context.destination);
        this.sources.add(source);
        source.onended = () => { this.sources.delete(source); source.disconnect(); };
        const contextStartSeconds = this.context.currentTime;
        source.start(contextStartSeconds);
        this.lastChirp = pageNowMs;
        this.record('keypress-chirp', {session: this.sessions.length,
          eventTimeStampMs: finite(event.timeStamp), contextStartSeconds: finite(contextStartSeconds),
          contextState: this.context.state});
        this.update('One chirp requested. The log is diagnostic; the phone recording supplies the measurement.');
        return true;
      } catch (_) {
        if (source) {
          this.sources.delete(source);
          try { source.stop(); } catch (_) {}
          try { source.disconnect(); } catch (_) {}
        }
        this.record('chirp-failed');
        this.stop('chirp-failed');
        return false;
      }
    }

    async stop(reason = 'operator') {
      if (this.state === 'stopping') return;
      ++this.generation;
      const wasActive = this.state !== 'idle';
      const context = this.context;
      this.context = null;
      this.state = 'stopping';
      for (const source of this.sources) {
        try { source.stop(); } catch (_) {}
        try { source.disconnect(); } catch (_) {}
      }
      this.sources.clear();
      if (this.warm) {
        try { this.warm.stop(); } catch (_) {}
        try { this.warm.disconnect(); } catch (_) {}
      }
      this.warm = null;
      this.buffer = null;
      if (wasActive) this.record('disarmed', {reason: ['operator', 'hidden', 'window-blur', 'page-exit',
        'context-not-running', 'arm-failed', 'chirp-failed', 'event-limit'].includes(reason) ? reason : 'operator'});
      this.update('Disarmed. Owned audio resources are closing; other media is untouched.');
      if (context) { try { await context.close(); } catch (_) {} }
      this.state = 'idle';
      this.update('Disarmed. No owned source is connected; other media is untouched.');
    }

    exportLog() {
      return JSON.parse(JSON.stringify({schema_version: 1, kind: 'physical-emitter-diagnostic-log',
        evidence_class: 'browser-software-diagnostics', physical_latency_ms: null,
        scope: 'physical-key-click-to-speaker-chirp-requires-external-recording',
        signal: {...SIGNAL, channels: 2, rampShape: 'raised-cosine', format: 'float32'},
        limits: {minimumKeyGapMs: MIN_GAP_MS, maximumEvents: MAX_EVENTS,
          continuousSilentWarmStream: true, microphoneAccess: false, networkRequests: false,
          powerBaseline: false, keyboardPhysicalOriginVerifiedByBrowser: false},
        sessions: this.sessions, events: this.events}));
    }

    exportReference() { return this.reference === null ? null : this.reference.slice(); }
  }
  return Object.freeze({Emitter, signal, SIGNAL, MIN_GAP_MS, MAX_EVENTS, LATENCY_HINT_SECONDS});
});
