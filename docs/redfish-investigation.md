# Raritan Redfish API Investigation

## Conclusion

**Decision: Keep JSON-RPC backend as-is. No Redfish migration.**

Redfish does not add meaningful new data over JSON-RPC. The only field Redfish has
that JSON-RPC lacks is `PowerStateInTransition`, which is a minor improvement for
power cycle handling (would eliminate `time.sleep(3)`).

## What Redfish Can Do

- Full PDU hardware info (model, serial, firmware)
- Outlet power data (current, power, voltage, energy in kWh)
- Outlet power control: `POST .../Outlets/{N}/Actions/Outlet.PowerControl`
  - `{"PowerState": "On" | "Off" | "PowerCycle"}` → HTTP 200
- Inlet polyphase data (PolyPhaseCurrentAmps, PolyPhasePowerWatts, etc.)
- OCP/Branch state: `BreakerState: "Normal" | "Tripped"`
- Network interface info (MAC, IP, DHCP/Static)
- `PowerStateInTransition` flag on outlets (not available in JSON-RPC)

## What JSON-RPC Has That Redfish Does NOT

| Field | Notes |
|-------|-------|
| `energy_reset_at` | `getLastResetTime()` on energy sensor |
| `hw_revision` | `getMetaData().hwRevision` |
| `rated_voltage/current/frequency/power` | `getMetaData().nameplate.rating` |
| `dns_servers` | `/net getInfo()` |
| `ntp_servers` | `/datetime getActiveNtpServers()` |
| Link speed (NIC) | ethMap in `/net getInfo()` |
| Thresholds | `getThresholds()` per sensor |

## Key Endpoints

```
GET  /redfish/v1/PowerEquipment/RackPDUs/1
GET  /redfish/v1/PowerEquipment/RackPDUs/1/Outlets
GET  /redfish/v1/PowerEquipment/RackPDUs/1/Outlets/{N}
POST /redfish/v1/PowerEquipment/RackPDUs/1/Outlets/{N}/Actions/Outlet.PowerControl
GET  /redfish/v1/PowerEquipment/RackPDUs/1/Mains/I1
GET  /redfish/v1/PowerEquipment/RackPDUs/1/Branches/{C1|C2|C3}
GET  /redfish/v1/Managers/BMC/EthernetInterfaces/{ETH1|ETH2}
```
