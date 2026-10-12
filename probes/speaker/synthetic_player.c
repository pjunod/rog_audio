/* SPDX-License-Identifier: MIT
 * Finite-amplitude generated audio in an isolated server, never a host device.
 */
#define _GNU_SOURCE
#include <pipewire/pipewire.h>
#include <spa/param/audio/format-utils.h>
#include <math.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
struct player {struct pw_main_loop* loop;struct pw_stream* stream;uint64_t frame;FILE* capture;};
static void process(void* data) {
 struct player* p=data;struct pw_buffer* buffer=pw_stream_dequeue_buffer(p->stream);
 if(!buffer)return;
 struct spa_data* d=&buffer->buffer->datas[0];float* samples=d->data;
 if(p->capture) {
  if(d->data && d->chunk->offset<=d->maxsize && d->chunk->size<=d->maxsize-d->chunk->offset)
   fwrite((char*)d->data+d->chunk->offset,1,d->chunk->size,p->capture);
  pw_stream_queue_buffer(p->stream,buffer);return;
 }
 uint32_t frames=d->maxsize/(2*sizeof(float));if(buffer->requested && buffer->requested<frames)frames=buffer->requested;
 if(samples)for(uint32_t n=0;n<frames;n++) {float value=.1f*sinf(2.f*3.14159265f*1000.f*(p->frame++%48000)/48000.f);samples[2*n]=value;samples[2*n+1]=value;}
 d->chunk->offset=0;d->chunk->stride=2*sizeof(float);d->chunk->size=frames*2*sizeof(float);
 buffer->size=frames;pw_stream_queue_buffer(p->stream,buffer);
}
static void quit(void* data,int signal) {(void)signal;pw_main_loop_quit(((struct player*)data)->loop);}
int main(int argc,char** argv) {
 if(argc<2 || argc>4)return 2;
 int capture=argc==4 && strcmp(argv[1],"--capture")==0;
 if(argc==4 && !capture)return 2;pw_init(&argc,&argv);struct player p={0};p.loop=pw_main_loop_new(NULL);
 struct pw_properties* props=pw_properties_new(PW_KEY_MEDIA_TYPE,"Audio",PW_KEY_MEDIA_CATEGORY,"Playback",
  PW_KEY_MEDIA_ROLE,"Music",PW_KEY_NODE_NAME,capture?"rog-synthetic-capture":argv[1],PW_KEY_APP_ID,"rog_audio.synthetic",NULL);
 if(argc==3 || capture)pw_properties_set(props,PW_KEY_TARGET_OBJECT,argv[2]);
 if(capture) {p.capture=fopen(argv[3],"wb");if(!p.capture)return 4;pw_properties_set(props,"stream.capture.sink","true");}
 const struct pw_stream_events events={.version=PW_VERSION_STREAM_EVENTS,.process=process};
 p.stream=pw_stream_new_simple(pw_main_loop_get_loop(p.loop),argv[1],props,&events,&p);
 uint8_t bytes[1024];struct spa_pod_builder b=SPA_POD_BUILDER_INIT(bytes,sizeof(bytes));
 const struct spa_pod* params[1];struct spa_audio_info_raw info={.format=SPA_AUDIO_FORMAT_F32,.rate=48000,.channels=2,.position={SPA_AUDIO_CHANNEL_FL,SPA_AUDIO_CHANNEL_FR}};
 params[0]=spa_format_audio_raw_build(&b,SPA_PARAM_EnumFormat,&info);
 int r=pw_stream_connect(p.stream,capture?PW_DIRECTION_INPUT:PW_DIRECTION_OUTPUT,PW_ID_ANY,PW_STREAM_FLAG_AUTOCONNECT|PW_STREAM_FLAG_MAP_BUFFERS|PW_STREAM_FLAG_RT_PROCESS,params,1);
 if(r<0)return 3;pw_loop_add_signal(pw_main_loop_get_loop(p.loop),SIGINT,quit,&p);pw_loop_add_signal(pw_main_loop_get_loop(p.loop),SIGTERM,quit,&p);
 pw_main_loop_run(p.loop);pw_stream_destroy(p.stream);pw_main_loop_destroy(p.loop);if(p.capture)fclose(p.capture);pw_deinit();return 0;
}
