# Swarm Router

A high-performance, zero-configuration gateway for Ethereum Swarm that routes domains based on DNSLink records.

## Overview

Swarm Router allows you to point any domain to Ethereum Swarm content without configuring the server. It uses a "Pull" model where the configuration lives in the DNS records of the domains themselves, rather than a central configuration file.

### Architecture

1.  **Caddy (with [caddy-dnslink](https://github.com/o8is/caddy-dnslink))**: The entry point. It intercepts requests, looks up the `_dnslink` TXT record for the hostname, and rewrites the request to the corresponding Swarm hash.
2.  **Gatekeeper**: A security sidecar that validates domains before Caddy issues TLS certificates. It ensures that only domains with valid DNSLink records are allowed to consume resources.
3.  **Varnish**: A high-performance HTTP accelerator that caches Swarm content to reduce load on the Bee node and improve response times.
4.  **Bee**: The Ethereum Swarm node that retrieves content from the decentralized network.

## Features

*   **Zero-Configuration**: Add a new domain just by creating DNS records. No server restarts or API calls required.
*   **On-Demand TLS**: Automatically provisions and renews HTTPS certificates for any valid domain that points to the router.
*   **DNSLink Support**: Fully compatible with the [DNSLink standard](https://dnslink.dev).
*   **Smart Caching**: Varnish caching tuned for immutable Swarm content.
*   **DDoS Protection**: Gatekeeper prevents TLS abuse by verifying domain ownership via DNS before issuance.

## Usage

To point a domain to your Swarm Router:

1.  **CNAME Record**: Point your domain to the router's hostname (or A record to its IP).
    ```text
    example.com.  IN  CNAME  router.your-domain.com.
    ```

2.  **TXT Record**: Create a `_dnslink` TXT record containing the Swarm reference.
    ```text
    _dnslink.example.com.  IN  TXT  "dnslink=/swarm/<hash>"
    ```

The router will automatically detect these records, provision an SSL certificate, resolve the hash, and serve the content.

## Deployment

### Akash Network

This project is optimized for deployment on the [Akash Network](https://akash.network).

1.  Use the provided `deploy.yaml`.
2.  Adjust the resource profiles if necessary.
3.  Deploy using the Akash Console or CLI.

### Docker Compose

You can run the stack locally or on a VPS using Docker Compose:

```bash
docker compose up -d
```

## Components

*   **`swarm-router-caddy`**: Custom Caddy build including the [caddy-dnslink](https://github.com/o8is/caddy-dnslink) module.
*   **`swarm-router-gatekeeper`**: Go service that acts as an `ask` endpoint for Caddy's On-Demand TLS.
*   **`swarm-router-varnish`**: Varnish Cache configured for Swarm.
*   **`ethersphere/bee`**: Official Swarm node.

## License

MIT
