import configparser

def load_inventory(path):
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(path)

    inventory = {}
    for section in config.sections():
        inventory[section] = list(config[section].keys())
    return inventory
