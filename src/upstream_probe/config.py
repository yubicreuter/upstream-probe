from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AppConfig:
    name: str
    vlan: str
    log_level: str
    user_agent: str
    timeout_seconds: float
    retries: int
    backoff_base_seconds: float
    backoff_max_seconds: float


@dataclass(frozen=True)
class DNSConfig:
    query_name: str
    resolvers: list[str]


@dataclass(frozen=True)
class HTTPConfig:
    method: str
    targets: list[str]


@dataclass(frozen=True)
class InfluxConfig:
    url: str
    org: str
    bucket: str
    measurement: str


@dataclass(frozen=True)
class Config:
    app: AppConfig
    dns: DNSConfig
    http: HTTPConfig
    influx: InfluxConfig


class ConfigError(RuntimeError):
    pass


def _require(data: dict[str, Any], key: str) -> Any:
    if key not in data:
        raise ConfigError(f"Missing required config key: {key}")
    return data[key]


def load_config(path: Path) -> Config:
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict):
        raise ConfigError("Config root must be a mapping")

    app_raw = _require(raw, "app")
    dns_raw = _require(raw, "dns")
    http_raw = _require(raw, "http")
    influx_raw = _require(raw, "influx")

    app = AppConfig(
        name=str(_require(app_raw, "name")),
        vlan=str(_require(app_raw, "vlan")),
        log_level=str(_require(app_raw, "log_level")),
        user_agent=str(_require(app_raw, "user_agent")),
        timeout_seconds=float(_require(app_raw, "timeout_seconds")),
        retries=int(_require(app_raw, "retries")),
        backoff_base_seconds=float(_require(app_raw, "backoff_base_seconds")),
        backoff_max_seconds=float(_require(app_raw, "backoff_max_seconds")),
    )

    dns = DNSConfig(
        query_name=str(_require(dns_raw, "query_name")),
        resolvers=[str(item) for item in _require(dns_raw, "resolvers")],
    )

    http = HTTPConfig(
        method=str(_require(http_raw, "method")).upper(),
        targets=[str(item) for item in _require(http_raw, "targets")],
    )

    influx = InfluxConfig(
        url=str(_require(influx_raw, "url")),
        org=str(_require(influx_raw, "org")),
        bucket=str(_require(influx_raw, "bucket")),
        measurement=str(_require(influx_raw, "measurement")),
    )

    return Config(app=app, dns=dns, http=http, influx=influx)
