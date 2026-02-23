vcl 4.1;

import std;

backend bee {
    .host = "bee";
    .port = "1633";
    .connect_timeout = 10s;
    .first_byte_timeout = 30s;
    .between_bytes_timeout = 10s;
}

sub vcl_recv {
    # Pass POST, PUT, DELETE and other non-GET/HEAD requests directly to backend
    if (req.method != "GET" && req.method != "HEAD") {
        return (pass);
    }

    # Use bee as backend
    set req.backend_hint = bee;

    # Normalize Accept-Encoding to improve cache hit ratio
    if (req.http.Accept-Encoding) {
        if (req.http.Accept-Encoding ~ "gzip") {
            set req.http.Accept-Encoding = "gzip";
        } elsif (req.http.Accept-Encoding ~ "deflate") {
            set req.http.Accept-Encoding = "deflate";
        } else {
            unset req.http.Accept-Encoding;
        }
    }

    # Remove cookies (Swarm doesn't use them)
    unset req.http.Cookie;

    return (hash);
}

sub vcl_hit {
    # Object is stale (expired)
    if (obj.ttl + obj.grace > 0s) {
        # Within grace period: serve stale immediately and refresh in background
        return (deliver);
    }

    # Beyond grace period: restart request to fetch fresh
    return (restart);
}

sub vcl_backend_response {
    # Remove Set-Cookie from backend responses
    unset beresp.http.Set-Cookie;

    # Don't cache error responses (especially 404s). Content-addressed
    # uploads may return 404 briefly before the data is available
    if (beresp.status >= 400) {
        set beresp.ttl = 0s;
        set beresp.grace = 0s;
        set beresp.uncacheable = true;
        return (deliver);
    }

    # Cache based on Cache-Control headers set by Caddy
    if (beresp.http.Cache-Control ~ "max-age") {
        unset beresp.http.Set-Cookie;
        set beresp.ttl = std.duration(regsub(beresp.http.Cache-Control, ".*max-age=([0-9]+).*", "\1s"), 0s);
    }

    # Enable grace mode - serve stale content if backend is down
    set beresp.grace = 24h;

    return (deliver);
}

sub vcl_deliver {
    # Add header to show cache status
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
        set resp.http.X-Cache-Hits = obj.hits;
    } else {
        set resp.http.X-Cache = "MISS";
    }

    return (deliver);
}
