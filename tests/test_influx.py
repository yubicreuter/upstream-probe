from upstream_probe.influx import build_line_protocol


def test_build_line_protocol() -> None:
    line = build_line_protocol(
        "upstream_probe",
        {"vlan": "vlan-10", "target": "1.1.1.1", "check_type": "dns"},
        {"rtt_ms": 12.345, "dns_rcode": 0, "success": True},
    )
    assert line.startswith("upstream_probe,")
    assert "vlan=vlan-10" in line
    assert "check_type=dns" in line
    assert "rtt_ms=12.345" in line
    assert "dns_rcode=0i" in line
    assert "success=true" in line
