import discord
from discord import ui

from app import config
from app.vending_machine import VendingMachine


def embed_color() -> discord.Color:
    return discord.Color(int(config['EMBED']['COLOR']))


def is_manager(user: discord.abc.User) -> bool:
    return user.id == int(config['CLIENT']['MANAGER_ID'])


def is_admin_manager(user) -> bool:
    perms = getattr(user, 'guild_permissions', None)
    return is_manager(user) and perms is not None and perms.administrator


# ============================================================
# 사용자 패널
# ============================================================
class BuySelect(ui.Select):
    def __init__(self, coupons: list):
        options = [
            discord.SelectOption(label=f'[{cid}] {desc}'[:100], description=f'{cost} 크레딧'[:100], value=str(cid))
            for cid, desc, cost in coupons[:25]
        ]
        super().__init__(placeholder='구매할 쿠폰을 고르세요', options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        result = VendingMachine().buy_coupon(str(interaction.user.id), int(self.values[0]))
        if result[0] != 'ok':
            await interaction.response.send_message(result[1], ephemeral=True)
            return

        await interaction.response.send_message(result[1], ephemeral=True)
        try:
            await interaction.user.send(f'🎟️ 쿠폰 코드: `{result[2]}`')
        except discord.Forbidden:
            await interaction.followup.send(
                'DM을 받을 수 없어 쿠폰 코드를 보내지 못했습니다. 관리자에게 문의해 주세요.', ephemeral=True)


class BuyView(ui.View):
    def __init__(self, coupons: list):
        super().__init__(timeout=180)
        self.add_item(BuySelect(coupons))


class PanelView(ui.View):
    """채널에 올려 두는 사용자 패널. 재시작 후에도 동작하도록 timeout=None과 custom_id를 씁니다."""

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label='상점', emoji='🛒', style=discord.ButtonStyle.primary, custom_id='vm:shop')
    async def shop(self, interaction: discord.Interaction, button: ui.Button):
        coupons = VendingMachine().view_showcase()
        if not coupons:
            await interaction.response.send_message('현재 판매 중인 쿠폰이 없습니다.', ephemeral=True)
            return
        embed = discord.Embed(title='🛒 쿠폰 상점', description='구매 가능한 쿠폰 목록', color=embed_color())
        for cid, desc, cost in coupons:
            embed.add_field(name=f'[{cid}] {desc}', value=f'{cost} 크레딧', inline=False)
        await interaction.response.send_message(embed=embed, view=BuyView(coupons), ephemeral=True)

    @ui.button(label='잔액', emoji='💰', style=discord.ButtonStyle.success, custom_id='vm:balance')
    async def balance(self, interaction: discord.Interaction, button: ui.Button):
        bal = VendingMachine().user_balance(str(interaction.user.id))
        await interaction.response.send_message(f'💰 내 잔액: **{bal} 크레딧**', ephemeral=True)

    @ui.button(label='구매', emoji='🎟️', style=discord.ButtonStyle.primary, custom_id='vm:buy')
    async def buy(self, interaction: discord.Interaction, button: ui.Button):
        coupons = VendingMachine().view_showcase()
        if not coupons:
            await interaction.response.send_message('현재 판매 중인 쿠폰이 없습니다.', ephemeral=True)
            return
        await interaction.response.send_message('구매할 쿠폰을 골라 주세요.', view=BuyView(coupons), ephemeral=True)

    @ui.button(label='도움말', emoji='📖', style=discord.ButtonStyle.secondary, custom_id='vm:help')
    async def show_help(self, interaction: discord.Interaction, button: ui.Button):
        embed = discord.Embed(title='📖 사용법', color=embed_color())
        embed.add_field(name='🛒 상점', value='판매 중인 쿠폰 보기', inline=False)
        embed.add_field(name='💰 잔액', value='내 크레딧 확인', inline=False)
        embed.add_field(name='🎟️ 구매', value='쿠폰을 골라 구매 (코드는 DM으로 전송)', inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ============================================================
# 관리자 패널
# ============================================================
class CouponModal(ui.Modal, title='쿠폰 등록'):
    description = ui.TextInput(label='설명', max_length=100)
    code = ui.TextInput(label='쿠폰 코드', max_length=200)
    cost = ui.TextInput(label='가격 (숫자)', max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            cost = int(str(self.cost.value).strip())
        except ValueError:
            await interaction.response.send_message('가격은 숫자로 입력해 주세요.', ephemeral=True)
            return
        if cost <= 0:
            await interaction.response.send_message('가격은 1 이상이어야 합니다.', ephemeral=True)
            return
        message = VendingMachine().add_coupon(str(self.description.value), str(self.code.value), cost)
        await interaction.response.send_message(message, ephemeral=True)


class RewardModal(ui.Modal, title='크레딧 지급'):
    user_id = ui.TextInput(label='멤버 사용자 ID', max_length=25)
    amount = ui.TextInput(label='지급 금액', max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            uid = int(str(self.user_id.value).strip())
            value = int(str(self.amount.value).strip())
        except ValueError:
            await interaction.response.send_message('사용자 ID와 금액은 숫자로 입력해 주세요.', ephemeral=True)
            return
        if value <= 0:
            await interaction.response.send_message('지급 금액은 1 이상이어야 합니다.', ephemeral=True)
            return
        status, message = VendingMachine().give_credit(str(uid), value)
        if status == 'ok':
            await interaction.response.send_message(f'<@{uid}>님에게 {value} 크레딧을 지급했습니다.', ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


class AdminPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _deny_if_not_admin(self, interaction: discord.Interaction) -> bool:
        if is_admin_manager(interaction.user):
            return False
        await interaction.response.send_message('관리자 전용 기능입니다.', ephemeral=True)
        return True

    @ui.button(label='쿠폰 등록', emoji='➕', style=discord.ButtonStyle.primary, custom_id='vm:admin_coupon')
    async def coupon(self, interaction: discord.Interaction, button: ui.Button):
        if await self._deny_if_not_admin(interaction):
            return
        await interaction.response.send_modal(CouponModal())

    @ui.button(label='크레딧 지급', emoji='🪙', style=discord.ButtonStyle.success, custom_id='vm:admin_reward')
    async def reward(self, interaction: discord.Interaction, button: ui.Button):
        if await self._deny_if_not_admin(interaction):
            return
        await interaction.response.send_modal(RewardModal())
