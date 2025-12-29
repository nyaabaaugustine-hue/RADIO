FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV PORT=8000
RUN apt-get update && apt-get install -y icecast2 ca-certificates && rm -rf /var/lib/apt/lists/*

# Create the icecast user and group
RUN groupadd icecast && useradd -r -g icecast -s /usr/sbin/nologin icecast2

# Create necessary directories and set permissions
RUN mkdir -p /app /var/log/icecast2 /usr/share/icecast2/web /usr/share/icecast2/admin
RUN chown -R icecast2:icecast /app /var/log/icecast2 /usr/share/icecast2

WORKDIR /app

COPY render/icecast.xml /app/icecast.xml
COPY render/index.html /usr/share/icecast2/web/index.html

USER icecast2

EXPOSE 8000

CMD ["icecast2", "-c", "/app/icecast.xml"]
