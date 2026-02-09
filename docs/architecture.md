# Architecture

## Overview
The service performs external DNS and HTTPS probes and writes measurements to InfluxDB. It is designed to separate internal resolver/application issues from upstream/provider outages.

### Components
- **CLI runner**: Loads config, enforces dry-run default, executes probes, and optionally writes metrics.
- **DNS probe**: Queries configured resolvers for a fixed name (default: `example.com`).
- **HTTP probe**: Sends HEAD/GET to configured targets (Cloudflare/GitHub by default).
- **Influx writer**: Converts results to line protocol and POSTs to InfluxDB v2 write API.

## Data Flow
1. Read config from YAML (+ env for secrets).
2. Execute DNS probes with strict timeout and bounded retries.
3. Execute HTTPS probes with strict timeout and bounded retries.
4. Build line protocol with tags `vlan`, `target`, `check_type` and fields `rtt_ms`, `http_status`, `dns_rcode`, `success`.
5. If `--write` is set, POST to InfluxDB; otherwise log what would be written (dry-run).

## Key Design Decisions
- **Read-only first**: Default is dry-run; writing requires `--write`.
- **Secrets isolation**: Influx token only via ENV or /etc/.../secrets.env (never committed).
- **Resilience**: Strict timeouts, exponential backoff, bounded retries.
- **Ops-friendly**: Systemd unit + tmpfiles for stable deployment in a homelab.

## Configuration and Defaults
- YAML config: [config.example.yml](../config.example.yml)
- Secrets: [​.env.example](../.env.example)

## Observability
- Structured logs (JSON) include probe target, status, rtt, and errors.
- Metrics measurement: `upstream_probe`.
