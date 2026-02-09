# Runbook: Upstream/Internet Health

## Quick Diagnosis
- DNS intern ok, extern fail ⇒ Upstream
- DNS extern ok, HTTPS extern fail ⇒ Externer HTTP-Pfad (SNI/HTTPS/Proxy/Firewall)
- DNS extern fail, HTTPS extern fail ⇒ Upstream oder Resolver-Probleme
- DNS extern ok, HTTPS extern ok ⇒ Internet-Pfad gesund; Fehler vermutlich intern

## Common Checks
1) Dry-run once to validate reachability:
```bash
source /etc/upstream-probe/secrets.env
upstream-probe --config /etc/upstream-probe/config.yml
```
2) If writes are expected, enable write and check Influx:
```bash
source /etc/upstream-probe/secrets.env
upstream-probe --config /etc/upstream-probe/config.yml --write
```
3) Check logs:
```bash
journalctl -u upstream-probe -n 200 --no-pager
```

## Failure Modes
- **DNS timeout**: Check resolver IP reachability and VLAN routing.
- **HTTP timeout**: Check outbound firewall/NAT and TLS interception.
- **Auth error on write**: Verify `INFLUX_TOKEN` and bucket/org.
