import asyncio
import logging
from collections import deque

import deepl
import discord
from discord.ext import commands

from config import *

#############################

logging.SUCCESS = 25


def success(self, message, *args, **kwargs):
    if self.isEnabledFor(logging.SUCCESS):
        self._log(logging.SUCCESS, message, args, **kwargs)


logging.Logger.success = success


class LoggingFormatter(logging.Formatter):
    black = "\x1b[30m"
    red = "\x1b[31m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    blue = "\x1b[34m"
    gray = "\x1b[38m"
    reset = "\x1b[0m"
    bold = "\x1b[1m"

    LEVEL_NAMES = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.SUCCESS: "OK",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    COLORS = {
        logging.DEBUG: yellow + bold,
        logging.INFO: blue + bold,
        logging.SUCCESS: green + bold,
        logging.WARNING: red + bold,
        logging.ERROR: red,
        logging.CRITICAL: red + bold,
    }

    def format(self, record):
        level_name = self.LEVEL_NAMES.get(
            record.levelno, "LEVEL " + str(record.levelno)
        )
        log_color = self.COLORS.get(
            record.levelno, self.yellow + self.bold
        )  # Use yellow color by default for unknown log levels
        format = "(black){asctime}(reset) (levelcolor){levelname}(reset) {message}"
        format = format.replace("(black)", self.black + self.bold)
        format = format.replace("(reset)", self.reset)
        format = format.replace("(levelcolor)", log_color)
        format = format.replace("(green)", self.green + self.bold)
        formatter = logging.Formatter(format, "%H:%M:%S", style="{")
        record.levelname = level_name  # Replace the level name with the custom string
        return formatter.format(record)


logger = logging.getLogger("discord_bot")
logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setFormatter(LoggingFormatter())
file_handler = logging.FileHandler(
    filename=LOGFILE,
    encoding="utf-8",
)
file_handler_formatter = logging.Formatter("{message}", style="{")
file_handler.setFormatter(file_handler_formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)
#################################


class MessageQueue:
    def __init__(self):
        self.queue = deque()

    def add_message(self, message):
        self.queue.append(message)
        logger.info(f"Сообщение добавлено в очередь: {message.content}")

    def get_next_message(self):
        if self.queue:
            message = self.queue.popleft()
            logger.info(f"Сообщение взято из очереди: {message.content}")
            return message
        return None


ID_TRANSLATE = [DE_CHANNEL_ID, EN_CHANNEL_ID, PT_CHANNEL_ID, RU_CHANNEL_ID]
ID_CHATBOT = [AICHAT_ID]
""" CONFIG BOT """
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="/", intents=intents)
webhooks_cache = {}
""" CONFIG BOT """
translator = deepl.Translator(DEEPL_API)


RU_CODE = "RU"
EN_CODE = "EN-US"
DE_CODE = "DE"
PT_CODE = "PT-PT"
channel_mapping = {
    RU_CHANNEL_ID: [
        (PT_CODE, PT_CHANNEL_ID),
        (EN_CODE, EN_CHANNEL_ID),
        (DE_CODE, DE_CHANNEL_ID),
    ],
    PT_CHANNEL_ID: [
        (RU_CODE, RU_CHANNEL_ID),
        (EN_CODE, EN_CHANNEL_ID),
        (DE_CODE, DE_CHANNEL_ID),
    ],
    EN_CHANNEL_ID: [
        (RU_CODE, RU_CHANNEL_ID),
        (PT_CODE, PT_CHANNEL_ID),
        (DE_CODE, DE_CHANNEL_ID),
    ],
    DE_CHANNEL_ID: [
        (RU_CODE, RU_CHANNEL_ID),
        (PT_CODE, PT_CHANNEL_ID),
        (EN_CODE, EN_CHANNEL_ID),
    ],
}
message_queue = MessageQueue()


@bot.event
async def on_ready():
    for guild in bot.guilds:
        logger.info(
            f"Авторизован как [{bot.user}] на сервере [{guild.name}] с ID [{guild.id}]"
        )


@bot.event
async def on_message(message):
    logger.info(f"Получено сообщение: {message.content}")

    if message.author.bot:
        logger.info("Сообщение отправлено ботом, игнорируем.")
        return

    if message.channel.id in ID_TRANSLATE:
        message_queue.add_message(message)


async def process_translation(message, target_channel_id, lng):
    logger.info(f"Начало перевода сообщения: {message.content}")

    target_channel = discord.utils.get(message.guild.channels, id=target_channel_id)
    if not target_channel:
        logger.error("Не удалось найти целевой канал.")
        return

    webhook = await get_webhook(target_channel)
    if not webhook:
        logger.error("Не удалось получить вебхук для отправки сообщения.")
        return

    translated_message = await translate_message(message, lng)
    if translated_message is None:
        logger.error("Ошибка при переводе сообщения.")
        return

    files = [await attachment.to_file() for attachment in message.attachments]
    try:
        await webhook.send(
            content=translated_message,
            username=message.author.display_name,
            avatar_url=(
                message.author.avatar.url
                if message.author.avatar
                else message.author.default_avatar.url
            ),
            files=files,
        )
        logger.info("Сообщение успешно отправлено.")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")


async def translate_message(message, lng):
    logger.info(f"Начало перевода текста: {message.content}")

    content = message.content.strip() or "Отправка файла:"
    if message.reference and message.reference.resolved:
        original_message = message.reference.resolved
        content = f"{original_message.author.mention} {content}"

    try:
        translated_text = translator.translate_text(content, target_lang=lng).text
        logger.info("Текст успешно переведен.")
        return translated_text
    except deepl.exceptions.DeepLException as e:
        logger.error(f"Ошибка при переводе: {e}")
        return None


async def get_webhook(target_channel):
    logger.info(f"Получение вебхука для канала: {target_channel.name}")

    if target_channel.id in webhooks_cache:
        logger.info("Вебхук найден в кэше.")
        return webhooks_cache[target_channel.id]

    try:
        webhook = await target_channel.create_webhook(name="TR")
        webhooks_cache[target_channel.id] = webhook
        logger.info("Вебхук успешно создан.")
        return webhook
    except (discord.Forbidden, discord.HTTPException):
        logger.error(f"Не удалось создать вебхук для канала {target_channel.name}")
        return None


async def process_queue():
    logger.info("Начало обработки очереди сообщений.")

    while True:
        message = message_queue.get_next_message()
        if message:
            logger.info(f"Обработка сообщения: {message.content}")
            for lng, target_channel_id in channel_mapping[message.channel.id]:
                await process_translation(message, target_channel_id, lng)
        await asyncio.sleep(1)


async def main():
    try:
        await bot.start(TOKEN)
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")


if __name__ == "__main__":
    logger.info("Запуск бота...")
    asyncio.get_event_loop().create_task(process_queue())
    asyncio.get_event_loop().run_until_complete(main())
