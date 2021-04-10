project_schema = {
    'toolset': {'type': 'string', 'allowed': ['ModelSim', 'Vivado', 'VivadoHLS'], 'required': True},
    'device_generation': {'type': 'string'},
    'device_name': {'type': 'string', 'required': True},
    'device_speed': {'type': 'string', 'required': True},
    'device_package': {'type': 'string', 'required': True},
    'boardname': {'type': 'string'},
    'top_entity': {'type': 'string'},
}