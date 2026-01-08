import configparser

def load_inventory(path):
    """
    Carga inventario de servidores desde un archivo ini.
    Retorna un diccionario con grupos y lista de hosts.
    """
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(path)

    inventory = {}
    for section in config.sections():
        inventory[section] = list(config[section].keys())

    return inventory
