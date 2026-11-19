import configparser

import discord
from discord.ext import commands

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

intents = discord.Intents.default()
intents.message_content = True  # 접두사 명령어를 읽으려면 필요합니다

client = commands.Bot(
    command_prefix=config['CLIENT']['PREFIX'],
    intents=intents,
    help_command=None,  # 기본 영어 도움말 대신 직접 만든 도움말을 씁니다
)
