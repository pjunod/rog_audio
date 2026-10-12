namespace AtmosProbe;

// Keep renderer arrays/configuration bound to the initial frame. The patched
// decoder exposes actual OAMD presence separately from its retained state.
internal sealed class ObjectFrameGuard {
    readonly record struct Shape(int Objects, int CodedObjects, int Channels, int Beds, int Lfe);
    Shape? initial;
    public void Validate(bool currentOamd, int objects, int codedObjects, int channels, int beds, int lfe) {
        if (!initial.HasValue && !currentOamd) throw new Unsupported("initial_oamd_missing");
        if (objects is < 1 or > 64 || codedObjects is < 1 or > 64 || channels is not (5 or 7)
            || beds < 0 || beds > objects || lfe < -1 || lfe >= objects
            || objects != codedObjects + (lfe == -1 ? 0 : 1)) throw new Unsupported("unsupported_object_metadata");
        Shape shape = new(objects,codedObjects,channels,beds,lfe);
        if (initial.HasValue && initial.Value != shape) throw new Unsupported("changing_object_configuration");
        initial = shape;
    }
    // Called while observing frames and after Render, because the pinned
    // matrix expander sets HadSparse later than DecodeFrame observation.
    public static void CheckSparse(bool hadSparse) {
        if (hadSparse) throw new Unsupported("unsupported_sparse_joc");
    }
}
