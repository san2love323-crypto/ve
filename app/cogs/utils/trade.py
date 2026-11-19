import discord
from discord.ext import commands

from app import config
from app.vending_machine import VendingMachine


def _color() -> discord.Color:
    return discord.Color(int(config['EMBED']['COLOR']))


class Trade(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name='도움말', aliases=['help'])
    async def help_cmd(self, ctx) -> None:
        p = ctx.prefix
        embed = discord.Embed(title='📖 명령어 목록', color=_color())
        embed.add_field(name=f'{p}상점', value='판매 중인 쿠폰 보기', inline=False)
        embed.add_field(name=f'{p}잔액 [@멤버]', value='내 잔액 또는 멤버의 잔액 보기', inline=False)
        embed.add_field(name=f'{p}구매 <쿠폰ID>', value='쿠폰 구매 (코드는 DM으로 전송)', inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='상점', aliases=['shop'])
    async def shop(self, ctx) -> None:
        coupons = VendingMachine().view_showcase()
        embed = discord.Embed(
            title='🛒 쿠폰 상점',
            description='구매 가능한 쿠폰 목록' if coupons else '현재 판매 중인 쿠폰이 없습니다.',
            color=_color(),
        )
        for coupon_id, description, cost in coupons:
            embed.add_field(name=f'[{coupon_id}] {description}', value=f'{cost} 크레딧', inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='잔액', aliases=['coin'])
    async def coin(self, ctx, member: discord.Member = None) -> None:
        target = member or ctx.author
        balance = VendingMachine().user_balance(str(target.id))
        embed = discord.Embed(
            title=f'💰 {target.display_name}님의 잔액',
            description=f'{balance} 크레딧',
            color=_color(),
        )
        await ctx.send(embed=embed)

    @commands.command(name='구매', aliases=['claim'])
    async def claim(self, ctx, coupon_id: int) -> None:
        result = VendingMachine().buy_coupon(str(ctx.author.id), coupon_id)

        if result[0] != 'ok':
            await ctx.send(result[1])
            return

        await ctx.send(result[1])
        try:
            await ctx.author.send(f'🎟️ 쿠폰 코드: `{result[2]}`')
        except discord.Forbidden:
            await ctx.send('DM을 받을 수 없어 쿠폰 코드를 보내지 못했습니다. 관리자에게 문의해 주세요.')


async def setup(client):
    await client.add_cog(Trade(client))
