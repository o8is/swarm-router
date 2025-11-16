# Swarm Router

Dynamic domain routing for Ethereum Swarm. Maps custom domains to Swarm content using a decentralized configuration feed.

## How it works

1. **Poller** fetches domain mappings from Swarm
2. **Caddy** gets configured to route each domain to its Swarm content
3. **Bee** serves the actual content from the Swarm network

## Configuration

Create a JSON mapping file and upload it to Swarm:

```json
{
  "example.com": "bzz://abc123.../",
  "docs.example.com": "bzz://xyz789.../"
}
```

Set environment variables:

```
MAPPINGS_FEED=bzz://your-mapping-hash/
POLL_INTERVAL=300          # seconds between updates
CACHE_MAX_AGE=3600         # browser cache duration in seconds
```

## Deployment

The poller image is available on Docker Hub: `octalmage/swarm-caddy-poller`

Deploy to Akash using the [Akash Console](https://console.akash.network/) with the included `deploy.yaml`.

## Building (optional)

If you want to build your own image:

```bash
docker build --platform linux/amd64 -t your-image:latest --push .
```

## License

MIT
