import cerberus
from ..console import cprint, console
from ..utils import error_notice

project_schema = {
    'toolset': {'type': 'string', 'allowed': ['sim', 'vivado', 'vitis_hls'], 'required': True},
    'device_generation': {'type': 'string'},
    'device_name': {'type': 'string', 'required': True},
    'device_speed': {'type': 'string', 'required': True},
    'device_package': {'type': 'string', 'required': True},
    'board_name': {'type': 'string'},
    'top_entity': {'type': 'string'},
    'package_to_lib_mapping': {'type': 'dict'},
}

#------------------------------------------------------------------------------
def validate_schema(schema, settings):

    lValidator = cerberus.Validator(schema, allow_unknown=True)
    if not lValidator.validate(settings.dict()):
        error_notice(f"""Project settings validation failed
               Detected errors: {lValidator.errors}
               Settings: {settings.dict()}
               """)

        raise RuntimeError(f"Project settings validation failed: {lValidator.errors}")
