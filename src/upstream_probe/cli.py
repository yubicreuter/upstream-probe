from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .config import ConfigError, load_config
from .influx import InfluxWriteRequest, results_to_lines, write_lines
from .logging import configure_logging, log_event
from .probes import run_all_dns, run_all_http

EXIT_OK = 0
EXIT_CONFIG = 2
EXIT_RUNTIME = 3


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upstream DNS/HTTPS probe")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to config YAML",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Enable InfluxDB writes (default: dry-run)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        config = load_config(Path(args.config))
    except (OSError, ConfigError) as exc:
        print(f"config_error: {exc}")
        return EXIT_CONFIG

    configure_logging(config.app.log_level)
    log_event("startup", app=config.app.name, vlan=config.app.vlan, write=args.write)

    dns_results = run_all_dns(
        resolvers=config.dns.resolvers,
        query_name=config.dns.query_name,
        timeout_seconds=config.app.timeout_seconds,
        retries=config.app.retries,
        backoff_base=config.app.backoff_base_seconds,
        backoff_max=config.app.backoff_max_seconds,
    )
    http_results = run_all_http(
        targets=config.http.targets,
        method=config.http.method,
        timeout_seconds=config.app.timeout_seconds,
        retries=config.app.retries,
        backoff_base=config.app.backoff_base_seconds,
        backoff_max=config.app.backoff_max_seconds,
        user_agent=config.app.user_agent,
    )

    for result in [*dns_results, *http_results]:
        log_event(
            "probe_result",
            target=result.target,
            check_type=result.check_type,
            rtt_ms=round(result.rtt_ms, 3),
            success=result.success,
            http_status=result.http_status,
            dns_rcode=result.dns_rcode,
            error=result.error,
        )

    lines = results_to_lines(config.influx.measurement, config.app.vlan, [*dns_results, *http_results])

    if args.write:
        token = os.getenv("INFLUX_TOKEN")
        if not token:
            log_event("write_skipped", reason="missing_influx_token")
            return EXIT_RUNTIME
        request = InfluxWriteRequest(
            url=config.influx.url,
            org=config.influx.org,
            bucket=config.influx.bucket,
            measurement=config.influx.measurement,
            token=token,
        )
        try:
            write_lines(request, lines, timeout_seconds=config.app.timeout_seconds)
            log_event("write_ok", count=len(lines))
        except Exception as exc:  # noqa: BLE001
            log_event("write_failed", error=str(exc))
            return EXIT_RUNTIME
    else:
        log_event("dry_run", count=len(lines))

    return EXIT_OK
