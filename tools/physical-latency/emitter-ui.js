/* Browser wiring: user actions only. Never opens a microphone or a network. */
'use strict';
(() => {
  const element = id => document.getElementById(id);
  const pad = element('pad');
  const emitter = new ROGPhysicalEmitter.Emitter({
    makeContext: options => {
      const Context = window.AudioContext || window.webkitAudioContext;
      if (!Context) throw new Error('audio unavailable');
      return new Context(options);
    },
    now: () => performance.now(),
    onChange: ({state, notice, events, hasReference, session}) => {
      element('status').textContent = notice;
      element('count').textContent = String(events);
      element('arm').disabled = state !== 'idle';
      element('stop').disabled = state === 'idle';
      element('level').disabled = state !== 'idle';
      element('system').disabled = state !== 'idle';
      element('verified').disabled = state !== 'idle';
      element('reference').disabled = !hasReference;
      element('context').textContent = session ?
        `Latest session: ${session.actualContextSampleRateHz} Hz AudioContext; ${session.levelDb} dBFS peak; requested application latency 100 ms. These are software parameters, not physical latency.` :
        'Audio parameters are unknown until armed. The external recorder has its own sample rate.';
      pad.disabled = state !== 'armed';
    }
  });
  element('arm').addEventListener('click', async event => {
    const armed = await emitter.arm(event, Number(element('level').value), {
      systemAlias: element('system').value, browserUserAgent: navigator.userAgent,
      operatorVerifiedInternalSpeakers: element('verified').checked});
    if (armed) pad.focus();
  });
  element('stop').addEventListener('click', () => emitter.stop());
  pad.addEventListener('keydown', event => {
    if (document.activeElement === pad && event.target === pad) emitter.keydown(event);
  });
  const download = (data, type, name) => {
    const blob = new Blob([data], {type});
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = name;
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  element('export').addEventListener('click', event => {
    if (!event.isTrusted) return;
    download(JSON.stringify(emitter.exportLog(), null, 2) + '\n', 'application/json', 'physical-emitter-diagnostic-log.json');
  });
  element('reference').addEventListener('click', event => {
    if (!event.isTrusted) return;
    const reference = emitter.exportReference();
    if (reference) download(reference, 'audio/wav', 'physical-emitter-chirp-reference.wav');
  });
  document.addEventListener('visibilitychange', () => { if (document.hidden) emitter.stop('hidden'); });
  window.addEventListener('blur', () => emitter.stop('window-blur'));
  window.addEventListener('pagehide', () => emitter.stop('page-exit'));
})();
