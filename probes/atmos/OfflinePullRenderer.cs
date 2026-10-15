using System.Diagnostics;
using Cavern;
using Cavern.Format.Renderers;
using Cavern.Format.Utilities;

namespace AtmosProbe;

/// <summary>Sample PTS is an integer in a 1/48000 timebase. EOF has Frames=0.</summary>
public readonly record struct PullRead(long SamplePts, int Frames, long Epoch, bool EndOfStream);

/// <summary>
/// Bounded offline renderer. One active context owns Cavern's process-global layout.
/// It never opens devices. Call Dispose before opening another context.
/// </summary>
public sealed class OfflinePullRenderer : IDisposable {
    public const int SampleRate = 48000, DspFrames = 256, MaximumReadFrames = 4096;
    public const int MaximumCommands = 4096, MaximumDspBlocks = 67500;
    static readonly object Gate = new();
    static OfflinePullRenderer? active;
    readonly Func<Engine> factory;
    readonly int commandLimit, blockLimit, startupBlocks;
    Engine? engine;
    float[] pending = [];
    int pendingOffset, pendingFrames, commands, workBlocks;
    long position, epoch;
    bool disposed, faulted;
    long dspTicks, dspAllocated, maximumBlockTicks, maximumBlockAllocated;
    int renderedBlocks;
    public int Length { get; }
    public int Channels { get; }
    public bool HasObjects { get; private set; }
    public string RendererName { get; private set; } = "";
    internal ObservedDecoder? Decoder => engine?.Decoder;
    public long Position { get { lock (Gate) { EnsureActive(); return position; } } }
    public long Epoch { get { lock (Gate) { EnsureActive(); return epoch; } } }
    public object Profile { get { lock (Gate) { return new {
        rendered_blocks = renderedBlocks, charged_work_blocks = workBlocks, commands,
        dsp_elapsed_ms = dspTicks * 1000.0 / Stopwatch.Frequency,
        dsp_allocated_bytes = dspAllocated, block_samples = DspFrames,
        maximum_block_ms = maximumBlockTicks * 1000.0 / Stopwatch.Frequency,
        maximum_block_allocated_bytes = maximumBlockAllocated,
        evidence = "build-host offline block calls only; excludes setup, replay setup and WAV I/O; allocations are approximate process-wide deltas; includes discard-forward blocks; not physical latency or realtime qualification"
    }; } } }

    /// <summary>
    /// Snapshot explicit bytes, validate and open. Layout: stereo-speakers or 7.1.4.
    /// Reduced limits allow callers to enforce stricter cumulative work budgets.
    /// Encoded startup is conservatively charged six blocks per decoder rebuild.
    /// </summary>
    public static OfflinePullRenderer Open(byte[] input, bool synthetic, string layout = "stereo-speakers",
        int maximumCommands = MaximumCommands, int maximumDspBlocks = MaximumDspBlocks) {
        ArgumentNullException.ThrowIfNull(input);
        if (input.Length is <= 0 or > 67108864) throw new InvalidInput("input_size_limit");
        if (layout is not ("stereo-speakers" or "7.1.4")) throw new Unsupported("unsupported_layout");
        if (maximumCommands is < 1 or > MaximumCommands || maximumDspBlocks is < 1 or > MaximumDspBlocks)
            throw new InvalidInput("pull_limits");
        lock (Gate) {
            if (active != null) throw new InvalidOperationException("active_render_context");
            // Snapshot once: later mutation by the caller cannot change a seek's source.
            byte[] bytes = (byte[])input.Clone();
            Func<Engine> factory;
            int length;
            if (synthetic) {
                Program.Scene scene;
                try { scene = Program.ParseScene(bytes); }
                catch (System.Text.Json.JsonException) { throw new InvalidInput("scene_json"); }
                length = scene.samples;
                float[][] clips = scene.objects.Select(obj => Enumerable.Range(0, length)
                    .Select(i => obj.amplitude * MathF.Sin(2 * MathF.PI * obj.frequency_hz * i / SampleRate)).ToArray()).ToArray();
                factory = () => Engine.Synthetic(scene, clips, layout);
            } else {
                var scan = Program.Scan(bytes);
                length = scan.samples;
                factory = () => Engine.Encoded(bytes, scan.frameSamples, scan.frames, layout);
            }
            var result = new OfflinePullRenderer(factory, length, layout == "7.1.4" ? 12 : 2,
                maximumCommands, maximumDspBlocks, synthetic ? 0 : 6);
            active = result;
            try { result.Rebuild(); return result; }
            catch { result.Dispose(); throw; }
        }
    }

    OfflinePullRenderer(Func<Engine> factory, int length, int channels, int commandLimit, int blockLimit, int startupBlocks) {
        this.factory = factory; Length = length; Channels = channels;
        this.commandLimit = commandLimit; this.blockLimit = blockLimit; this.startupBlocks = startupBlocks;
    }

    /// <summary>
    /// Copies up to requestedFrames into the beginning of caller-owned interleaved PCM.
    /// Only Frames*Channels elements are written; the rest is untouched. No returned
    /// buffer aliases DSP memory. A failed read may have written a prefix; discard it.
    /// </summary>
    public PullRead Read(float[] destination, int requestedFrames) {
        lock (Gate) {
            EnsureActive(); ChargeCommand();
            ArgumentNullException.ThrowIfNull(destination);
            if (requestedFrames is < 1 or > MaximumReadFrames || destination.Length < requestedFrames * Channels)
                throw new InvalidInput("pull_read_size");
            long pts = position;
            int frames = (int)Math.Min(requestedFrames, Length - position);
            int neededBlocks = Math.Max(0, (frames - pendingFrames + DspFrames - 1) / DspFrames);
            if (neededBlocks > blockLimit - workBlocks) throw new InvalidInput("pull_work_limit");
            try {
                int written = 0;
                while (written < frames) {
                    Fill();
                    int copy = Math.Min(frames - written, pendingFrames);
                    Array.Copy(pending, pendingOffset * Channels, destination, written * Channels, copy * Channels);
                    Consume(copy); written += copy;
                }
                return new PullRead(pts, frames, epoch, position == Length);
            } catch { Fail(); throw; }
        }
    }

    /// <summary>Rebuild from frame zero and discard forward. Epoch increments even at the same PTS.</summary>
    public void Seek(long samplePts) {
        lock (Gate) {
            EnsureActive(); ChargeCommand();
            if (samplePts < 0 || samplePts > Length) throw new InvalidInput("pull_seek_range");
            // Reserve all required work before discarding a usable renderer.
            int replayBlocks = checked((int)((samplePts + DspFrames - 1) / DspFrames));
            if (startupBlocks + replayBlocks > blockLimit - workBlocks) throw new InvalidInput("pull_work_limit");
            try {
                ReleaseEngine(); Rebuild(); position = 0; epoch++;
                while (position < samplePts) {
                    Fill(); Consume((int)Math.Min(samplePts - position, pendingFrames));
                }
            } catch { Fail(); throw; }
        }
    }

    /// <summary>Replay to current PTS to restore metadata and filter history; increment epoch.</summary>
    public void Flush() { lock (Gate) { EnsureActive(); Seek(position); } }

    void ChargeCommand() {
        if (commands == commandLimit) throw new InvalidInput("pull_command_limit");
        commands++; // Invalid requests count as commands, preventing free retry loops.
    }
    void ChargeWork(int blocks) {
        if (blocks > blockLimit - workBlocks) throw new InvalidInput("pull_work_limit");
        workBlocks += blocks;
    }
    void Rebuild() {
        ChargeWork(startupBlocks);
        engine = factory();
        HasObjects = engine.Decoder?.HasObjects ?? false;
        RendererName = "Cavern.Listener/" + Listener.Renderer.GetType().Name;
        pending = []; pendingOffset = pendingFrames = 0;
    }
    void Fill() {
        if (pendingFrames != 0) return;
        ChargeWork(1);
        long beforeAlloc = GC.GetTotalAllocatedBytes(false), beforeTime = Stopwatch.GetTimestamp();
        try { pending = engine!.Render((int)position); }
        finally {
            long ticks = Stopwatch.GetTimestamp() - beforeTime;
            long allocated = Math.Max(0, GC.GetTotalAllocatedBytes(false) - beforeAlloc);
            dspTicks += ticks; dspAllocated += allocated;
            maximumBlockTicks = Math.Max(maximumBlockTicks, ticks);
            maximumBlockAllocated = Math.Max(maximumBlockAllocated, allocated);
            renderedBlocks++;
        }
        int frames = (int)Math.Min(DspFrames, Length - position);
        if (pending.Length < frames * Channels) throw new InvalidInput("render_length");
        for (int i = 0; i < frames * Channels; i++) {
            float value = pending[i];
            if (!float.IsFinite(value)) throw new InvalidInput("nonfinite_render");
            if (Math.Abs(value) > 1) throw new Unsupported("render_clipping");
        }
        engine!.Verify(position + frames == Length);
        pendingOffset = 0; pendingFrames = frames;
    }
    void Consume(int count) { position += count; pendingOffset += count; pendingFrames -= count; }
    void EnsureActive() {
        ObjectDisposedException.ThrowIf(disposed, this);
        if (faulted) throw new InvalidOperationException("faulted_render_context");
        if (!ReferenceEquals(active, this)) throw new InvalidOperationException("inactive_render_context");
    }
    void ReleaseEngine() {
        Engine? previous = engine; engine = null;
        pending = []; pendingOffset = pendingFrames = 0;
        previous?.Dispose();
    }
    void Fail() { faulted = true; ReleaseEngine(); }
    public void Dispose() {
        lock (Gate) {
            if (disposed) return;
            disposed = true;
            try { ReleaseEngine(); }
            finally { if (ReferenceEquals(active, this)) active = null; }
        }
    }

    sealed class Engine : IDisposable {
        readonly Listener listener;
        readonly Action<int> update;
        readonly Renderer? renderer;
        readonly MemoryStream? stream;
        readonly int expectedFrames;
        public ObservedDecoder? Decoder { get; }
        Engine(Listener listener, Action<int> update, Renderer? renderer = null,
            MemoryStream? stream = null, ObservedDecoder? decoder = null, int expectedFrames = 0) {
            this.listener = listener; this.update = update; this.renderer = renderer;
            this.stream = stream; Decoder = decoder; this.expectedFrames = expectedFrames;
        }
        public static Engine Synthetic(Program.Scene scene, float[][] clips, string layout) {
            Listener listener = Program.ListenerFor(layout, SampleRate);
            var sources = new List<Source>();
            try {
                for (int i = 0; i < scene.objects.Length; i++) {
                    var source = new Source { Clip = new Clip(clips[i], 1, SampleRate), VolumeRolloff = Rolloffs.Disabled,
                        Position = Program.Position(scene.objects[i], 0) };
                    sources.Add(source); listener.AttachSource(source);
                }
                return new Engine(listener, sample => {
                    for (int i = 0; i < sources.Count; i++) sources[i].Position = Program.Position(scene.objects[i], sample);
                });
            } catch { listener.DetachAllSources(); throw; }
        }
        public static Engine Encoded(byte[] bytes, int frameSamples, int frames, string layout) {
            var stream = new MemoryStream(bytes, false);
            Listener? listener = null; Renderer? renderer = null;
            try {
                var decoder = new ObservedDecoder(BlockBuffer<byte>.Create(stream));
                decoder.Seed(frames);
                if (decoder.SampleRate != SampleRate || decoder.FrameSize != frameSamples || decoder.ChannelCount is < 1 or > 8)
                    throw new Unsupported("decoder_configuration");
                bool objects = decoder.HasObjects;
                decoder.RequireObjects = objects; decoder.RejectObjects = !objects;
                listener = Program.ListenerFor(layout, SampleRate);
                renderer = objects ? new EnhancedAC3Renderer(decoder) : new BedRenderer(decoder);
                listener.AttachSources(renderer.Objects);
                return new Engine(listener, _ => { }, renderer, stream, decoder, frames);
            } catch {
                listener?.DetachAllSources();
                try { renderer?.Dispose(); } finally { stream.Dispose(); }
                throw;
            }
        }
        public float[] Render(int sample) { update(sample); return listener.Render(); }
        public void Verify(bool final) {
            if (Decoder?.RequireObjects == true) {
                Decoder.VerifyNoSparse();
                if (final && Decoder.ObjectFrames != expectedFrames) throw new Unsupported("object_metadata_not_continuous");
            }
        }
        public void Dispose() {
            listener.DetachAllSources();
            try { renderer?.Dispose(); } finally { stream?.Dispose(); }
        }
    }
}
