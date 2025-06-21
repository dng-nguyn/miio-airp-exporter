# Xiaomi Air Purifier (4 Lite) Prometheus Exporter
This is only tested for 4 Lite, but can be used with any devices that are supported by the [python-miio](https://python-miio.readthedocs.io/en/latest/) library.

To get device token, use this [script](https://gist.github.com/dng-nguyn/cd3d7a0fe3c10856057f80f9f663039a) or other legacy official methods [here.](https://python-miio.readthedocs.io/en/latest/legacy_token_extraction.html#legacy-token-extraction)

For other devices, modify and verify the MIoT specs accordingly - [Xiaomi MIoT Specs.](https://home.miot-spec.com/s/)

## Requirements:
```sh
pip install python-miio
apt install python3-prometheus-client
```

## Usage:
```sh
export.py JSON_FILE
```

JSON Configuration is as follow: 
```json
{
  "prometheus_port": 8000,
  "polling_interval_seconds": 60,
  "purifiers": [
    {
      "ip": "192.168.1.255",
      "token": "2c82ea271c375619b845c3d1f3e775f3",
      "name": "Bedroom"
     }
  ]
}
```
Support for multiple devices is untested, I have no idea if it would work.
