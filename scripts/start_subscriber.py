import os

from gateway.constants import ENABLE_DB
from gateway.subscriber import Subscriber
from gateway.utils.database import InfluxDataBase


def main():
	Subscriber(
		db=InfluxDataBase(
			url=os.environ["INFLUX_URL"],
			org=os.environ["INFLUX_ORG"],
			token=os.environ["INFLUX_TOKEN"],
			bucket=os.environ["INFLUX_BUCKET"]
		),
		enable_db_writes=ENABLE_DB
		mqqt_host=os.environ["MQTT_HOST"]
	).start()


if __name__ == "__main__":
	main()
