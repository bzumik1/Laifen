# Laifen for Home Assistant (development build)

This repository is a development build of the `laifen` integration that is being prepared for
Home Assistant core. It lets the integration be installed and tested as a custom integration
before it is merged.

It supports the **Laifen Wave** (`LFTB01-P`) electric toothbrush over Bluetooth, using the
[laifen-ble](https://github.com/bzumik1/laifen-ble) library.

## Entities

- **Battery**, **Last brushing** and **Last brushing duration** sensors, kept while the
  toothbrush is asleep
- **Mode** select: Mode 1, Mode 2, Mode 3, or High frequency when it is turned on
- **Strength**, **Range** and **Speed** of the active mode, and **Brushing time**
- **Brushing**, **High frequency** and **30-second reminder** switches
- **Airplane mode** binary sensor, disabled by default

The controls are only available while the toothbrush is awake.

## Installation

1. Add `https://github.com/bzumik1/Laifen` to the Marketplace as a custom repository of type
   **Integration** and download it.
2. Restart Home Assistant.
3. Press the button of the toothbrush to wake it up. Home Assistant discovers it and offers to
   set it up.

## Credits

The protocol is documented by
[marc-alexis-com/laifen-toolbox](https://github.com/marc-alexis-com/laifen-toolbox) and was
first explored by [UrbanTechIO/Laifen](https://github.com/UrbanTechIO/Laifen), from which this
repository is forked.
