from hydrogram import Client

from ..compatibility import (
    apply_compatibility_patch,
)
from ..config import (
    API_HASH,
    API_ID,
    DATA_DIR,
    SESSION_NAME,
)


# Patch must run BEFORE the Client is constructed.
apply_compatibility_patch()


app = Client(
    name=SESSION_NAME,
    api_id=API_ID,
    api_hash=API_HASH,
    workdir=str(DATA_DIR),
    hide_password=True,
)