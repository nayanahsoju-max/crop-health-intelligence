"""Run config/class checks and full image/mask validation on local datasets."""

from scripts.dataset_inventory import main as inventory_main
from scripts.validate_dataset_config import main as config_main


def main() -> None:
    config_main()
    inventory_main()


if __name__ == "__main__":
    main()
