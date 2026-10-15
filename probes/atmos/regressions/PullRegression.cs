using System.Reflection;
using System.Runtime.ExceptionServices;
using System.Text.Json;

static partial class Regression {
    static readonly Assembly Probe = Assembly.LoadFrom(Path.Combine(AppContext.BaseDirectory, "..", "AtmosProbe.dll"));
    static readonly Type PullType = Probe.GetType("AtmosProbe.OfflinePullRenderer", true)!;
    static byte[] PullScene(int samples = 8197) => JsonSerializer.SerializeToUtf8Bytes(new {
        schema_version = 1, sample_rate = 48000, samples,
        objects = new[] { new { amplitude = .125, frequency_hz = 997,
            keyframes = new[] { new { sample = 0, position = new[] { -1, 0, 1 } },
                new { sample = samples - 1, position = new[] { 1, 1, -1 } } } } }
    });
    static object? Invoke(MethodInfo method, object? target, params object?[] args) {
        try { return method.Invoke(target, args); }
        catch (TargetInvocationException ex) when (ex.InnerException != null) {
            ExceptionDispatchInfo.Capture(ex.InnerException).Throw(); throw;
        }
    }
    static object Prop(object obj, string name) => obj.GetType().GetProperty(name)!.GetValue(obj)!;
    static void Reject(Action action, string message) {
        try { action(); }
        catch (Exception ex) when (ex.Message == message) { return; }
        throw new InvalidOperationException("expected rejection: " + message);
    }
    sealed class PullHandle : IDisposable {
        public readonly object Value;
        public int Channels => (int)Prop(Value, "Channels");
        public long Position => (long)Prop(Value, "Position");
        public long Epoch => (long)Prop(Value, "Epoch");
        public PullHandle(byte[]? scene = null, string layout = "7.1.4", int commands = 4096, int blocks = 67500) {
            Value = Invoke(PullType.GetMethod("Open")!, null, scene ?? PullScene(), true, layout, commands, blocks)!;
        }
        public object Read(float[] buffer, int frames) => Invoke(PullType.GetMethod("Read")!, Value, buffer, frames)!;
        public void Seek(long pts) => Invoke(PullType.GetMethod("Seek")!, Value, pts);
        public void Flush() => Invoke(PullType.GetMethod("Flush")!, Value);
        public void Dispose() => ((IDisposable)Value).Dispose();
    }
    static float[] PullAll(byte[] scene, int[] sizes) {
        using var pull = new PullHandle(scene);
        var pcm = new List<float>();
        int round = 0;
        while (true) {
            int request = sizes[round++ % sizes.Length];
            float[] buffer = Enumerable.Repeat(12345f, request * pull.Channels + 7).ToArray();
            object result = pull.Read(buffer, request);
            int frames = (int)Prop(result, "Frames");
            Check((long)Prop(result, "SamplePts") == pcm.Count / pull.Channels, "sample PTS drift");
            Check((long)Prop(result, "Epoch") == 0, "unexpected epoch");
            Check(buffer.Skip(frames * pull.Channels).All(x => x == 12345f), "caller suffix changed");
            pcm.AddRange(buffer.Take(frames * pull.Channels));
            if (frames == 0) {
                Check((bool)Prop(result, "EndOfStream"), "EOF flag missing");
                break;
            }
        }
        return pcm.ToArray();
    }
    static void PullContinuation() {
        byte[] scene = PullScene(4101);
        float[] baseline = PullAll(scene, [256]);
        float[] split = PullAll(scene, [1, 17, 255, 257, 4096]);
        Check(baseline.Length == 4101 * 12 && baseline.SequenceEqual(split), "split-read continuation differs");
        using var pull = new PullHandle(scene);
        Array.Fill(scene, (byte)0); // An opened input owns a stable snapshot.
        float[] buffer = new float[37 * 12];
        pull.Read(buffer, 37);
        float[] saved = (float[])buffer.Clone();
        pull.Read(new float[4096 * 12], 4096);
        Check(buffer.SequenceEqual(saved) && buffer.SequenceEqual(baseline.Take(buffer.Length)), "caller buffer aliased or source mutated");
    }
    static void PullSeekFlushEof() {
        byte[] scene = PullScene();
        float[] baseline = PullAll(scene, [4096]);
        using var pull = new PullHandle(scene);
        pull.Read(new float[123 * 12], 123);
        pull.Seek(765);
        float[] buffer = new float[777 * 12];
        object result = pull.Read(buffer, 777);
        Check((long)Prop(result, "SamplePts") == 765 && (long)Prop(result, "Epoch") == 1, "seek timestamp/epoch");
        Check(buffer.SequenceEqual(baseline.Skip(765 * 12).Take(buffer.Length)), "seek lost filter/position history");
        long at = pull.Position;
        pull.Flush();
        result = pull.Read(buffer, 777);
        Check((long)Prop(result, "SamplePts") == at && (long)Prop(result, "Epoch") == 2, "flush timestamp/epoch");
        Check(buffer.SequenceEqual(baseline.Skip((int)at * 12).Take(buffer.Length)), "flush lost history");
        pull.Seek(8196);
        float[] tail = Enumerable.Repeat(12345f, 4 * 12).ToArray();
        result = pull.Read(tail, 4);
        Check((int)Prop(result, "Frames") == 1 && (bool)Prop(result, "EndOfStream"), "partial EOS not trimmed");
        Check(tail.Take(12).SequenceEqual(baseline.Skip(8196 * 12)) && tail.Skip(12).All(x => x == 12345), "EOS buffer extent");
        for (int i = 0; i < 2; i++) {
            result = pull.Read(tail, 4);
            Check((int)Prop(result, "Frames") == 0 && (long)Prop(result, "SamplePts") == 8197 &&
                (long)Prop(result, "Epoch") == 3 && (bool)Prop(result, "EndOfStream"), "EOF not idempotent");
        }
        pull.Seek(8197); Check(pull.Position == 8197 && pull.Epoch == 4, "seek exact EOS");
        pull.Seek(0); Check(pull.Position == 0 && pull.Epoch == 5, "seek frame zero");
    }
    static void PullContextAndBounds() {
        foreach (string malformed in new[] { "{", "{\"schema_version\":\"wrong-type\"}" }) {
            try {
                using var invalid = new PullHandle(System.Text.Encoding.UTF8.GetBytes(malformed));
                throw new InvalidOperationException("malformed scene accepted");
            } catch (Exception ex) when (ex.GetType().FullName == "AtmosProbe.InvalidInput" && ex.Message == "scene_json") { }
            using var afterFailedOpen = new PullHandle();
            afterFailedOpen.Read(new float[12], 1);
        }
        using (var pull = new PullHandle()) {
            Reject(() => { using var second = new PullHandle(layout: "stereo-speakers"); }, "active_render_context");
            Check(pull.Channels == 12, "competing layout changed context");
            Reject(() => pull.Read(new float[12], 0), "pull_read_size");
            Reject(() => pull.Read(new float[12], 2), "pull_read_size");
            Reject(() => pull.Read(new float[5000 * 12], 4097), "pull_read_size");
            Reject(() => pull.Seek(-1), "pull_seek_range");
            Reject(() => pull.Seek(8198), "pull_seek_range");
            Check(pull.Position == 0 && pull.Epoch == 0, "invalid request changed timeline");
            pull.Read(new float[12], 1);
        }
        using (var recovered = new PullHandle(layout: "stereo-speakers")) {
            Check(recovered.Channels == 2, "context lease not released");
            recovered.Dispose(); recovered.Dispose();
            try { recovered.Read(new float[2], 1); }
            catch (ObjectDisposedException) { return; }
            throw new InvalidOperationException("disposed context read succeeded");
        }
    }
    static void PullBudgets() {
        using (var pull = new PullHandle(commands: 4)) {
            Reject(() => pull.Read(new float[12], 0), "pull_read_size");
            Reject(() => pull.Seek(-1), "pull_seek_range");
            pull.Read(new float[12], 1); pull.Read(new float[12], 1);
            Reject(() => pull.Read(new float[12], 1), "pull_command_limit");
            Check(pull.Position == 2 && pull.Epoch == 0, "command rejection changed state");
        }
        using (var pull = new PullHandle(blocks: 2)) {
            pull.Read(new float[256 * 12], 256);
            Reject(() => pull.Seek(257), "pull_work_limit");
            Check(pull.Position == 256 && pull.Epoch == 0, "failed seek destroyed context");
            pull.Read(new float[256 * 12], 256);
            Reject(() => pull.Read(new float[12], 1), "pull_work_limit");
            Check(pull.Position == 512, "failed read changed state");
            pull.Seek(0);
            Reject(() => pull.Read(new float[12], 1), "pull_work_limit");
            Reject(() => pull.Seek(8197), "pull_work_limit");
            Check(pull.Position == 0 && pull.Epoch == 1, "seek reset cumulative work budget");
        }
        using (var pull = new PullHandle(blocks: 70)) {
            pull.Seek(8197); pull.Seek(8197); // 33 replay blocks each, even when PTS is unchanged.
            Reject(() => pull.Seek(8197), "pull_work_limit");
            Reject(() => pull.Flush(), "pull_work_limit");
            Check(pull.Position == 8197 && pull.Epoch == 2, "long-seek failure changed usable state");
            pull.Seek(0);
            pull.Read(new float[1024 * 12], 1024); // The four remaining blocks can still be used.
            Reject(() => pull.Read(new float[12], 1), "pull_work_limit");
        }
    }
    static void PullNonfinite() {
        using (var pull = new PullHandle()) {
            object engine = PullType.GetField("engine", Instance)!.GetValue(pull.Value)!;
            object listener = engine.GetType().GetField("listener", Instance)!.GetValue(engine)!;
            listener.GetType().GetProperty("Volume")!.SetValue(listener, float.NaN);
            Reject(() => pull.Read(new float[12], 1), "nonfinite_render");
            Reject(() => pull.Read(new float[12], 1), "faulted_render_context");
        }
        using var recovered = new PullHandle();
        recovered.Read(new float[12], 1);
    }
}
