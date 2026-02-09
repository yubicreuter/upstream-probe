from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import httpx

from .probes import ProbeResult


@dataclass(frozen=True)
class InfluxWriteRequest:
    url: str
    org: str
    bucket: str
    measurement: str
    token: str


def _escape_tag(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(" ", "\\ ")
        .replace(",", "\\,")
        .replace("=", "\\=")
    )


def _format_field(value: int | float | bool) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return f"{value}i"
    return f"{value:.3f}"


def build_line_protocol(
    measurement: str,
    tags: dict[str, str],
    fields: dict[str, int | float | bool],
) -> str:
    tag_set = ",".join(f"{k}={_escape_tag(v)}" for k, v in tags.items())
    field_set = ",".join(f"{k}={_format_field(v)}" for k, v in fields.items())
    if tag_set:
        return f"{measurement},{tag_set} {field_set}"
    return f"{measurement} {field_set}"


def results_to_lines(
    measurement: str,
    vlan: str,
    results: Iterable[ProbeResult],
) -> list[str]:
    lines: list[str] = []
    for result in results:
        fields: dict[str, int | float | bool] = {
            "rtt_ms": float(result.rtt_ms),
            "success": bool(result.success),
        }
        if result.http_status is not None:
            fields["http_status"] = int(result.http_status)
        if result.dns_rcode is not None:
            fields["dns_rcode"] = int(result.dns_rcode)

        tags = {
            "vlan": vlan,
            "target": result.target,
            "check_type": result.check_type,
        }
        lines.append(build_line_protocol(measurement, tags, fields))
    return lines


def write_lines(request: InfluxWriteRequest, lines: Iterable[str], timeout_seconds: float) -> None:
    payload = "\n".join(lines)
    url = f"{request.url}/api/v2/write"
    params = {"org": request.org, "bucket": request.bucket, "precision": "ms"}
    headers = {"Authorization": f"Token {request.token}"}
    with httpx.Client(timeout=timeout_seconds, headers=headers) as client:
        response = client.post(url, params=params, content=payload)
    response.raise_for_status()
