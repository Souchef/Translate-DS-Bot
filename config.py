import json
import os

from dotenv import load_dotenv


def CONFIG():
    try:
        load_dotenv()
        file_path = os.getenv("CONFIG")
        with open(file_path, "r") as f:
            config_data = json.load(f)
        return config_data
    except FileNotFoundError:
        errors = "NO FILE"
        return errors
    except json.JSONDecodeError as e:
        errors = "Error decoding"
        return errors


config = CONFIG()
TOKEN = config.get("TOKEN")
DB_PATH = config.get("DB_PATH")
SCHEMA_PATH = config.get("SCHEMA_PATH")
CONTEXT = config.get("CONTEXT")
PROMPT = config.get("PROMPT")
MODEL = config.get("MODEL")
URL = config.get("URL")
API = config.get("API")
PREFIX = config.get("PREFIX")
SERVER_ID = config.get("SERVER_ID")
LOGFILE = config.get("LOGFILE")
DEEPL_API = config.get("DEEPL_API")
AICHAT_ID = int(config.get("AICHAT_ID"))
RU_CHANNEL_ID = int(config.get("RU_CHANNEL_ID"))
PT_CHANNEL_ID = int(config.get("PT_CHANNEL_ID"))
DE_CHANNEL_ID = int(config.get("DE_CHANNEL_ID"))
EN_CHANNEL_ID = int(config.get("EN_CHANNEL_ID"))
RU_CODE = "RU"
EN_CODE = "EN-US"
DE_CODE = "DE"
PT_CODE = "PT-PT"
invite_link = "NOLINK"

if __name__ == "__main__":
    pass
