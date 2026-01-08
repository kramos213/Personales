import os

modules_path = "modules"  # Ajusta esta ruta si es necesario

for item in os.listdir(modules_path):
    full_path = os.path.join(modules_path, item)
    if os.path.isdir(full_path):
        init_file = os.path.join(full_path, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                pass  # crea archivo vacío
            print(f"Creado: {init_file}")
        else:
            print(f"Ya existe: {init_file}")
