
from api.registry import get_global_registry

# Import schema files from newly registered apps
# Sorted from core apps to more dependent apps, NOT ALPHABETICALLY


schema = get_global_registry().get_schema()
