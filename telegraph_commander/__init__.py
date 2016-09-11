from inspect import getfullargspec


class InvalidCommandException(Exception):
    pass


class InvalidCommandArgumentsException(Exception):
    pass


class CommandRouter:
    def __init__(self):
        self._commands_map = dict()

    def command(self, name):
        def decorator(cls):
            orig_init = cls.__init__

            def wrap_init(obj, *args, **kwargs):
                obj._command_name = name
                orig_init(obj, *args, **kwargs)

            cls.__init__ = wrap_init
            self._commands_map[name] = cls
            return cls
        return decorator

    async def resolve(self, command, chat_id):
        if type(command) == str:
            command = (command, list())

        if command[0] not in self._commands_map:
            #log.error('command %s not found' % (command[0],))
            raise InvalidCommandException(command[0])

        call_class = self._commands_map[command[0]]
        command_instance = call_class(chat_id=chat_id)

        args_list = getfullargspec(command_instance.run)
        if len(command[1]) > len(args_list.args) -1:
            raise InvalidCommandArgumentsException('max args count : %s' % (len(args_list.args)-1))

        await command_instance.a_init()
        await command_instance.run(*command[1])