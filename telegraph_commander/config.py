class BotConfig(dict):
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    TELEGRAM_LONG_POOLING_TIMEOUT = 60
    TELEGRAM_API_KEY = None
    LOGGER_NAME = 'telebot'
    DEFAULT_COMMAND = None
