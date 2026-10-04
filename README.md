# Flexit Roomie (EcoVent v1) for Home Assistant

Local control of Flexit Roomie Wifi single-room ventilators, and the identical
Blauberg / TwinFresh / Vents units that use the older **EcoVent v1** Wi-Fi protocol.
No cloud, no device ID or password: the fan is controlled over UDP port 4000 on your
local network.

Not affiliated with or endorsed by Flexit or Blauberg.

## Features

- **Fan entity:** on/off, 3 speeds, and the three airflow modes as preset modes
  (`ventilation`, `heat_recovery`, `air_supply`)
- **Humidity sensor:** the humidity measured by the fan
- Non-blocking async UDP; the fan is polled every 30 seconds and shows as
  unavailable if it stops answering
- Unique IDs, so entities can be renamed and assigned to areas in the UI

## Compatibility

Tested with a Flexit Roomie Wifi that answers the v1 protocol (status replies start with
`master`). Newer **v2** units (e.g. Roomie One Wifi V2, Blauberg Vento Expert v.2) use a
different protocol with device ID and password and are **not** supported.

Quick check from any machine on the same network (replace the IP):

```sh
python3 -c "import socket;s=socket.socket(2,2);s.settimeout(3);s.sendto(bytes.fromhex('6D6F62696C6501000D0A'),('192.168.1.50',4000));print(s.recv(98))"
```

A reply starting with `b'master'` means the fan is supported.

## Installation

### HACS (custom repository)

1. HACS → ⋮ → **Custom repositories** → add this repository's URL, type **Integration**.
2. Install **Flexit Roomie (EcoVent v1)**.
3. Add the configuration below and restart Home Assistant.

### Manual

Copy `custom_components/flexit_roomie` into your Home Assistant `config/custom_components/`
folder, add the configuration below and restart.

## Configuration

`configuration.yaml`:

```yaml
flexit_roomie:
  devices:
    - name: "Living room ventilation"
      ip_address: 192.168.1.50
      # port: 4000  # optional
```

Give the fan a fixed IP address (DHCP reservation) in your router.

## Entities

| Entity | Description |
|---|---|
| `fan.<name>` | On/off, speed (33 / 67 / 100 %), preset mode |
| `sensor.<name>_luftfuktighet` | Humidity (%) |

If a manual speed has been set in the app, the fan reports it as a percentage of the
fan's manual range.

## Protocol notes

Packets are `6D6F62696C65` ("mobile") + command + `0D0A`, sent to UDP port 4000.

| Command | Bytes |
|---|---|
| Status request | `01 00` |
| Toggle power | `03 00` |
| Set speed 1-3 | `04 0N` |
| Set airflow mode 0-2 | `06 0N` |

The status reply is `master` followed by (parameter, value) pairs. Protocol details are
based on [aglehmann/pyEcovent](https://github.com/aglehmann/pyEcovent).

## License

MIT
