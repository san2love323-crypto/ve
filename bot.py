import asyncio
from pathlib import Path

import discord
from discord.ext import commands

from app import client, config


@client.event
async def on_ready():
    await client.change_presence(
        status=discord.Status(config['CLIENT']['STATUS']),
        activity=discord.Game(config['CLIENT']['ACTIVITY']),
    )
    print('봇이 준비되었습니다!')


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('관리자 권한이 필요합니다.')
    elif isinstance(error, commands.CheckFailure):
        await ctx.send('이 명령어를 사용할 권한이 없습니다.')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'필수 입력값이 빠졌습니다: `{error.param.name}`  (도움말: `{ctx.prefix}도움말`)')
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f'입력값 형식이 올바르지 않습니다. (도움말: `{ctx.prefix}도움말`)')
    else:
        print(f'명령어 오류: {error}')


async def load_extensions(cogs: str) -> None:
    for extension in Path(cogs).rglob('*.py'):
        extension = '.'.join(extension.parts)[:-3]
        try:
            await client.load_extension(extension)
            print(f'{extension} 로드 완료')
        except Exception as e:
            print(f'{extension} 로드 실패: {e}')


async def main():
    async with client:
        await load_extensions(config['DEFAULT']['COG_DIR'])
        await client.start(config['CLIENT']['TOKEN'])


if __name__ == '__main__':
    asyncio.run(main())
