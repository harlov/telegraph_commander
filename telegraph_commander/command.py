import json

from telegraph_commander.redis import get_redis_client
from telegraph_commander.telegram import TelegramApi




class BotCommand:
    PARAMS = None
    context = None

    """
    Base class for all bot's commands.
    Command is a logic for response to certain user message.
    """

    config = None
    event_loop = None
    logger = None
    router = None

    def __init__(self, chat_id, config, event_loop, logger, name):
        self.chat_id = chat_id
        self.config = config
        self.event_loop = event_loop
        self.logger = logger
        self.name = name

        self.telegram_api = TelegramApi(self.event_loop, self.config)

    async def a_init(self):
        """
        Async init. Income command arguments.
        Must be redefined in child.
        """
        self.redis_client = await get_redis_client(self.config)

    async def save_args_to_list(self):
        self.args_list = list()

        for arg in self.PARAMS:
            if not hasattr(self, arg.get('name')) or getattr(self, arg.get('name')) is None:
                return
            self.args_list.append(getattr(self, arg.get('name')))

    async def run(self, *args, **kwargs):
        self.args_list = list()

        input_args = list(args)
        input_params_list = list(self.PARAMS)
        self.logger.debug('input args: {}'.format(input_args))
        for input_arg in input_args:
            orig_param = input_params_list.pop(0)
            self.logger.debug('set {} = {}'.format(orig_param['name'], input_arg))
            setattr(self, orig_param['name'], input_arg)

        if len(input_params_list):
            last_unsetted_param = input_params_list[0]
            if last_unsetted_param.get('dynamic') is not True:
                await self.telegram_api.send_message(self.chat_id, 'Please enter {}'.format(
                    last_unsetted_param.get('label') or last_unsetted_param.get('name')
                ))
                await self.set_state('provide_{}'.format(last_unsetted_param.get('name')))
                return
        self.logger.debug('all params provided, run handle')
        try:
            return await self.run_handle()
        except Exception as e:
            self.logger.error('command {} exception: {}'.format(self.name, e))

    async def run_handle(self):
        raise NotImplemented

    async def set_state(self, stage):
        await self.save_args_to_list()

        state_dict = dict(
            command=self._command_name,
            stage=stage,
            context=self.context,
            args_list=self.args_list
        )
        await self.redis_client.set(str(self.chat_id), json.dumps(state_dict))

    async def end_command(self):
        await self.redis_client.delete([str(self.chat_id), ])


class InvalidCommandException(Exception):
    pass


class InvalidCommandArgumentsException(Exception):
    pass


class CommandRouter:
    logger = None
    config = None
    event_loop = None

    def __init__(self, logger, config, event_loop):
        self.logger = logger
        self.config = config
        self.event_loop = event_loop

        self._commands_map = dict()

    def command(self, name):
        def decorator(cls):
            orig_init = cls.__init__

            def wrap_init(obj, *args, **kwargs):
                obj._command_name = name
                kwargs.update(dict(
                    config=self.config,
                    event_loop=self.event_loop,
                    logger=self.logger,
                    name=name
                ))
                orig_init(obj, *args, **kwargs)

            cls.__init__ = wrap_init
            cls.config = self.config
            cls.event_loop = self.event_loop
            cls.logger = self.logger
            self._commands_map[name] = cls
            return cls
        return decorator

    async def resolve(self, command, chat_id):
        if type(command) == str:
            command = dict(command=command)

        if command.get('command') not in self._commands_map:
            self.logger.error('command %s not found' % (command.get('command'),))
            raise InvalidCommandException(command.get('command'))

        call_class = self._commands_map[command.get('command')]
        command_instance = call_class(chat_id=chat_id, )
        if command.get('context') is not None:
            command_instance.context = command.get('context')
        else:
            command_instance.context = dict()

        if call_class.PARAMS is not None and len(command.get('args_list', [])) > len(call_class.PARAMS):
            raise InvalidCommandArgumentsException('max args count exception')

        await command_instance.a_init()
        return await command_instance.run(*command.get('args_list', list()))
