import discord
from discord.ext import commands

from app import config
from app.ui import PanelView, embed_color
from app.vending_machine import VendingMachine


class Trade(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name='패널', aliases=['panel'])
    @commands.has_permissions(administrator=True)
    async def panel(self, ctx) -> None:
        """버튼 패널을 채널에 올립니다. (관리자 전용)"""
        embed = discord.Embed(
            title='🎮 자판기',
            description='아래 버튼을 눌러 이용하세요.\n🛒 상점 · 💰 잔액 · 🎟️ 구매 · 📖 도움말',
            color=embed_color(),
        )
        await ctx.send(embed=embed, view=PanelView())

    @commands.command(name='도움말', aliases=['help'])
    async def help_cmd(self, ctx) -> None:
        p = ctx.prefix
        embed = discord.Embed(title='📖 명령어 목록', color=embed_color())
        embed.add_field(name=f'{p}패널', value='버튼 패널 올리기 (관리자)', inline=False)
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
            color=embed_color(),
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
            color=embed_color(),
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
    # 재시작 후에도 이미 올라간 패널 버튼이 동작하도록 등록
    client.add_view(PanelView())
    await client.add_cog(Trade(client))
