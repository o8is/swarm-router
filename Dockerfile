FROM ghcr.io/o8is/caddy-dnslink:0.1.0 AS source

FROM caddy:2.7.5

COPY --from=source /usr/bin/caddy /usr/bin/caddy
COPY Caddyfile /etc/caddy/Caddyfile
COPY error.html /etc/caddy/error.html
