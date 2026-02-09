from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Iterable

import dns.message
import dns.query
import dns.rcode
import httpx


@dataclass(frozen=True)
class ProbeResult:
    target: str
    check_type: str
    rtt_ms: float
    success: bool
    http_status: int | None = None
    dns_rcode: int | None = None
    error: str | None = None


def _sleep_backoff(base: float, max_backoff: float, attempt: int) -> None:
    delay = min(base * (2 ** (attempt - 1)), max_backoff)
    time.sleep(delay)


def _with_retries(
    fn: Callable[[], ProbeResult],
    retries: int,
    base: float,
    max_backoff: float,
) -> ProbeResult:
    attempt = 0
    last_error: ProbeResult | None = None
    while attempt <= retries:
        attempt += 1
        result = fn()
        if result.success:
            return result
        last_error = result
        if attempt <= retries:
            _sleep_backoff(base, max_backoff, attempt)
    return last_error if last_error is not None else fn()


def run_dns_probe(
    resolver: str,
    query_name: str,
    timeout_seconds: float,
    retries: int,
    backoff_base: float,
    backoff_max: float,
) -> ProbeResult:
    def _attempt() -> ProbeResult:
        start = time.perf_counter()
        try:
            request = dns.message.make_query(query_name, "A")
            response = dns.query.udp(request, resolver, timeout=timeout_seconds)
            rtt = (time.perf_counter() - start) * 1000.0
            return ProbeResult(
                target=resolver,
                check_type="dns",
                rtt_ms=rtt,
                success=response.rcode() == dns.rcode.NOERROR,
                dns_rcode=int(response.rcode()),
            )
        except Exception as exc:  # noqa: BLE001
            rtt = (time.perf_counter() - start) * 1000.0
            return ProbeResult(
                target=resolver,
                check_type="dns",
                rtt_ms=rtt,
                success=False,
                dns_rcode=None,
                error=str(exc),
            )

    return _with_retries(_attempt, retries, backoff_base, backoff_max)


def run_http_probe(
    url: str,
    method: str,
    timeout_seconds: float,
    retries: int,
    backoff_base: float,
    backoff_max: float,
    user_agent: str,
) -> ProbeResult:
    def _attempt() -> ProbeResult:
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=timeout_seconds, headers={"User-Agent": user_agent}) as client:
                response = client.request(method, url, follow_redirects=True)
            rtt = (time.perf_counter() - start) * 1000.0
            return ProbeResult(
                target=url,
                check_type="http",
                rtt_ms=rtt,
                success=response.status_code < 500,
                http_status=int(response.status_code),
            )
        except Exception as exc:  # noqa: BLE001
            rtt = (time.perf_counter() - start) * 1000.0
            return ProbeResult(
                target=url,
                check_type="http",
                rtt_ms=rtt,
                success=False,
                http_status=None,
                error=str(exc),
            )

    return _with_retries(_attempt, retries, backoff_base, backoff_max)


def run_all_dns(
    resolvers: Iterable[str],
    query_name: str,
    timeout_seconds: float,
    retries: int,
    backoff_base: float,
    backoff_max: float,
) -> list[ProbeResult]:
    return [
        run_dns_probe(resolver, query_name, timeout_seconds, retries, backoff_base, backoff_max)
        for resolver in resolvers
    ]


def run_all_http(
    targets: Iterable[str],
    method: str,
    timeout_seconds: float,
    retries: int,
    backoff_base: float,
    backoff_max: float,
    user_agent: str,
) -> list[ProbeResult]:
    return [
        run_http_probe(target, method, timeout_seconds, retries, backoff_base, backoff_max, user_agent)
        for target in targets
    ]
