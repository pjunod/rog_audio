FROM ubuntu@sha256:ee126c2fa0249079a7e24ae3a3d29b04783ef93ab33c868751c9a1289d3fffff
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    gcc libc6-dev pkg-config python3 libpipewire-0.3-dev=1.6.8-1ubuntu4 \
    pipewire=1.6.8-1ubuntu4 wireplumber=0.5.17-1ubuntu1 \
    && rm -rf /var/lib/apt/lists/*
