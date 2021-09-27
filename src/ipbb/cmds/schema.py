import cerberus
from ..console import cprint, console

project_schema = {
    'toolset': {'type': 'string', 'allowed': ['sim', 'vivado', 'vitis_hls'], 'required': True},
    'device_generation': {'type': 'string'},
    'device_name': {'type': 'string', 'required': True},
    'device_speed': {'type': 'string', 'required': True},
    'device_package': {'type': 'string', 'required': True},
    'boardname': {'type': 'string'},
    'top_entity': {'type': 'string'},
}

def validate(schema, settings, toolset):

    lValidator = cerberus.Validator(schema, allow_unknown=True)
    if not lValidator.validate(settings.dict()):
        cprint(f"ERROR: Project settings validation failed", style='red')
        cprint(f"   Detected errors: {lValidator.errors}", style='red')
        cprint(f"   Settings: {settings.dict()}", style='red')
        raise RuntimeError(f"Project settings validation failed: {lValidator.errors}")
