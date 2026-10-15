FROM mcr.microsoft.com/dotnet/sdk:8.0.414-bookworm-slim@sha256:ff8311847c54c04d1a14c488362807997d59b61372da5095a95f89cbcda7f9b7 AS build
# Launcher dependencies, inside the image only; no desktop clients/services.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3=3.11.2-1+b1 python3-minimal=3.11.2-1+b1 libpython3-stdlib=3.11.2-1+b1 \
    python3.11=3.11.2-6+deb12u9 python3.11-minimal=3.11.2-6+deb12u9 \
    libpython3.11-stdlib=3.11.2-6+deb12u9 libpython3.11-minimal=3.11.2-6+deb12u9 \
    && rm -rf /var/lib/apt/lists/*
ENV DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_EnableDiagnostics=0

FROM build AS ci
# Generates plain synthetic E-AC-3 only; not a JOC encoder or runtime decoder.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg=7:5.1.9-0+deb12u1 \
    && rm -rf /var/lib/apt/lists/*

FROM ci AS live-ci-legacy
# Native virtual-sink acceptance only; no host sound devices/session sockets.
RUN apt-get update && apt-get install -y --no-install-recommends \
    pipewire=0.3.65-3+deb12u1 pipewire-bin=0.3.65-3+deb12u1 \
    libpipewire-0.3-modules=0.3.65-3+deb12u1 libspa-0.2-modules=0.3.65-3+deb12u1 \
    wireplumber=0.4.13-1 dbus=1.14.10-1~deb12u1 \
    dbus-daemon=1.14.10-1~deb12u1 dbus-bin=1.14.10-1~deb12u1 \
    dbus-session-bus-common=1.14.10-1~deb12u1 \
    && rm -rf /var/lib/apt/lists/*

FROM ubuntu@sha256:ee126c2fa0249079a7e24ae3a3d29b04783ef93ab33c868751c9a1289d3fffff AS live-ci
# Match the laptops' native PipeWire/WirePlumber versions. Keep the legacy
# diagnostic stage above; its partial-fragment capture failures remain history.
COPY --from=build /usr/share/dotnet /usr/share/dotnet
ENV DOTNET_ROOT=/usr/share/dotnet PATH=/usr/share/dotnet:$PATH \
    DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_EnableDiagnostics=0
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3=3.14.7-3 \
    python3-minimal=3.14.7-3 \
    libpython3-stdlib=3.14.7-3 \
    python3.14=3.14.8-1ubuntu1 \
    python3.14-minimal=3.14.8-1ubuntu1 \
    libpython3.14-stdlib=3.14.8-1ubuntu1 \
    libpython3.14-minimal=3.14.8-1ubuntu1 \
    git=1:2.55.0-1ubuntu1 \
    ca-certificates=20260816 \
    libicu78=78.3-2ubuntu1 \
    libssl3t64=3.5.5-1ubuntu6 \
    libgssapi-krb5-2=1.22.1-3ubuntu2 \
    ffmpeg=7:8.1.2-2ubuntu2 \
    pipewire=1.6.8-1ubuntu4 \
    pipewire-bin=1.6.8-1ubuntu4 \
    libpipewire-0.3-0t64=1.6.8-1ubuntu4 \
    libpipewire-0.3-modules=1.6.8-1ubuntu4 \
    libspa-0.2-modules=1.6.8-1ubuntu4 \
    wireplumber=0.5.17-1ubuntu1 \
    libwireplumber-0.5-0=0.5.17-1ubuntu1 \
    dbus=1.16.2-5ubuntu2 \
    dbus-daemon=1.16.2-5ubuntu2 \
    dbus-bin=1.16.2-5ubuntu2 \
    dbus-session-bus-common=1.16.2-5ubuntu2 \
    && rm -rf /var/lib/apt/lists/*

FROM live-ci AS live-compiler
# Separate build layer; selected acceptance still runs in the unchanged live-ci image.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    binutils-common=2.47-6ubuntu1 \
    binutils-x86-64-linux-gnu=2.47-6ubuntu1 \
    binutils=2.47-6ubuntu1 \
    cpp-15-x86-64-linux-gnu=15.3.0-4ubuntu1 \
    cpp-15=15.3.0-4ubuntu1 \
    cpp-x86-64-linux-gnu=4:15.2.0-5ubuntu1 \
    cpp=4:15.2.0-5ubuntu1 \
    gcc-15-base=15.3.0-4ubuntu1 \
    gcc-15-x86-64-linux-gnu=15.3.0-4ubuntu1 \
    gcc-15=15.3.0-4ubuntu1 \
    gcc-x86-64-linux-gnu=4:15.2.0-5ubuntu1 \
    gcc=4:15.2.0-5ubuntu1 \
    libasan8=16.2.0-3ubuntu1 \
    libbinutils=2.47-6ubuntu1 \
    libc-bin=2.44-1ubuntu2 \
    libc-dev-bin=2.44-1ubuntu2 \
    libc-gconv-modules-extra=2.44-1ubuntu2 \
    libc6-dev=2.44-1ubuntu2 \
    libc6=2.44-1ubuntu2 \
    libcc1-0=16.2.0-3ubuntu1 \
    libctf-nobfd0=2.47-6ubuntu1 \
    libctf0=2.47-6ubuntu1 \
    libgcc-15-dev=15.3.0-4ubuntu1 \
    libgprofng0=2.47-6ubuntu1 \
    libhwasan0=16.2.0-3ubuntu1 \
    libisl23=0.28-1 \
    libitm1=16.2.0-3ubuntu1 \
    libjansson4=2.15.1-1 \
    liblsan0=16.2.0-3ubuntu1 \
    libmpc3=1.3.1-3 \
    libmpfr6=4.2.2-3 \
    libpipewire-0.3-dev=1.6.8-1ubuntu4 \
    libpkgconf7=2.5.1-4 \
    libquadmath0=16.2.0-3ubuntu1 \
    libsframe3=2.47-6ubuntu1 \
    libspa-0.2-dev=1.6.8-1ubuntu4 \
    libtsan2=16.2.0-3ubuntu1 \
    libubsan1=16.2.0-3ubuntu1 \
    linux-libc-dev=7.3.0-9.9 \
    pkg-config=2.5.1-4 \
    pkgconf-bin=2.5.1-4 \
    pkgconf=2.5.1-4 \
    && rm -rf /var/lib/apt/lists/*
