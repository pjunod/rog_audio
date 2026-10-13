/* Read HAL output properties only. Never create/start an IOProc or set a property. */
#include <CoreAudio/CoreAudio.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define MAX_OBJECTS 128U

typedef struct {
    OSStatus status;
    UInt32 count;
    AudioObjectID ids[MAX_OBJECTS];
} ObjectList;

static AudioObjectPropertyAddress address(AudioObjectPropertySelector selector,
                                          AudioObjectPropertyScope scope) {
    return (AudioObjectPropertyAddress){selector, scope, kAudioObjectPropertyElementMain};
}

static OSStatus scalar(AudioObjectID object, AudioObjectPropertySelector selector,
                       AudioObjectPropertyScope scope, void *value, UInt32 size) {
    AudioObjectPropertyAddress property = address(selector, scope);
    if (!AudioObjectHasProperty(object, &property)) return kAudioHardwareUnknownPropertyError;
    UInt32 actual = size;
    OSStatus status = AudioObjectGetPropertyData(object, &property, 0, NULL, &actual, value);
    if (status == noErr && actual != size) return kAudioHardwareBadPropertySizeError;
    return status;
}

static ObjectList objects(AudioObjectID object, AudioObjectPropertySelector selector,
                           AudioObjectPropertyScope scope) {
    ObjectList list = {0};
    AudioObjectPropertyAddress property = address(selector, scope);
    if (!AudioObjectHasProperty(object, &property)) {
        list.status = kAudioHardwareUnknownPropertyError;
        return list;
    }
    UInt32 size = 0;
    list.status = AudioObjectGetPropertyDataSize(object, &property, 0, NULL, &size);
    if (list.status != noErr) return list;
    if (size > sizeof(list.ids) || size % sizeof(AudioObjectID) != 0) {
        list.status = kAudioHardwareBadPropertySizeError;
        return list;
    }
    if (size == 0) return list;
    UInt32 capacity = size;
    list.status = AudioObjectGetPropertyData(object, &property, 0, NULL, &size, list.ids);
    if (list.status != noErr) return list;
    if (size > capacity || size % sizeof(AudioObjectID) != 0) {
        list.status = kAudioHardwareBadPropertySizeError;
        return list;
    }
    list.count = size / (UInt32)sizeof(AudioObjectID);
    return list;
}

static void prefix(OSStatus status, bool valid) {
    const char *state = status == noErr ? (valid ? "ok" : "invalid-data") :
                       status == kAudioHardwareUnknownPropertyError ? "unavailable" : "error";
    printf("{\"status\":\"%s\",\"os_status\":%d,\"value\":", state, (int)status);
}

static void uint_property(AudioObjectID object, AudioObjectPropertySelector selector,
                           AudioObjectPropertyScope scope) {
    UInt32 value = 0;
    OSStatus status = scalar(object, selector, scope, &value, sizeof(value));
    prefix(status, true);
    if (status == noErr) printf("%u", (unsigned)value); else printf("null");
    printf("}");
}

static void rate_property(AudioObjectID object, AudioObjectPropertySelector selector) {
    Float64 value = 0;
    OSStatus status = scalar(object, selector, kAudioObjectPropertyScopeGlobal, &value, sizeof(value));
    bool valid = isfinite(value) && value > 0;
    prefix(status, valid);
    if (status == noErr && valid) printf("%.17g", value); else printf("null");
    printf("}");
}

static void format_property(AudioObjectID stream, AudioObjectPropertySelector selector) {
    AudioStreamBasicDescription value = {0};
    OSStatus status = scalar(stream, selector, kAudioObjectPropertyScopeGlobal, &value, sizeof(value));
    bool valid = isfinite(value.mSampleRate) && value.mSampleRate > 0;
    prefix(status, valid);
    if (status != noErr || !valid) printf("null");
    else printf("{\"rate_hz\":%.17g,\"channels\":%u,\"format_id\":%u,\"format_flags\":%u,"
                "\"bytes_per_packet\":%u,\"frames_per_packet\":%u,\"bytes_per_frame\":%u,\"bits_per_channel\":%u}",
                value.mSampleRate, (unsigned)value.mChannelsPerFrame, (unsigned)value.mFormatID,
                (unsigned)value.mFormatFlags, (unsigned)value.mBytesPerPacket, (unsigned)value.mFramesPerPacket,
                (unsigned)value.mBytesPerFrame, (unsigned)value.mBitsPerChannel);
    printf("}");
}

static void stream(AudioObjectID id) {
    printf("{\"object_id\":%u,\"latency_frames\":", (unsigned)id);
    uint_property(id, kAudioStreamPropertyLatency, kAudioObjectPropertyScopeGlobal);
    printf(",\"terminal_type\":");
    uint_property(id, kAudioStreamPropertyTerminalType, kAudioObjectPropertyScopeGlobal);
    printf(",\"is_active\":");
    uint_property(id, kAudioStreamPropertyIsActive, kAudioObjectPropertyScopeGlobal);
    printf(",\"virtual_format\":");
    format_property(id, kAudioStreamPropertyVirtualFormat);
    printf(",\"physical_format\":");
    format_property(id, kAudioStreamPropertyPhysicalFormat);
    printf("}");
}

static void device(AudioObjectID id, ObjectList streams) {
    printf("{\"object_id\":%u,\"transport_type\":", (unsigned)id);
    uint_property(id, kAudioDevicePropertyTransportType, kAudioObjectPropertyScopeGlobal);
    printf(",\"nominal_rate_hz\":"); rate_property(id, kAudioDevicePropertyNominalSampleRate);
    printf(",\"actual_rate_hz\":"); rate_property(id, kAudioDevicePropertyActualSampleRate);
    printf(",\"buffer_frames\":");
    uint_property(id, kAudioDevicePropertyBufferFrameSize, kAudioObjectPropertyScopeGlobal);
    printf(",\"buffer_range_frames\":");
    AudioValueRange range = {0};
    OSStatus status = scalar(id, kAudioDevicePropertyBufferFrameSizeRange,
                            kAudioObjectPropertyScopeGlobal, &range, sizeof(range));
    bool valid = isfinite(range.mMinimum) && isfinite(range.mMaximum) &&
                 range.mMinimum > 0 && range.mMaximum >= range.mMinimum;
    prefix(status, valid);
    if (status == noErr && valid) printf("[%.17g,%.17g]", range.mMinimum, range.mMaximum); else printf("null");
    printf("},\"output_device_latency_frames\":");
    uint_property(id, kAudioDevicePropertyLatency, kAudioObjectPropertyScopeOutput);
    printf(",\"output_safety_offset_frames\":");
    uint_property(id, kAudioDevicePropertySafetyOffset, kAudioObjectPropertyScopeOutput);
    printf(",\"is_running\":");
    uint_property(id, kAudioDevicePropertyDeviceIsRunningSomewhere, kAudioObjectPropertyScopeGlobal);
    printf(",\"is_alive\":");
    uint_property(id, kAudioDevicePropertyDeviceIsAlive, kAudioObjectPropertyScopeGlobal);
    printf(",\"output_streams\":"); prefix(streams.status, true);
    if (streams.status != noErr) printf("null");
    else {
        printf("[");
        for (UInt32 i = 0; i < streams.count; ++i) {
            if (i != 0) printf(",");
            stream(streams.ids[i]);
        }
        printf("]");
    }
    printf("}}");
}

int main(int argc, char **argv) {
    (void)argv;
    if (argc != 1) { fputs("coreaudio probe failed: invalid arguments\n", stderr); return 2; }
    printf("{\"schema_version\":1,\"kind\":\"coreaudio-output-inventory\","
           "\"evidence_kind\":\"live-read-only\",\"default_output_before\":");
    uint_property(kAudioObjectSystemObject, kAudioHardwarePropertyDefaultOutputDevice, kAudioObjectPropertyScopeGlobal);
    printf(",\"system_output_before\":");
    uint_property(kAudioObjectSystemObject, kAudioHardwarePropertyDefaultSystemOutputDevice, kAudioObjectPropertyScopeGlobal);
    ObjectList devices = objects(kAudioObjectSystemObject, kAudioHardwarePropertyDevices, kAudioObjectPropertyScopeGlobal);
    printf(",\"devices\":"); prefix(devices.status, true);
    if (devices.status != noErr) printf("null");
    else {
        printf("[");
        bool emitted = false;
        for (UInt32 i = 0; i < devices.count; ++i) {
            ObjectList streams = objects(devices.ids[i], kAudioDevicePropertyStreams, kAudioObjectPropertyScopeOutput);
            if (streams.status == noErr && streams.count == 0) continue;
            if (emitted) printf(",");
            device(devices.ids[i], streams);
            emitted = true;
        }
        printf("]");
    }
    printf("},\"default_output_after\":");
    uint_property(kAudioObjectSystemObject, kAudioHardwarePropertyDefaultOutputDevice, kAudioObjectPropertyScopeGlobal);
    printf(",\"system_output_after\":");
    uint_property(kAudioObjectSystemObject, kAudioHardwarePropertyDefaultSystemOutputDevice, kAudioObjectPropertyScopeGlobal);
    printf("}\n");
    return ferror(stdout) ? 1 : devices.status == noErr ? 0 : 3;
}
