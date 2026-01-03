import time

from sense_hat import SenseHat

from gateway.constants import GATEWAY_NAME, PUBLISH_INTERVAL_SEC
from gateway.publisher import Publisher
from gateway.utils import TemperatureSensor, HumiditySensor, PressureSensor, CPUSensor


def main():
	sense_hat = SenseHat()
	publisher = Publisher(
		device_name=GATEWAY_NAME,
		device_source="pi",
		sensors=[
			TemperatureSensor(sense_hat=sense_hat),
			HumiditySensor(sense_hat=sense_hat),
			PressureSensor(sense_hat=sense_hat),
			CPUSensor(sense_hat=sense_hat),
		]
	)
	
	while True:
		publisher.publish_sensor_data()
		time.sleep(PUBLISH_INTERVAL_SEC)


if __name__ == "__main__":
	main()
