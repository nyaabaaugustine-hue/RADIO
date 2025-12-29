FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV PORT=8000
RUN apt-get update && apt-get install -y icecast2 ca-certificates jq curl mime-support && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY render/icecast.xml /app/icecast.xml
COPY render/start.sh /app/start.sh
COPY render/index.html /usr/share/icecast2/web/index.html
RUN chmod +x /app/start.sh && mkdir -p /var/log/icecast2 /usr/share/icecast2/web /usr/share/icecast2/admin
RUN id -u icecast2 >/dev/null 2>&1 || useradd -r -g icecast -s /usr/sbin/nologin icecast2 \
  && mkdir -p /usr/share/icecast2 /var/log/icecast2 /usr/share/icecast2/web /usr/share/icecast2/admin \
  && chown -R icecast2:icecast /var/log/icecast2 /usr/share/icecast2 /app
USER icecast2
EXPOSE 8000
CMD ["/app/start.sh"]
