import json

import aiohttp
from telegraph_commander.singleton import Singleton


class TelegramApiException(Exception):
    pass


class TelegramApi:
    """
    Class provide async call's to telegram api methods.
    """
    __metaclass__ = Singleton

    config = dict()
    API_BASE_URL = 'https://api.telegram.org'

    def __init__(self, event_loop, config):
        self.config = config
        self.session = aiohttp.ClientSession(loop=event_loop)

    def __del__(self):
        self.session.close()

    def make_bot_url(self, method):
        """
        Create full bot api url, by provided method name (ex. getUpdates or sendMessage)
        :param method: One of methods Telegram bot API (https://core.telegram.org/bots/api)
        :return finally URL
        """
        return '%s/bot%s/%s' % (self.API_BASE_URL, self.config.TELEGRAM_API_KEY, method)

    async def bot_request(self, method, params):
        """
        Send request to method of telegram bot API.
        :param method: One of methods Telegram bot API (https://core.telegram.org/bots/api)
        :param params: Dictionary of request parameters.
        :return (dict, int) - JSON response and HTTP status code
        """
        async with self.session.get(self.make_bot_url(method), params=params) as response:
            response_status = response.status
            if response_status != 200:
                raise TelegramApiException('error code from api: {}'.format(response_status))
            try:
                response_body = await response.json()
            except json.decoder.JSONDecodeError:
                raise TelegramApiException('not json response')

            if not response_body['ok']:
                raise TelegramApiException('({}){}'.format(response_body['error_code'], response_body['description']))

            return response_body['result']

    async def send_message(self, chat_id, text, variants=None):
        request_dict = dict(chat_id=chat_id, text=text)
        if variants:
            request_dict['reply_markup'] = json.dumps(dict(
                keyboard=variants,
                one_time_keyboard=True
            ))

        result = await self.bot_request('sendMessage', request_dict)
        return result
