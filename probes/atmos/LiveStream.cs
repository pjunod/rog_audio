using System.Buffers.Binary;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace AtmosProbe;

/// <summary>Private producer protocol, never an audio-device callback.</summary>
static class LiveStream {
    // Release six fixed DSP blocks without changing the offline caller limit.
    // Even 90 seconds plus seek/EOF fits the existing 4096-command budget.
    const int CallerFrames = 1536;
    internal static void Run(byte[] bytes, bool synthetic, string layout,
        string startValue, string volumeValue, Dictionary<string, object?> report) {
        if (!long.TryParse(startValue, NumberStyles.None, CultureInfo.InvariantCulture, out long start) ||
            !float.TryParse(volumeValue, NumberStyles.Float, CultureInfo.InvariantCulture, out float volume) ||
            !float.IsFinite(volume) || volume is < 0 or > 1)
            throw new InvalidInput("stream_options");
        using var pull = OfflinePullRenderer.Open(bytes, synthetic, layout);
        if (start < 0 || start > pull.Length) throw new InvalidInput("pull_seek_range");
        if (start != 0) pull.Seek(start);
        bool objects = pull.HasObjects;
        report["evidence_class"] = synthetic ? "synthetic-test" : "private-live-producer";
        report["container"] = synthetic ? "synthetic-json-v1" : "raw-eac3";
        report["codec"] = synthetic ? "generated-sine-objects" : "E-AC-3";
        report["decoder"] = synthetic ? "none" : "Cavern.Format.EnhancedAC3Decoder";
        report["atmos_signalling"] = objects ? "Cavern-parsed-JOC" : null;
        report["object_metadata_consumed"] = synthetic || objects;
        report["input_samples"] = pull.Length;
        report["renderer"] = pull.RendererName;
        using Stream output = Console.OpenStandardOutput();
        byte[] header = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new {
            protocol = "rog-atmos-pcm-v1", format = "f32le", sample_rate = 48000,
            channels = pull.Channels, input_samples = pull.Length, start_sample = start
        }) + "\n");
        output.Write(header); output.Flush();
        float[] buffer = new float[CallerFrames * pull.Channels];
        byte[] pcm = new byte[buffer.Length * sizeof(float)];
        long written = 0;
        using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        while (true) {
            PullRead read = pull.Read(buffer, CallerFrames);
            if (read.SamplePts != start + written || read.Epoch != (start == 0 ? 0 : 1))
                throw new InvalidInput("stream_discontinuity");
            if (read.Frames == 0) {
                if (!read.EndOfStream || written != pull.Length - start)
                    throw new InvalidInput("stream_length");
                break;
            }
            int count = read.Frames * pull.Channels;
            for (int i = 0; i < count; i++) {
                float value = buffer[i] * volume;
                if (!float.IsFinite(value) || Math.Abs(value) > 1)
                    throw new InvalidInput("stream_pcm");
                BinaryPrimitives.WriteInt32LittleEndian(pcm.AsSpan(i * 4, 4), BitConverter.SingleToInt32Bits(value));
            }
            int length = count * sizeof(float);
            // Fixed caller buffer plus bounded kernel pipe: a blocked consumer
            // blocks further decoding. No complete rendered-file staging.
            output.Write(pcm, 0, length); output.Flush();
            hash.AppendData(pcm, 0, length);
            written += read.Frames;
        }
        report["stream"] = new { start_sample = start, written_frames = written,
            sample_rate = 48000, channels = pull.Channels, layout, format = "f32le",
            volume_attenuation = volume, caller_frames = CallerFrames,
            pcm_sha256 = Convert.ToHexString(hash.GetHashAndReset()).ToLowerInvariant() };
        report["dsp_processing"] = pull.Profile;
        if (pull.Decoder is { } decoder) {
            report["decoded_frames"] = decoder.Frames;
            report["object_frames"] = decoder.ObjectFrames;
            report["oamd_fresh_object_frames"] = decoder.FreshOamdFrames;
            report["oamd_reused_object_frames"] = decoder.ReusedOamdFrames;
            report["object_configuration"] = decoder.ObjectConfiguration;
        }
        report["status"] = synthetic ? "synthetic-stream" : objects ? "joc-stream-unqualified" : "bed-fallback-stream";
    }
}
