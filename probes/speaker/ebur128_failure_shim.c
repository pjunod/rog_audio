/* SPDX-License-Identifier: MIT
 * Isolated acceptance-only LD_PRELOAD shim: inject a real ingestion error.
 * Not built into, installed with or referenced by the production runtime.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <ebur128.h>
#include <fcntl.h>
#include <stdlib.h>
#include <unistd.h>

static int control_fd=-1;
static int count_fd=-1;
static int (*real_add_frames)(ebur128_state*, const float*, size_t);

__attribute__((constructor)) static void initialize(void) {
  const char* control=getenv("ROG_AUDIO_TEST_EBUR_CONTROL");
  const char* count=getenv("ROG_AUDIO_TEST_EBUR_FAILURE_COUNT");
  if(!control || !count)_exit(125);
  control_fd=open(control,O_RDONLY|O_CLOEXEC);
  count_fd=open(count,O_WRONLY|O_APPEND|O_CLOEXEC);
  real_add_frames=dlsym(RTLD_NEXT,"ebur128_add_frames_float");
  if(control_fd<0 || count_fd<0 || !real_add_frames)_exit(125);
}

int ebur128_add_frames_float(ebur128_state* state, const float* source, size_t frames) {
  char control=0;
  if(pread(control_fd,&control,1,0)!=1)return EBUR128_ERROR_NOMEM;
  if(control=='1') {
    const char marker='F';
    if(write(count_fd,&marker,1)!=1)_exit(125);
    return EBUR128_ERROR_NOMEM;
  }
  return real_add_frames(state,source,frames);
}

__attribute__((destructor)) static void close_files(void) {
  if(control_fd>=0)close(control_fd);
  if(count_fd>=0)close(count_fd);
}
