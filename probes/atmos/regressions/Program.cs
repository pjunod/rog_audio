using System.Reflection;
using Cavern.Format.Decoders;
using Cavern.Format.Utilities;

static class Regression {
    const BindingFlags Instance = BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic;
    static readonly Assembly Format = typeof(EnhancedAC3Decoder).Assembly;
    static Type JType => Format.GetType("Cavern.Format.Decoders.EnhancedAC3.JointObjectCoding",true)!;
    static Type GuardType => Assembly.LoadFrom(Path.Combine(AppContext.BaseDirectory,"..","AtmosProbe.dll")).GetType("AtmosProbe.ObjectFrameGuard",true)!;
    static object Get(object obj,string field) => obj.GetType().GetField(field,Instance)!.GetValue(obj)!;
    static void SetProperty(object obj,string property,object value) => obj.GetType().GetProperty(property,Instance)!.SetValue(obj,value);
    static object Call(object obj,string method,params object[] args) => obj.GetType().GetMethods(Instance).Single(m=>m.Name == method && m.GetParameters().Length == args.Length).Invoke(obj,args)!;
    static void Check(bool condition,string reason) { if (!condition) throw new InvalidOperationException(reason); }
    static void Unsupported(Action action,string reason) {
        try { action(); } catch (TargetInvocationException ex) when (ex.InnerException?.GetType().Name == "Unsupported") {
            Check(ex.InnerException.Message == reason,"wrong capability failure"); return;
        }
        throw new InvalidOperationException("missing capability failure: "+reason);
    }
    static object NewJoc() {
        object joc = Activator.CreateInstance(JType,true)!;
        SetProperty(joc,"ObjectCount",1); SetProperty(joc,"ChannelCount",5); SetProperty(joc,"Gain",1f);
        Call(joc,"UpdateCache"); // ObjectActive defaults to false: deterministic zero matrices.
        return joc;
    }
    static void BlockBufferBoundary() {
        const int frameSize = 1536, blockSize = 64;
        int metadataFrame = 0;
        var buffer = new BlockBuffer<float>(() => {
            metadataFrame++;
            return Enumerable.Range(0,frameSize).Select(i=>(float)((metadataFrame-1)*frameSize+i)).ToArray();
        });
        for (int start = 0; start < frameSize; start += blockSize) {
            float[] block = buffer.Read(blockSize);
            Check(block.Length == blockSize,"block length");
            Check(metadataFrame == 1,"next metadata fetched before current PCM consumed");
            Check(buffer.LastFetchStart == start,"current-frame timecode changed");
            for (int i = 0; i < blockSize; i++) Check(block[i] == start+i,"current PCM changed");
        }
        Check(buffer.LastFetchStart == frameSize-blockSize,"final current-frame timecode");
        float[] next = buffer.Read(blockSize);
        Check(metadataFrame == 2,"next-frame metadata not fetched on next Read");
        Check(buffer.LastFetchStart == 0,"next-frame timecode not reset");
        for (int i = 0; i < blockSize; i++) Check(next[i] == frameSize+i,"next-frame PCM mismatch");
    }
    static void JocTimeslots() {
        Type applierType = Format.GetType("Cavern.Format.Decoders.EnhancedAC3.JointObjectCodingApplier",true)!;
        foreach (int frameSize in new[]{256,512,768,1536}) {
            using var joc = (IDisposable)NewJoc();
            using var applier = (IDisposable)Activator.CreateInstance(applierType,Instance,null,new object[]{joc,frameSize},null)!;
            float[][] input = Enumerable.Range(0,7).Select(_=>new float[64]).ToArray();
            for (int frame = 0; frame < 3; frame++) {
                for (int slot = 0; slot < frameSize/64; slot++) {
                    float[][] output = (float[][])Call(applier,"Apply",input,joc);
                    Check((int)Get(applier,"timeslot") == (slot+1)%(frameSize/64),"wrong JOC timeslot wrap");
                    Check(output.Length == 1 && output[0].Length == 64 && output[0].All(x=>x == 0),"zero JOC output");
                }
            }
        }
    }
    static void LateSparse() {
        using var joc = (IDisposable)NewJoc();
        MethodInfo guard = GuardType.GetMethod("CheckSparse")!;
        bool flag() => (bool)JType.GetProperty("HadSparse")!.GetValue(joc)!;
        Check(!flag(),"sparse marked before matrix expansion");
        guard.Invoke(null,new object[]{flag()});
        ((bool[])Get(joc,"ObjectActive"))[0] = true;
        ((bool[])Get(joc,"sparseCoded"))[0] = true;
        ((byte[])Get(joc,"bands"))[0] = 1;
        ((int[])Get(joc,"dataPoints"))[0] = 1;
        Call(joc,"GetMixingMatrices",256);
        Check(flag(),"matrix expansion did not mark sparse workaround");
        Unsupported(()=>guard.Invoke(null,new object[]{flag()}),"unsupported_sparse_joc");
    }
    static void MetadataState() {
        Type extType = Format.GetType("Cavern.Format.Decoders.EnhancedAC3.ExtensibleMetadataDecoder",true)!;
        object extensions = Activator.CreateInstance(extType,true)!;
        object oamd = extType.GetProperty("OAMD")!.GetValue(extensions)!;
        SetProperty(oamd,"ObjectCount",1); SetProperty(extensions,"HasOAMD",true);
        Call(extensions,"Decode",Activator.CreateInstance(Format.GetType("Cavern.Format.Utilities.BitExtractor",true)!,Instance,null,new object[]{Array.Empty<byte>()},null)!);
        Check(!(bool)extType.GetProperty("HasOAMD")!.GetValue(extensions)!,"OAMD marker not reset");
        Check((int)oamd.GetType().GetProperty("ObjectCount")!.GetValue(oamd)! == 1,"persisted OAMD lost");
        object NewGuard() => Activator.CreateInstance(GuardType,true)!;
        void Validate(object g,bool fresh,int objects=1,int coded=1,int channels=5,int beds=0,int lfe=-1) => Call(g,"Validate",fresh,objects,coded,channels,beds,lfe);
        Unsupported(()=>Validate(NewGuard(),false),"initial_oamd_missing");
        object guard = NewGuard(); Validate(guard,true); Validate(guard,false); // Valid carry-forward.
        Unsupported(()=>Validate(guard,true,2,2),"changing_object_configuration");
        Unsupported(()=>Validate(guard,true,channels:7),"changing_object_configuration");
        Unsupported(()=>Validate(guard,true,beds:1),"changing_object_configuration");
        Unsupported(()=>Validate(guard,true,objects:2,lfe:0),"changing_object_configuration");
    }
    static int Main(string[] args) {
        switch (args.Single()) {
            case "block-buffer": BlockBufferBoundary(); break;
            case "joc-timeslots": JocTimeslots(); break;
            case "late-sparse": LateSparse(); break;
            case "metadata-state": MetadataState(); break;
            default: throw new ArgumentException("regression ID");
        }
        Console.WriteLine(args[0]+": pass"); return 0;
    }
}
