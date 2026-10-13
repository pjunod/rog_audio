# Source is the GPL-3.0-or-later upstream EasyEffects v8.2.8 snapshot, supplied
# with the pinned patch series applied, as easyeffects/ in this public-only context.
FROM ubuntu@sha256:ee126c2fa0249079a7e24ae3a3d29b04783ef93ab33c868751c9a1289d3fffff
ENV DEBIAN_FRONTEND=noninteractive
RUN sed -i 's/^Types: deb$/Types: deb deb-src/' /etc/apt/sources.list.d/ubuntu.sources \
 && apt-get update \
 && apt-get build-dep -y easyeffects=8.2.8+ds-1build1 \
 && apt-get install -y --no-install-recommends cmake ninja-build g++ git python3 \
      easyeffects=8.2.8+ds-1build1 pipewire=1.6.8-1ubuntu4 wireplumber=0.5.17-1ubuntu1 lsp-plugins-lv2 lilv-utils dbus \
 && rm -rf /var/lib/apt/lists/*
COPY easyeffects/ /src/easyeffects/
COPY source.json /opt/rog-audio/easyeffects-source.json
RUN cmake -S /src/easyeffects -B /build/easyeffects -G Ninja \
      -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/opt/rog-audio/easyeffects \
 && cmake --build /build/easyeffects --parallel 1 \
 && cmake --install /build/easyeffects
COPY probes/ /src/probes/
RUN c++ -std=c++20 -Wall -Wextra /src/probes/mock_device.cpp $(pkg-config --cflags --libs libpipewire-0.3) -o /opt/rog-audio/mock-device \
 && cc -std=c11 -Wall -Wextra /src/probes/synthetic_player.c $(pkg-config --cflags --libs libpipewire-0.3) -lm -o /opt/rog-audio/synthetic-player
