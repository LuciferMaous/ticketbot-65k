import discord
from discord import app_commands
from discord.ext import commands
import os

TOKEN = os.getenv("token")
GUILD_ID = 1340187883587244037  # ID máy chủ Discord
CATEGORY_ID = 1340199059331485757  # ID danh mục chứa các ticket
ADMIN_ROLE_ID = 1340289086174400613  # Thay bằng ID role admin

intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

tree = bot.tree  # Sử dụng bot.tree thay vì tạo CommandTree mới

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Mua Hàng", description="Liên hệ để mua hàng", emoji="🛒", value="mua-hang"),
            discord.SelectOption(label="Hỗ Trợ", description="Nhận hỗ trợ kỹ thuật", emoji="🛠️", value="ho-tro"),
            discord.SelectOption(label="Bảo Hành", description="Yêu cầu bảo hành sản phẩm", emoji="🔑", value="bao-hanh")
        ]
        super().__init__(placeholder="Chọn loại ticket...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await self.view.create_ticket(interaction, self.values[0])

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str):
        guild = bot.get_guild(GUILD_ID)
        category = guild.get_channel(CATEGORY_ID)
        ticket_name = f"{ticket_type}-{interaction.user.name}"
        
        existing_channel = discord.utils.get(guild.channels, name=ticket_name)
        if existing_channel:
            await interaction.response.send_message(f"Bạn đã có một ticket mở: {existing_channel.mention}", ephemeral=True)
            return
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        ticket_channel = await guild.create_text_channel(ticket_name, category=category, overwrites=overwrites)
        embed = discord.Embed(title="🎟️ Ticket Mới", color=discord.Color.green())
        embed.add_field(name="Người tạo:", value=interaction.user.mention, inline=True)
        embed.add_field(name="Loại Ticket:", value=ticket_type, inline=True)
        embed.set_footer(text=f"ID: {interaction.user.id}")
        
        view = TicketActionView()
        admin_role = discord.utils.get(guild.roles, id=ADMIN_ROLE_ID)
        await ticket_channel.send(f"|| {admin_role.mention} {interaction.user.mention} ||", embed=embed, view=view)
        await interaction.response.send_message(f"Ticket của bạn đã được tạo: {ticket_channel.mention}", ephemeral=True)

class CloseReasonModal(discord.ui.Modal, title="Lý do đóng ticket"):
    reason = discord.ui.TextInput(label="Nhập lý do", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Ticket đã bị đóng với lý do: {self.reason.value}", ephemeral=False)
        await interaction.channel.delete()

class TicketActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketButton("🔒 Close", "close", discord.ButtonStyle.danger))
        self.add_item(TicketButton("✅ Claim", "claim", discord.ButtonStyle.success))

class TicketButton(discord.ui.Button):
    def __init__(self, label, action, style):
        super().__init__(label=label, style=style)
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        admin_role = discord.utils.get(guild.roles, id=ADMIN_ROLE_ID)
        
        if self.action == "close":
            if admin_role in interaction.user.roles:
                await interaction.channel.delete()
            else:
                await interaction.response.send_message("Chỉ admin mới có thể đóng ticket này!", ephemeral=True)
        elif self.action == "claim":
            await interaction.response.send_message(f"{interaction.user.mention} đã nhận xử lý ticket này!", ephemeral=False)

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Bot {bot.user} đã sẵn sàng!")

@tree.command(name="ticket", description="Mở ticket hỗ trợ", guild=discord.Object(id=GUILD_ID))
async def ticket(interaction: discord.Interaction):
    embed = discord.Embed(title="🎀 TICKET 🎀", description="## ✨ CÁC LOẠI TICKET MÀ BẠN CÓ THỂ CHỌN ✨ \n ### 🛒 MUA HÀNG \n ### 🦸‍♂️ HỖ TRỢ \n ### 🔑 BẢO HÀNH", color=discord.Color.blue())
    view = TicketView()
    await interaction.response.send_message(embed=embed, view=view)

bot.run(TOKEN)