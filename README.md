# upstream-probe

External DNS + HTTPS probes to distinguish internal vs upstream failures.

## Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
```

## Configure
1) Create config and secrets:
```bash
cp config.example.yml /etc/upstream-probe/config.yml
cp .env.example /etc/upstream-probe/secrets.env
```
2) Edit:
- /etc/upstream-probe/config.yml (non-secret config)
- /etc/upstream-probe/secrets.env (export INFLUX_TOKEN)

## Run (dry-run default)
```bash
source /etc/upstream-probe/secrets.env
upstream-probe --config /etc/upstream-probe/config.yml
```

## Run (write enabled)
```bash
source /etc/upstream-probe/secrets.env
upstream-probe --config /etc/upstream-probe/config.yml --write
```

## Systemd
```bash
sudo cp deploy/systemd/upstream-probe.service /etc/systemd/system/
sudo cp deploy/systemd/upstream-probe.tmpfiles /etc/tmpfiles.d/upstream-probe.conf
sudo systemd-tmpfiles --create /etc/tmpfiles.d/upstream-probe.conf
sudo systemctl daemon-reload
sudo systemctl enable --now upstream-probe
```

## Tests & Quality
```bash
ruff check .
ruff format .
mypy src
pytest
```

## Upgrade
```bash
git pull
pip install -e .
sudo systemctl restart upstream-probe
```

## Rollback
```bash
git checkout <tag-or-commit>
pip install -e .
sudo systemctl restart upstream-probe
```

## Troubleshooting
- Check logs: `journalctl -u upstream-probe -n 200 --no-pager`
- Verify config path and INFLUX_TOKEN is set.
- Run a single dry-run to validate network reachability.

## Docs
- Architecture: [docs/architecture.md](docs/architecture.md)
- Runbook: [docs/runbook.md](docs/runbook.md)