from scripts.serial_bridge import parse_reading


def test_parse_serial_reading():
    assert parse_reading("Temperature: 25.0 C | Humidity: 48.0 %") == (25.0, 48.0)
    assert parse_reading("DHT11 read failed") is None

