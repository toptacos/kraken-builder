# syntax=docker/dockerfile:1
FROM python:3.12-alpine AS runtime
WORKDIR /opt/board
RUN apk add --no-cache git bash
COPY handler.sh handler.py tentacle.yaml board.yaml ./
COPY workflows ./workflows
COPY suckers ./suckers
COPY tests ./tests
RUN chmod +x handler.sh handler.py
ENV KRAKEN_OFFLINE=1
CMD ["python3", "tests/test_board.py", "-v"]
