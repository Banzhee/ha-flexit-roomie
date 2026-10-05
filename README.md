# Flexit Roomie (EcoVent v1) for Home Assistant

Local control of Flexit Roomie Wifi single-room ventilators, and the identical
Blauberg / TwinFresh / Vents units that use the older **EcoVent v1** Wi-Fi protocol.
No cloud, no device ID or password: the fan is controlled over UDP port 4000 on your
local network.

Not affiliated with or endorsed by Flexit or Blauberg.

## Features

- **Fan entity:** on/off, 3 speeds, and the three airflow modes as preset modes
  (Ventilation, Heat recovery, Air supply; translated to Norwegian Bokmål)
- **Humidity sensor:** the humidity measured by the fan
- Non-blocking async UDP; the fan is polled every 30 seconds and shows as
  unavailable if it stops answering
- **Set up from the UI:** add each fan under Settings → Devices & services; the address
  is checked before the device is created
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

1. HACS → ⋮ → **Custom repositories** → add `https://github.com/Banzhee/ha-flexit-roomie`, type **Integration**.
2. Install **Flexit Roomie (EcoVent v1)** and restart Home Assistant.
3. **Settings → Devices & services → Add integration → Flexit Roomie**.

### Manual

Copy `custom_components/flexit_roomie` into your Home Assistant `config/custom_components/`
folder, restart, then add the integration from **Settings → Devices & services**.

## Configuration

Setup is done in the UI; there is nothing to put in `configuration.yaml`. Adding the
integration asks for a name, the fan's IP address and the port (4000 unless you have
changed it), and checks that the fan answers before the device is created. Add the
integration once per fan.

Give each fan a fixed IP address (a DHCP reservation in your router) so it does not
change later.

### Upgrading from 1.x

The old YAML block is still read once: on the first start after upgrading, each device
under `flexit_roomie:` is imported into the UI and a warning is logged. Entities keep
their IDs and history. Delete the `flexit_roomie:` block from `configuration.yaml`
afterwards.

## Entities

Each fan becomes a device with two entities:

| Entity | Description |
|---|---|
| `fan.<name>` | On/off, speed (33 / 67 / 100 %), preset mode |
| `sensor.<name>_humidity` | Relative humidity (%) measured by the fan |

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

The status reply is `master` followed by (parameter, value) pairs. Parameter ids that are
not in the table are skipped a byte at a time rather than ending the parse, because the
fan sends ids that are not documented - one of them sits directly before the humidity.
Protocol details are
based on [aglehmann/pyEcovent](https://github.com/aglehmann/pyEcovent).

## License

MIT
