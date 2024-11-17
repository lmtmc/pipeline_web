import yaml
from pathlib import Path


def load_config(config_path=None):
    if config_path is None:
        # Assuming the config file is in the project root directory
        config_path = Path(__file__).parent / 'config.yaml'

    config_path = Path(config_path).resolve()

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML configuration file: {e}")
    except Exception as e:
        raise IOError(f"Error reading configuration file: {e}")


# Usage
try:
    config = load_config()
    # Use the config...
except (FileNotFoundError, ValueError, IOError) as e:
    print(f"Error loading configuration: {e}")