from pathlib import Path

import yaml

from upstream_probe.config import load_config


def test_load_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "app": {
                    "name": "upstream-probe",
                    "vlan": "vlan-10",
                    "log_level": "INFO",
                    "user_agent": "ua",
                    "timeout_seconds": 1.5,
                    "retries": 1,
                    "backoff_base_seconds": 0.1,
                    "backoff_max_seconds": 0.5,
                },
                "dns": {"query_name": "example.com", "resolvers": ["1.1.1.1"]},
                "http": {"method": "HEAD", "targets": ["https://example.com"]},
                "influx": {
                    "url": "http://localhost:8086",
                    "org": "org",
                    "bucket": "bucket",
                    "measurement": "upstream_probe",
                },
            }
        )
    )
    cfg = load_config(config_path)
    assert cfg.app.name == "upstream-probe"
    assert cfg.dns.resolvers == ["1.1.1.1"]
