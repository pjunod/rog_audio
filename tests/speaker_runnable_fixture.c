/* Silent owned Linux integration fixture; no audio, device or bus access. */
#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <pthread.h>
#include <sys/syscall.h>
#include <string.h>
#include <sys/epoll.h>
#include <sys/eventfd.h>
#include <sys/prctl.h>
#include <sys/resource.h>
#include <sys/timerfd.h>
#include <sched.h>
#include <signal.h>
#include <time.h>
#include <unistd.h>

static uint64_t now(clockid_t clock) {
    struct timespec ts;
    if (clock_gettime(clock, &ts)) _exit(10);
    return (uint64_t)ts.tv_sec * 1000000000 + ts.tv_nsec;
}
__attribute__((noinline)) static void finite_cpu_work(void) {
    uint64_t until = now(CLOCK_THREAD_CPUTIME_ID) + 120000000;
    volatile uint64_t value = 1;
    while (now(CLOCK_THREAD_CPUTIME_ID) < until)
        for (int i = 0; i < 1000; ++i) value = value * 1664525 + 1013904223;
}
static int run_mode(const char *mode) {
    if (prctl(PR_SET_NAME, "rog-rt-fixture", 0, 0, 0)) return 3;
    char announcement[32];
    int length = snprintf(announcement, sizeof announcement, "%ld\n", syscall(SYS_gettid));
    if (length <= 0 || length >= (int)sizeof announcement ||
        write(STDOUT_FILENO, announcement, (size_t)length) != length) return 14;
    char gate;
    if (read(STDIN_FILENO, &gate, 1) != 1 || gate != 'G') return 4;
    alarm(3);
    struct rlimit cpu = {RLIM_INFINITY, RLIM_INFINITY};
    struct rlimit rt = {200000, 200000};
    struct sched_param param = {.sched_priority = 1};
    if (setrlimit(RLIMIT_CPU, &cpu) || setrlimit(RLIMIT_RTTIME, &rt) ||
        sched_setscheduler(0, SCHED_RR | SCHED_RESET_ON_FORK, &param)) return 5;
    if (!strcmp(mode, "busy")) { finite_cpu_work(); return 0; }
    int blocking = !strcmp(mode, "blocking");
    int ep = epoll_create1(EPOLL_CLOEXEC);
    int fd = blocking ? timerfd_create(CLOCK_MONOTONIC, TFD_CLOEXEC) : eventfd(1, EFD_CLOEXEC);
    if (ep < 0 || fd < 0) return 6;
    struct epoll_event event = {.events = EPOLLIN, .data.fd = fd};
    if (epoll_ctl(ep, EPOLL_CTL_ADD, fd, &event)) return 7;
    if (blocking) {
        struct itimerspec timer = {.it_interval = {.tv_nsec = 10000000}, .it_value = {.tv_nsec = 10000000}};
        if (timerfd_settime(fd, 0, &timer, 0)) return 8;
    }
    uint64_t until = now(blocking ? CLOCK_MONOTONIC : CLOCK_THREAD_CPUTIME_ID) + 120000000;
    while (now(blocking ? CLOCK_MONOTONIC : CLOCK_THREAD_CPUTIME_ID) < until) {
        if (epoll_wait(ep, &event, 1, -1) != 1) return 9;
        if (blocking) { uint64_t count; if (read(fd, &count, sizeof count) != sizeof count) return 11; }
        /* ready mode intentionally leaves eventfd readable. */
    }
    close(fd); close(ep);
    return 0;
}

static void *worker(void *mode) {
    return (void *)(intptr_t)run_mode(mode);
}
int main(int argc, char **argv) {
    if (argc != 2 || (strcmp(argv[1], "blocking") && strcmp(argv[1], "ready") && strcmp(argv[1], "busy"))) return 2;
    if (signal(SIGALRM, SIG_DFL) == SIG_ERR) return 12;
    sigset_t alarms;
    sigemptyset(&alarms); sigaddset(&alarms, SIGALRM);
    if (sigprocmask(SIG_UNBLOCK, &alarms, 0)) return 13;
    alarm(20); /* Attachment gate also has a process-wide kernel deadline. */
    if (!strcmp(argv[1], "ready")) {
        pthread_t thread;
        void *result;
        if (pthread_create(&thread, NULL, worker, argv[1])) return 15;
        if (pthread_join(thread, &result)) return 16;
        return (int)(intptr_t)result;
    }
    return run_mode(argv[1]);
}
