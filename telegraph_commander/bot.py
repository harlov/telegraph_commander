import asyncio
import json

from telegraph_commander.redis import get_redis_client
from telegraph_commander.telegram import TelegramApi
from telegraph_commander.command import InvalidCommandArgumentsException, InvalidCommandException
from telegraph_commander.logger import get_logger


class BotConfigurationException(Exception):
    pass


class BaseBot:
    config = None
    router = None
    logger = None
    telegram_api = None

    router_class = None
    config_class = None

    def __init__(self):
        self.event_loop = asyncio.get_event_loop()

        self.bind_configuration()

        self.listen_updates = True
        self.last_update_id = None

    def bind_configuration(self):
        if self.config_class is None:
            raise BotConfigurationException('config_class attr is not setted')

        self.config = self.config_class()

        if self.logger is None:
            self.logger = get_logger(self.config.LOGGER_NAME)

        if self.router_class is None:
            raise BotConfigurationException('router_class attr is not setted')

        self.router = self.router_class(self.logger, self.config, self.event_loop)
        self.telegram_api = TelegramApi(self.event_loop, self.config)

    async def a_init(self):
        self.redis_client = await get_redis_client(self.config)

    def run(self):
        try:
            self.logger.info('running bot...')
            self.event_loop.run_until_complete(self.async_start())
        except KeyboardInterrupt:
            self.listen_updates = False
            self.event_loop.close()
            self.logger.info('bot stopped')

    async def async_start(self):
        await self.a_init()
        await self.updates_loop()

    async def updates_loop(self):
        while self.listen_updates:
            await self.get_updates()

    async def get_updates(self):
        params = dict(timeout=self.config.TELEGRAM_LONG_POOLING_TIMEOUT)
        if self.last_update_id is not None:
            params['offset'] = self.last_update_id + 1
        response, status_code = await self.telegram_api.bot_request('getUpdates', params=params)
        if not response['ok']:
            return

        update_items = response['result']
        for item in update_items:
            await self.processes_update_item(item=item)

    async def processes_update_item(self, item):
        self.last_update_id = item['update_id']
        message_chat = item['message']['chat']
        self.logger.info("incoming message, from chat %s, text: %s" % (message_chat['id'],  item['message']['text']))
        if message_chat['type'] != 'private':
            self.logger.error('chat %s is not private, chat type: %s' % (message_chat['id'], message_chat['type'] ))
            return

        await self.route_command(item['message'])

    async def route_command(self, msg):
        """
        Check command in income msg. If not found, try restore state from redis.
        use default command (menu), if state not exist.
        :param msg:
        """
        chat_id = msg['chat']['id']

        command = self.extract_command(msg['text'])
        if command is None:
            command = await self.restore_state(msg['chat'], msg['text'])

        if command is None:
            if self.config.DEFAULT_COMMAND is None:
                self.logger.warn('default command is not set.')
                await self.telegram_api.send_message(chat_id, 'command not found.')
                return
            else:
                command = self.config.DEFAULT_COMMAND
        try:
            while command is not None:
                command = await self.router.resolve(command, chat_id)
        except InvalidCommandException as e:
            await self.telegram_api.send_message(chat_id, 'invalid command : %s.' % (e,))
        except InvalidCommandArgumentsException as e:
            await self.telegram_api.send_message(chat_id, 'invalid command parameters: %s.' % (e, ))

    def extract_command(self, inp):
        """
        Extract command and arguments from income message
        :param inp: income message
        :return: tuple(command, tuple(<args>)
        """

        if inp[0] != '/':
            return None

        command_inp = inp[1:].split()

        if len(command_inp) < 1:
            return None

        command_name = command_inp[0]
        command_args = command_inp[1:]
        self.logger.debug("command income: %s, args: %s" % (command_name, command_args))
        return dict(command=command_name, args_list=command_args)

    async def restore_state(self, chat, text):
        current_state = await self.redis_client.get(str(chat['id']))
        if current_state is None:
            return None

        state_dict = json.loads(current_state)
        state_dict['args_list'].append(text)
        return state_dict