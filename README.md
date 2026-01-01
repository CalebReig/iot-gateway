# IoT Gateway (MQTT)

This project implements a local IoT gateway using:

- Mosquitto (MQTT broker)
- Python-based gateway services
- ESP32 devices (publish telemetry)

## Architecture

- ESP32 devices publish sensor data via MQTT
- Raspberry Pi runs the MQTT broker
- Python services subscribe to topics and process data

## Status

Work in progress (learning + implementation)

## Repo Structure

gateway/ # Python MQTT subscribers / logic
mosquitto/ # Broker config templates
scripts/ # Setup & helper scripts
docs/ # Architecture & notes
