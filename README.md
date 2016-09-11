# telegraph_commander
Telegram simple bot framework

## 1. First, extend BaseBot class, and provide router and configuration:
```python
from telegraph_commander.logger import get_console_handler
from telegraph_commander.bot import BaseBot
from telegraph_commander.command import CommandRouter, BotCommand
from telegraph_commander.config import BotConfig



class YourBotConfig(BotConfig):
    TELEGRAM_API_KEY = '<api_key>'
    DEFAULT_COMMAND = 'menu'


class YourBot(BaseBot):
    router_class = CommandRouter
    config_class = YourBotConfig

bot = YourBot()

```

## 2. Bind commands to router :
```python
@bot.router.command('menu')
class MenuCommand(BotCommand):
    async def run(self):
        await self.telegram_api.send_message(self.chat_id, 'Select action', variants=[['/mul']])


@bot.router.command('mul')
class MulCommand(BotCommand):
    PARAMS = (
        dict(name='operand_1', title='first argument'),
        dict(name='operand_2', title='second argument')
    )
    async def run_handle(self):
        result = float(self.operand_1) * float(self.operand_2)
        await self.telegram_api.send_message(self.chat_id, 'result: {}'.format(result))
```

## 3. Add console logger handler(optional), and run your bot:
```python
bot.logger.addHandler(get_console_handler())
bot.run()
```