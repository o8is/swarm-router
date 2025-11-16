#!/usr/bin/env python3
import os, json, time, hashlib, requests

BEE_API       = os.getenv("BEE_API_URL", "http://bee:1633")
CADDY_ADMIN   = os.getenv("CADDY_ADMIN", "http://caddy:2019")
MAPPINGS_FEED = os.getenv("MAPPINGS_FEED", "bzz://f3f5e25c90824876c2468b9bdf0d842cd05dc5f0974681789b9729bc155c4f65/")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "300")) # Default 5 minutes
CACHE_MAX_AGE = int(os.getenv("CACHE_MAX_AGE", "3600"))  # Default 1 hour

last_hash = None

def fetch_mappings():
    feed_ref = MAPPINGS_FEED.replace("bzz://", "").strip("/")
    url = f"{BEE_API.rstrip('/')}/bzz/{feed_ref}/"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

def build_caddy_config(mappings):
    routes, subjects = [], []
    for dom, ref in mappings.items():
        if not ref.startswith("bzz:/"): continue
        # Convert bzz://hash... to /bzz/hash...
        bzz_path = "/" + ref.replace("://", "/").strip("/")
        subjects.append(dom)
        routes.append({
            "match": [{"host": [dom]}],
            "handle": [
                {
                    "handler": "rewrite",
                    "uri": bzz_path + "{http.request.uri}"
                },
                {
                    "handler": "headers",
                    "response": {
                        "set": {
                            "Cache-Control": [f"public, max-age={CACHE_MAX_AGE}"],
                            "CDN-Cache-Control": [f"max-age={CACHE_MAX_AGE}"]
                        }
                    }
                },
                {
                    "handler": "reverse_proxy",
                    "upstreams": [{"dial": "bee:1633"}]
                }
            ],
            "terminal": True
        })
    # fallback
    routes.append({
        "handle": [{
            "handler": "static_response",
            "body": """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Swarm Router - No Mapping</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 100px; background: #1a1a1a; color: #fff; }
        h1 { font-size: 48px; margin-bottom: 20px; }
        p { font-size: 18px; color: #888; }
    </style>
</head>
<body>
    <h1>🐝 Swarm Router</h1>
    <p>No mapping configured for this host.</p>
</body>
</html>""",
            "status_code": 404,
            "headers": {
                "Content-Type": ["text/html"]
            }
        }]
    })
    return {
        "apps": {
            "http": {"servers": {"main": {
                "listen": [":80"],
                "routes": routes
            }}}
        }
    }

def send_to_caddy(cfg):
    url = f"{CADDY_ADMIN.rstrip('/')}/load"
    r = requests.post(url, json=cfg, timeout=10)
    r.raise_for_status()

def build_warmup_config():
    """Build a Caddy config that shows a warming up message"""
    return {
        "apps": {
            "http": {"servers": {"main": {
                "listen": [":80"],
                "routes": [{
                    "handle": [{
                        "handler": "static_response",
                        "body": """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Swarm Router - Warming Up</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 100px; background: #1a1a1a; color: #fff; }
        .spinner { font-size: 48px; animation: spin 2s linear infinite; display: inline-block; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(-360deg); } }
    </style>
</head>
<body>
    <div class="spinner">🐝</div>
    <h1>Swarm Router</h1>
    <p>The Bee node is warming up. This page will refresh automatically.</p>
    <p><small>Please try again in a moment...</small></p>
</body>
</html>""",
                        "status_code": 503,
                        "headers": {
                            "Content-Type": ["text/html"],
                            "Retry-After": ["30"]
                        }
                    }]
                }]
            }}}
        }
    }

def main():
    global last_hash
    print(f"[INIT] Polling {MAPPINGS_FEED} → {CADDY_ADMIN}")

    # Set initial warmup page
    print("[INIT] Setting up warmup page...")
    try:
        send_to_caddy(build_warmup_config())
        print("[INIT] Warmup page configured")
    except Exception as e:
        print(f"[WARN] Could not set warmup page: {e}")

    # Wait for bee to finish warming up
    print("[INIT] Waiting for Bee to finish warming up...")
    status_url = f"{BEE_API.rstrip('/')}/status"

    for attempt in range(60):  # Try for up to 10 minutes
        try:
            r = requests.get(status_url, timeout=10)
            if r.status_code == 200:
                status = r.json()
                if not status.get("isWarmingUp", True):
                    print("[INIT] Bee warmup complete!")
                    break
                else:
                    print(f"[INIT] Bee warming up (attempt {attempt + 1}/60)...")
            else:
                print(f"[INIT] Bee status returned {r.status_code} (attempt {attempt + 1}/60)")
        except Exception as e:
            print(f"[INIT] Bee not reachable (attempt {attempt + 1}/60): {e}")
        time.sleep(10)
    else:
        print("[WARN] Bee did not finish warming up in time, continuing anyway...")

    while True:
        try:
            m = fetch_mappings()
            h = hashlib.sha256(json.dumps(m, sort_keys=True).encode()).hexdigest()
            if h != last_hash:
                print(f"[UPDATE] {list(m.keys())}")
                send_to_caddy(build_caddy_config(m))
                last_hash = h
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()