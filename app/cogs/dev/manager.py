import discord
from discord.ext import commands

from app import config
from app.ui import AdminPanelView, embed_color, is_admin_manager
from app.vending_machine import VendingMachine


def is_manager():
    """MANAGER_ID에 설정된 사용자만 통과합니다."""
    async def predicate(ctx):
        if ctx.author.id != int(config['CLIENT']['MANAGER_ID']):
            raise commands.CheckFailure('관리자 전용 명령어입니다.')
        return True
    return commands.check(predicate)


class Manager(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name='관리패널', aliases=['admin_panel'])
    @commands.has_permissions(administrator=True)
    @is_manager()
    async def admin_panel(self, ctx) -> None:
        """관리자 버튼 패널을 올립니다."""
        embed = discord.Embed(
            title='🛠️ 관리자 패널',
            description='➕ 쿠폰 등록 · 🪙 크레딧 지급',
            color=embed_color(),
        )
        await ctx.send(embed=embed, view=AdminPanelView())

    @commands.command(name='쿠폰등록', aliases=['insert_coupon'])
    @is_manager()
    @commands.has_permissions(administrator=True)
    async def insert_coupon(self, ctx, description: str, code: str, cost: int) -> None:
        """사용법: ;쿠폰등록 "설명" 코드 가격"""
        if cost <= 0:
            await ctx.send('가격은 1 이상이어야 합니다.')
            return
        await ctx.send(VendingMachine().add_coupon(description, code, cost))

    @commands.command(name='지급', aliases=['reward'])
    @is_manager()
    @commands.has_permissions(administrator=True)
    async def reward(self, ctx, member: discord.Member, value: int) -> None:
        """사용법: ;지급 @멤버 금액"""
        if value <= 0:
            await ctx.send('지급 금액은 1 이상이어야 합니다.')
            return
        status, message = VendingMachine().give_credit(str(member.id), value)
        if status == 'ok':
            await ctx.send(f'{member.display_name}님에게 {value} 크레딧을 지급했습니다.')
        else:
            await ctx.send(message)


async def setup(client):
    # 재시작 후에도 관리자 패널 버튼이 동작하도록 등록
    client.add_view(AdminPanelView())
    await client.add_cog(Manager(client))
