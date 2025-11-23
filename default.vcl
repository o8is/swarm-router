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

sub vcl_backend_response {
    # Remove Set-Cookie from backend responses
    unset beresp.http.Set-Cookie;

    # Cache based on Cache-Control headers set by Caddy
    if (beresp.http.Cache-Control ~ "max-age") {
        unset beresp.http.Set-Cookie;
        set beresp.ttl = std.duration(regsub(beresp.http.Cache-Control, ".*max-age=([0-9]+).*", "\1s"), 0s);
    }

    # Enable grace mode - serve stale content if backend is down
    set beresp.grace = 1h;

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
