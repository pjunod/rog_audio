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
