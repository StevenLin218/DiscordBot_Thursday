import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional


def is_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def db(self):
        return self.bot.db

    def _get_games(self):
        return self.db().get_games()

    # ── /season reset ────────────────────────────────────────

    @app_commands.command(name="season", description="[管理員] 重置賽季（清空當季排行）")
    @app_commands.describe(game="要重置的遊戲")
    @is_admin()
    async def season(self, interaction: discord.Interaction, game: str):
        db = self.db()
        g = db.get_game(game)
        if not g:
            await interaction.response.send_message(f"❌ 找不到遊戲 `{game}`", ephemeral=True)
            return

        game_id, _, display_name = g
        guild_id = str(interaction.guild_id)
        new_season = db.next_season(guild_id, game_id)

        embed = discord.Embed(
            title="🏁 新賽季開始！",
            description=f"{display_name} 進入 **Season {new_season}**\n舊賽季數據已封存，重新出發！",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)

    @season.autocomplete("game")
    async def season_game_autocomplete(self, interaction, current):
        games = self._get_games()
        return [
            app_commands.Choice(name=g[2], value=g[1])
            for g in games
            if current.lower() in g[1].lower() or current.lower() in g[2].lower()
        ][:25]

    @season.error
    async def season_error(self, interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("❌ 只有管理員可以重置賽季。", ephemeral=True)

    # ── /addgame ─────────────────────────────────────────────

    @app_commands.command(name="addgame", description="[管理員] 新增遊戲項目")
    @app_commands.describe(
        name="遊戲代號（英文小寫）",
        display_name="顯示名稱（可含 emoji）",
        score_type="勝負判定方式"
    )
    @app_commands.choices(score_type=[
        app_commands.Choice(name="🔢 數字高勝", value="high"),
        app_commands.Choice(name="🔢 數字低勝", value="low"),
        app_commands.Choice(name="⏱ 時間短勝", value="time_short"),
        app_commands.Choice(name="⏱ 時間長勝", value="time_long"),
    ])
    @is_admin()
    async def addgame(
        self,
        interaction: discord.Interaction,
        name: str,
        display_name: str,
        score_type: str = "high"
    ):
        db = self.db()
        if db.get_game(name):
            await interaction.response.send_message(
                f"❌ 遊戲 `{name}` 已存在。", ephemeral=True
            )
            return
        db.add_game(name.lower(), display_name, score_type)
        label = {"high": "數字高勝", "low": "數字低勝", "time_short": "時間短勝", "time_long": "時間長勝"}.get(score_type, "")
        await interaction.response.send_message(
            f"✅ 已新增遊戲：**{display_name}** (`{name}`) ─ {label}"
        )

    @addgame.error
    async def addgame_error(self, interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("❌ 只有管理員可以新增遊戲。", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Admin(bot))
