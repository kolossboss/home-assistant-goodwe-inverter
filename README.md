[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

# GoodWe solar inverter sensors for Home Assistant

The GoodWe Inverter Solar Sensor component will retrieve data from a GoodWe inverter connected to local network.  
It has been tested on GoodWe ET, ES and EM families of inverters.  
It may work for other inverters as well, as long as they listen on UDP port 8899 and respond to one of supported communication protocols.

The values will be presented as sensors in [Home Assistant](https://home-assistant.io/).

## Requirements

Your inverter needs to be connected to your local network, as this custom component will utilise the UDP protocol to read data from inverter. All you need to know is the IP address of the inverter and you are good to go.

## HACS installation

Add this component using HACS by searching for `GoodWe Inverter Solar Sensor (UDP - no cloud)` on the `Integrations` page.

## Manual installation

Create a directory called `goodwe` in the `<config directory>/custom_components/` directory on your Home Assistant instance.
Install this component by copying all files in `/custom_components/goodwe/` folder from this repo into the new `<config directory>/custom_components/goodwe/` directory you just created.

This is how your custom_components directory should look like:

```bash
custom_components
├── goodwe
│   ├── __init__.py
│   ├── goodwe_inverter.py
│   ├── manifest.json
│   └── sensor.py
```

## Configuration example

To enable this sensor, add the following lines to your `configuration.yaml` file:

```YAML
sensor:
  - platform: goodwe
    ip_address: 192.168.100.100
    #scan_interval: 30
    #sensor_name_prefix: GoodWe
```

The optional `sensor_name_prefix` config may be used to change the prefix of the individual sensor's default entity names.

## Inverter communication testing

To test whether the inverter properly responds to UDP request, just execute the `inverter_test.py` script

## References and inspiration

- https://github.com/home-assistant/core/tree/dev/homeassistant/components/solax
- https://github.com/robbinjanssen/home-assistant-omnik-inverter
