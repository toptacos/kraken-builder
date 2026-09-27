FROM alpine:3.20
RUN apk add --no-cache bash
WORKDIR /opt/facts
COPY . .
CMD ["bash", "handler.sh"]
