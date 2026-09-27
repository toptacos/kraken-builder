# User compiler. Core does not ship gcc.
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /work
COPY handler.c /work/handler.c
RUN gcc -O2 -o /usr/local/bin/hello /work/handler.c
ENTRYPOINT ["/usr/local/bin/hello"]
