FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1

# Install only in this disposable build image. Runtime has no network,
# sound devices, desktop sockets or owner configuration mounts.
RUN pip install --no-cache-dir \
    numpy==2.2.6 scipy==1.15.3 pytest==8.3.5 pytest-xdist==3.6.1

ENV PYTHONDONTWRITEBYTECODE=1 \
    OPENBLAS_NUM_THREADS=1 \
    OMP_NUM_THREADS=1 \
    XDG_CONFIG_HOME=/tmp/empty-config \
    XDG_DATA_HOME=/tmp/empty-data \
    XDG_RUNTIME_DIR=/tmp/empty-runtime

WORKDIR /repo
