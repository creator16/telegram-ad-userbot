from pyrogram import Client

from ..config import API_HASH, API_ID, DATA_DIR, SESSION_NAME


app = Client(
    name=SESSION_NAME,
    api_id=API_ID,
    api_hash=API_HASH,
    workdir=str(DATA_DIR),
)