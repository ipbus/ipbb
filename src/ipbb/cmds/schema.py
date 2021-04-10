project_schema = {
    'toolset': {'type': 'string', 'allowed': ['sim', 'vivado', 'vivado_hls'], 'required': True},
    'device_generation': {'type': 'string'},
    'device_name': {'type': 'string', 'required': True},
    'device_speed': {'type': 'string', 'required': True},
    'device_package': {'type': 'string', 'required': True},
    'boardname': {'type': 'string'},
    'top_entity': {'type': 'string'},
}