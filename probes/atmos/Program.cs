using System.Diagnostics;
using System.Numerics;
using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
using Cavern;
using Cavern.Channels;
using Cavern.Format.Decoders;
using Cavern.Format.Renderers;
using Cavern.Format.Utilities;
using CavernUnsupported = Cavern.Format.Exceptions.UnsupportedFeatureException;

namespace AtmosProbe;

sealed class Unsupported(string message) : Exception(message);
sealed class InvalidInput(string message) : Exception(message);

static class Program {
    internal const string Pin = "7d85d1880666ca5ea323848cff47ce7f50b29f7d";
    internal const int Rate = 48000, Block = 256, MaxEncodedSeconds = 90;
    static readonly JsonSerializerOptions Json = new() { WriteIndented = true };
    static readonly string[] Stereo = ["FL", "FR"];
    // WAVEFORMATEXTENSIBLE bit order, matching the explicit Cavern matrix below.
    static readonly string[] Surround = ["FL", "FR", "FC", "LFE", "BL", "BR", "SL", "SR", "TFL", "TFR", "TBL", "TBR"];
    static Dictionary<string, object?> report = new() {
        ["schema_version"] = 1, ["tool_version"] = "0.2.0", ["cavern_source"] = Pin,
        ["modified_upstream_source"] = true, ["cavern_patches"] = new[]{"0001-block-buffer-exact-read", "0002-joc-timeslot-frame-boundary", "0003-emdf-oamd-presence"},
        ["status"] = "pending", ["evidence_class"] = "private-offline",
        ["container"] = null, ["codec"] = null, ["atmos_signalling"] = null,
        ["decoder"] = null, ["object_metadata_consumed"] = null,
        ["renderer"] = null, ["output"] = null, ["warnings"] = new List<string>(),
        ["delay"] = new { block_samples = Block, decoder_delay_samples = (int?)null,
            renderer_delay_samples = (int?)null, compensation_samples = 0,
            note = "No delay compensation or tail flush; physical latency unmeasured." }
    };
    static List<string> Warnings => (List<string>)report["warnings"]!;

    static int Main(string[] args) {
        string? reportPath = null;
        try {
            var opts = Parse(args);
            reportPath = opts["--report"];
            string path = opts["--input"];
            var info = new FileInfo(path);
            if (!info.Exists || info.Length is <= 0 or > 67108864) throw new InvalidInput("input_size_limit");
            byte[] bytes = File.ReadAllBytes(path);
            report["input_sha256"] = Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
            string layout = opts.GetValueOrDefault("--layout", "stereo-speakers");
            if (layout is not ("stereo-speakers" or "7.1.4")) throw new Unsupported("unsupported_layout");
            bool render = args[0] == "render";
            if (path.EndsWith(".json", StringComparison.OrdinalIgnoreCase)) Synthetic(bytes, layout, render ? opts["--output"] : null);
            else Encoded(bytes, layout, render ? opts["--output"] : null);
            Save(reportPath);
            return 0;
        } catch (Exception ex) {
            report["status"] = ex is Unsupported or CavernUnsupported ? "unsupported" : ex is InvalidInput or JsonException ? "invalid-input" : "decoder-failure";
            // Do not copy upstream exception messages: they may contain private paths/data.
            report["error"] = ex is Unsupported or InvalidInput ? ex.Message : ex.GetType().Name;
            if (ex is CavernUnsupported) {
                foreach (string feature in new[]{"stereo", "AHT", "ecplinu"}) {
                    if (ex.Message == $"A required feature in the codec is unsupported: {feature}.") report["error"] = "upstream_feature_" + feature;
                }
            }
            if (reportPath != null) Save(reportPath);
            return 2;
        }
    }

    static Dictionary<string,string> Parse(string[] args) {
        if (args.Length == 0 || args[0] is not ("inspect" or "render")) throw new InvalidInput("command");
        var result = new Dictionary<string,string>();
        for (int i = 1; i < args.Length; i++) {
            string key = args[i];
            if (key is not ("--input" or "--report" or "--output" or "--layout") || ++i == args.Length || !result.TryAdd(key,args[i])) throw new InvalidInput("option");
        }
        if (!result.ContainsKey("--input") || !result.ContainsKey("--report") || (args[0] == "render" && !result.ContainsKey("--output"))) throw new InvalidInput("required_option");
        if (args[0] == "inspect" && result.ContainsKey("--output")) throw new InvalidInput("inspect_option");
        return result;
    }

    static void Save(string path) => File.WriteAllText(path, JsonSerializer.Serialize(report, Json) + "\n");

    static Listener ListenerFor(string layout, int rate) {
        // The false constructor never reads the user's persisted Cavern settings.
        var listener = new Listener(false) { SampleRate = rate, UpdateRate = Block,
            Normalizer = 0, Volume = 1, LFESeparation = true, DirectLFE = true, MaximumSources = 128 };
        Listener.HeadphoneVirtualizer = false;
        Listener.EnvironmentSize = new Vector3(1,1,1);
        Listener.EnvironmentType = Environments.Home;
        ReferenceChannel[] matrix = layout == "stereo-speakers" ? [ReferenceChannel.FrontLeft, ReferenceChannel.FrontRight] :
            [ReferenceChannel.FrontLeft, ReferenceChannel.FrontRight, ReferenceChannel.FrontCenter, ReferenceChannel.ScreenLFE,
             ReferenceChannel.RearLeft, ReferenceChannel.RearRight, ReferenceChannel.SideLeft, ReferenceChannel.SideRight,
             ReferenceChannel.TopFrontLeft, ReferenceChannel.TopFrontRight, ReferenceChannel.TopRearLeft, ReferenceChannel.TopRearRight];
        Listener.ReplaceChannels(ChannelPrototype.ToLayout(matrix));
        return listener;
    }

    sealed record Point(int sample, float[] position);
    sealed record Obj(float amplitude, float frequency_hz, Point[] keyframes);
    sealed record Scene(int schema_version, int sample_rate, int samples, Obj[] objects);

    static void Synthetic(byte[] bytes, string layout, string? output) {
        Scene scene = JsonSerializer.Deserialize<Scene>(bytes) ?? throw new InvalidInput("scene");
        if (scene.schema_version != 1 || scene.sample_rate != Rate || scene.samples is < Block or > 480000 || scene.objects is null || scene.objects.Length is < 1 or > 8) throw new InvalidInput("scene_limits");
        float total = 0;
        foreach (Obj obj in scene.objects) {
            if (obj is null || !float.IsFinite(obj.amplitude) || obj.amplitude is < 0 or > .25f || !float.IsFinite(obj.frequency_hz) || obj.frequency_hz is < 20 or > 20000 || obj.keyframes is null || obj.keyframes.Length is < 1 or > 128) throw new InvalidInput("object_limits");
            total += obj.amplitude;
            int previous = -1;
            foreach (Point point in obj.keyframes) {
                if (point is null || point.sample <= previous || point.sample >= scene.samples || point.position is null || point.position.Length != 3 || point.position.Any(x => !float.IsFinite(x) || Math.Abs(x) > 1)) throw new InvalidInput("keyframes");
                previous = point.sample;
            }
            if (obj.keyframes[0].sample != 0) throw new InvalidInput("first_keyframe");
        }
        if (total > .5f) throw new InvalidInput("aggregate_gain");
        report["evidence_class"] = "synthetic-test";
        report["container"] = "synthetic-json-v1"; report["codec"] = "generated-sine-objects";
        report["atmos_signalling"] = null; report["decoder"] = "none";
        report["object_metadata_consumed"] = output != null;
        Warnings.Add("Synthetic object positions are not Dolby metadata or codec qualification.");
        report["input_samples"] = scene.samples;
        if (output == null) { report["status"] = "synthetic-inspected"; return; }
        Listener listener = ListenerFor(layout, Rate);
        var sources = new List<Source>();
        foreach (Obj obj in scene.objects) {
            float[] clip = new float[scene.samples];
            for (int i = 0; i < clip.Length; i++) clip[i] = obj.amplitude * MathF.Sin(2*MathF.PI*obj.frequency_hz*i/Rate);
            var source = new Source { Clip = new Clip(clip,1,Rate), VolumeRolloff = Rolloffs.Disabled, Position = Position(obj,0) };
            sources.Add(source); listener.AttachSource(source);
        }
        Render(listener, output, scene.samples, layout, sample => {
            for (int i = 0; i < sources.Count; i++) sources[i].Position = Position(scene.objects[i],sample);
        });
        report["status"] = "synthetic-rendered";
    }

    static Vector3 Position(Obj obj, int sample) {
        int i = 0;
        while (i+1 < obj.keyframes.Length && obj.keyframes[i+1].sample <= sample) i++;
        Point a = obj.keyframes[i];
        var start = new Vector3(a.position[0],a.position[1],a.position[2]);
        if (i+1 == obj.keyframes.Length) return start;
        Point b = obj.keyframes[i+1];
        return Vector3.Lerp(start,new Vector3(b.position[0],b.position[1],b.position[2]),(sample-a.sample)/(float)(b.sample-a.sample));
    }

    // Deliberately restricted elementary-stream scanner. No extension-based codec badges.
    static (int samples, int rate, int frameSamples, int frames) Scan(byte[] b) {
        int pos = 0, samples = 0, rate = 0, frameSamples = 0, frames = 0, channelMode = -1;
        while (pos < b.Length) {
            if (b.Length-pos < 6 || b[pos] != 0x0b || b[pos+1] != 0x77) throw new Unsupported("not_raw_eac3_or_bad_sync");
            int bsid = b[pos+5] >> 3;
            if (bsid is < 11 or > 16) throw new Unsupported("not_eac3");
            if ((b[pos+2] >> 6) != 0 || ((b[pos+2] >> 3)&7) != 0) throw new Unsupported("dependent_or_multiple_substreams");
            int size = ((((b[pos+2]&7)<<8)|b[pos+3])+1)*2;
            if (size < 6 || pos+size > b.Length) throw new InvalidInput("truncated_frame");
            int fscod = b[pos+4] >> 6;
            if (fscod != 0) throw new Unsupported("only_48khz_eac3");
            int n = new[]{1,2,3,6}[(b[pos+4]>>4)&3]*256;
            int mode = b[pos+4]&15;
            if (frames > 0 && (frameSamples != n || mode != channelMode)) throw new Unsupported("changing_stream_configuration");
            frameSamples = n; rate = Rate; channelMode = mode;
            samples += n; frames++; pos += size;
            if (samples > MaxEncodedSeconds*Rate) throw new InvalidInput("duration_limit");
        }
        return (samples,rate,frameSamples,frames);
    }

    static void Encoded(byte[] bytes, string layout, string? output) {
        var scan = Scan(bytes);
        report["container"] = "raw-eac3"; report["codec"] = "E-AC-3";
        report["decoder"] = "Cavern.Format.EnhancedAC3Decoder";
        report["input_samples"] = scan.samples;
        using var input = new MemoryStream(bytes,false);
        var decoder = new ObservedDecoder(BlockBuffer<byte>.Create(input));
        decoder.Seed(scan.frames);
        if (decoder.SampleRate != Rate || decoder.FrameSize != scan.frameSamples || decoder.ChannelCount is < 1 or > 8) throw new Unsupported("decoder_configuration");
        if (output == null) {
            float[] buffer = new float[scan.frameSamples*decoder.ChannelCount];
            for (int i = 0; i < scan.frames; i++) decoder.DecodeBlock(buffer,0,buffer.Length);
            report["atmos_signalling"] = decoder.ObjectFrames > 0 ? "Cavern-parsed-JOC" : null;
            report["object_metadata_consumed"] = false;
            report["decoded_frames"] = decoder.Frames;
            report["object_frames"] = decoder.ObjectFrames;
            report["oamd_fresh_object_frames"] = decoder.FreshOamdFrames;
            report["oamd_reused_object_frames"] = decoder.ReusedOamdFrames;
            report["object_configuration"] = decoder.ObjectConfiguration;
            report["status"] = decoder.ObjectFrames > 0 ? "joc-inspected-unqualified" : "bed-only";
            Warnings.Add("Signalling describes parsed frames; absence is not an independent bitstream metadata audit.");
            return;
        }
        bool objects = decoder.HasObjects;
        decoder.RequireObjects = objects;
        decoder.RejectObjects = !objects;
        Listener listener = ListenerFor(layout, Rate);
        using Renderer renderer = objects ? new EnhancedAC3Renderer(decoder) : new BedRenderer(decoder);
        listener.AttachSources(renderer.Objects);
        Render(listener,output,scan.samples,layout,_=>{});
        if (objects) decoder.VerifyNoSparse();
        if (objects && decoder.ObjectFrames != scan.frames) throw new Unsupported("object_metadata_not_continuous");
        report["atmos_signalling"] = objects ? "Cavern-parsed-JOC" : null;
        report["object_metadata_consumed"] = objects;
        report["decoded_frames"] = decoder.Frames; report["object_frames"] = decoder.ObjectFrames;
        report["oamd_fresh_object_frames"] = decoder.FreshOamdFrames;
        report["oamd_reused_object_frames"] = decoder.ReusedOamdFrames;
        report["object_configuration"] = decoder.ObjectConfiguration;
        report["status"] = objects ? "joc-rendered-unqualified" : "bed-fallback-rendered";
        Warnings.Add(objects ? "JOC decoded/rendered; independent reference fidelity, delay and gain comparison remain unqualified." : "Explicit conventional-channel fallback; not Atmos rendering.");
    }

    static void Render(Listener listener, string output, int samples, string layout, Action<int> update) {
        string[] channels = layout == "stereo-speakers" ? Stereo : Surround;
        using var writer = new Wave(output,channels.Length,samples,listener.SampleRate,layout == "stereo-speakers" ? 3u : 0x2d63fu);
        double[] energy = new double[channels.Length]; float peak = 0;
        var watch = Stopwatch.StartNew();
        long alloc = GC.GetTotalAllocatedBytes(true);
        for (int pos = 0; pos < samples; pos += Block) {
            update(pos);
            float[] block = listener.Render();
            int count = Math.Min(Block,samples-pos)*channels.Length;
            if (block.Length < count) throw new InvalidInput("render_length");
            for (int i = 0; i < count; i++) {
                float value = block[i];
                if (!float.IsFinite(value)) throw new InvalidInput("nonfinite_render");
                peak = Math.Max(peak,Math.Abs(value)); energy[i%channels.Length] += value*value;
                if (Math.Abs(value)>1) throw new Unsupported("render_clipping");
            }
            writer.Write(block,count);
        }
        watch.Stop();
        report["renderer"] = "Cavern.Listener/" + Listener.Renderer.GetType().Name;
        report["output"] = new { layout, sample_rate = listener.SampleRate, channels, samples_per_channel = samples,
            peak, rms = energy.Select(x=>Math.Sqrt(x/samples)).ToArray(), format = "WAVE-extensible-float32",
            gain = "unity listener; normalizer disabled; E-AC-3 object renderer upstream gain 0.707" };
        report["processing"] = new { elapsed_ms = watch.Elapsed.TotalMilliseconds,
            allocated_bytes = GC.GetTotalAllocatedBytes(true)-alloc, block_samples = Block,
            evidence = "single offline run, includes WAV I/O and startup; not realtime qualification" };
    }
}

// Source-bound observation of the exact metadata branch used by the pinned renderer.
// Fail closed if those internal names change; do not infer Atmos from a file label.
sealed class ObservedDecoder(BlockBuffer<byte> reader) : EnhancedAC3Decoder(reader) {
    static readonly PropertyInfo ExtensionsProperty = typeof(EnhancedAC3Decoder).GetProperty("Extensions",BindingFlags.Instance|BindingFlags.NonPublic)!;
    public int Frames { get; private set; }
    public int ObjectFrames { get; private set; }
    public int FreshOamdFrames { get; private set; }
    public int ReusedOamdFrames { get; private set; }
    public bool RequireObjects, RejectObjects;
    bool seeded;
    int expectedFrames;
    readonly ObjectFrameGuard guard = new();
    object Extensions => ExtensionsProperty.GetValue(this)!;
    static object Value(object obj,string name) => obj.GetType().GetProperty(name)!.GetValue(obj)!;
    public IReadOnlyDictionary<string,int>? ObjectConfiguration => guard.Describe();
    public bool HasObjects => (bool)Value(Extensions,"HasObjects");
    public void Seed(int frames) { expectedFrames = frames; seeded = true; Observe(); }
    void Observe() {
        Frames++;
        if (HasObjects) {
            ObjectFrames++;
            object oamd = Value(Extensions,"OAMD"), joc = Value(Extensions,"JOC");
            if ((bool)Value(Extensions,"HasOAMD")) FreshOamdFrames++; else ReusedOamdFrames++;
            guard.Validate((bool)Value(Extensions,"HasOAMD"), (int)Value(oamd,"ObjectCount"),
                (int)Value(joc,"ObjectCount"), (int)Value(joc,"ChannelCount"), (byte)Value(oamd,"Beds"),
                (int)oamd.GetType().GetMethod("GetLFEPosition")!.Invoke(oamd,null)!);
            VerifyNoSparse();
            if (RejectObjects) throw new Unsupported("joc_appeared_in_bed_fallback");
        } else if (RequireObjects) throw new Unsupported("object_metadata_missing_frame");
    }
    public void VerifyNoSparse() => ObjectFrameGuard.CheckSparse((bool)Value(Value(Extensions,"JOC"),"HadSparse"));
    protected override float[] DecodeFrame() {
        float[] result = base.DecodeFrame();
        // Finished is set while reading ahead to the next header. The last valid
        // frame still has samples; the next call returns a synthetic zero frame.
        // The source patch prevents exact-read prefetch. Still exclude any EOF
        // zero fill beyond the syncframes counted by the validated scanner.
        if (seeded && Frames < expectedFrames) Observe();
        return result;
    }
}

// The upstream EnhancedAC3Renderer's bed Update/Dispose dereference OAMD/applier.
// Use a small explicit PCM adapter for the separately labelled bed-only path.
sealed class BedRenderer : Renderer {
    readonly EnhancedAC3Decoder decoder;
    readonly ReferenceChannel[] matrix;
    public BedRenderer(EnhancedAC3Decoder decoder) : base(decoder) {
        this.decoder = decoder; matrix = decoder.GetChannels().Order().ToArray(); SetupChannels();
    }
    public override ReferenceChannel[] GetChannels() => matrix;
    public override void Update(int samples) {
        float[] data = new float[samples*decoder.ChannelCount];
        decoder.DecodeBlock(data,0,data.Length);
        for (int c = 0; c < objectSamples.Length; c++) {
            objectSamples[c] = new float[samples];
            for (int i = 0; i < samples; i++) objectSamples[c][i] = data[i*decoder.ChannelCount+c];
        }
    }
}

sealed class Wave : IDisposable {
    readonly BinaryWriter writer;
    public Wave(string path,int channels,int samples,int rate,uint mask) {
        writer = new BinaryWriter(new FileStream(path,FileMode.CreateNew,FileAccess.Write));
        int bytes = checked(samples*channels*4);
        writer.Write("RIFF"u8); writer.Write(bytes+60); writer.Write("WAVEfmt "u8); writer.Write(40);
        writer.Write((ushort)0xfffe); writer.Write((ushort)channels); writer.Write(rate); writer.Write(rate*channels*4);
        writer.Write((ushort)(channels*4)); writer.Write((ushort)32); writer.Write((ushort)22); writer.Write((ushort)32); writer.Write(mask);
        writer.Write(new Guid("00000003-0000-0010-8000-00aa00389b71").ToByteArray());
        writer.Write("data"u8); writer.Write(bytes);
    }
    public void Write(float[] data,int count) { for (int i = 0; i < count; i++) writer.Write(data[i]); }
    public void Dispose() => writer.Dispose();
}
