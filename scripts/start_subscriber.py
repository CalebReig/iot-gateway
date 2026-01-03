from gateway.constants import ENABLE_DB
from gateway.subscriber import Subscriber


def main():
	Subscriber(enable_db_writes=ENABLE_DB).start()


if __name__ == "__main__":
	main()
