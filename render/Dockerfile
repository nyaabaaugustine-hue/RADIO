FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV PORT=10000
RUN apt-get update && apt-get install -y icecast2 ca-certificates jq curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY icecast.xml /app/icecast.xml
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh && mkdir -p /var/log/icecast2 /usr/share/icecast2/web /usr/share/icecast2/admin
EXPOSE 10000
CMD ["/app/start.sh"]
