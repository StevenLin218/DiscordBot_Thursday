import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import textwrap

MEDALS = ["🥇", "🥈", "🥉"]

SCORE_TYPE_LABEL = {
    "high":       "🔢 數字高勝",
    "low":        "🔢 數字低勝",
    "time_short": "⏱ 時間短勝",
    "time_long":  "⏱ 時間長勝",
}

SCORE_TYPE_UNIT = {
    "high":       "分",
    "low":        "分",
    "time_short": "秒",
    "time_long":  "秒",
}


def game_autocomplete(games):
    async def autocomplete(interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=g[2], value=g[1])
            for g in games
            if current.lower() in g[1].lower() or current.lower() in g[2].lower()
        ][:25]
    return autocomplete


class Scores(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def db(self):
        return self.bot.db

    def _get_games(self):
        return self.db().get_games()

    # ── /score add ───────────────────────────────────────────

    @app_commands.command(name="score", description="新增玩家分數")
    @app_commands.describe(
        game="遊戲項目",
        player="要記錄的玩家",
        points="分數（可為負數）",
        note="備註（可選）"
    )
    async def score(
        self,
        interaction: discord.Interaction,
        game: str,
        player: discord.Member,
        points: int,
        note: Optional[str] = None
    ):
        db = self.db()
        g = db.get_game(game)
        if not g:
            await interaction.response.send_message(
                f"❌ 找不到遊戲 `{game}`，用 `/games` 查看所有選項。", ephemeral=True
            )
            return

        game_id, _, display_name, score_type = g
        unit = SCORE_TYPE_UNIT.get(score_type, "分")
        guild_id = str(interaction.guild_id)
        db.add_score(
            guild_id, str(player.id), player.display_name,
            game_id, points, note,
            interaction.user.display_name
        )
        total = db.get_user_total(guild_id, str(player.id), game_id)
        season = db.get_season(guild_id, game_id)

        sign = "+" if points >= 0 else ""
        embed = discord.Embed(
            title=f"{display_name} 分數紀錄",
            color=discord.Color.green() if points >= 0 else discord.Color.red()
        )
        embed.add_field(name="玩家", value=player.mention, inline=True)
        embed.add_field(name="本次", value=f"`{sign}{points}{unit}`", inline=True)
        embed.add_field(name=f"賽季 S{season} 累計", value=f"`{total}{unit}`", inline=True)
        if note:
            embed.add_field(name="備註", value=note, inline=False)
        embed.set_footer(text=f"由 {interaction.user.display_name} 記錄 ｜ {SCORE_TYPE_LABEL.get(score_type, '')}")
        await interaction.response.send_message(embed=embed)

    @score.autocomplete("game")
    async def score_game_autocomplete(self, interaction, current):
        return await game_autocomplete(self._get_games())(interaction, current)

    # ── /rank ────────────────────────────────────────────────

    @app_commands.command(name="rank", description="查看排行榜")
    @app_commands.describe(game="遊戲項目")
    async def rank(self, interaction: discord.Interaction, game: str):
        db = self.db()
        g = db.get_game(game)
        if not g:
            await interaction.response.send_message(
                f"❌ 找不到遊戲 `{game}`，用 `/games` 查看所有選項。", ephemeral=True
            )
            return

        game_id, _, display_name, score_type = g
        unit = SCORE_TYPE_UNIT.get(score_type, "分")
        guild_id = str(interaction.guild_id)
        season = db.get_season(guild_id, game_id)
        rows = db.get_leaderboard(guild_id, game_id, score_type)

        embed = discord.Embed(
            title=f"{display_name} 排行榜 ─ Season {season}",
            color=discord.Color.gold()
        )
        embed.set_footer(text=SCORE_TYPE_LABEL.get(score_type, ""))

        if not rows:
            embed.description = "還沒有任何紀錄，快來挑戰！"
        else:
            lines = []
            for i, (name, total, rounds) in enumerate(rows):
                prefix = MEDALS[i] if i < 3 else f"`{i+1}.`"
                lines.append(f"{prefix} **{name}** ─ `{total}{unit}` ({rounds}局)")
            embed.description = "\n".join(lines)

        await interaction.response.send_message(embed=embed)

    @rank.autocomplete("game")
    async def rank_game_autocomplete(self, interaction, current):
        return await game_autocomplete(self._get_games())(interaction, current)

    # ── /history ─────────────────────────────────────────────

    @app_commands.command(name="history", description="查看玩家歷史紀錄")
    @app_commands.describe(game="遊戲項目", player="查詢的玩家（留空查自己）")
    async def history(
        self,
        interaction: discord.Interaction,
        game: str,
        player: Optional[discord.Member] = None
    ):
        db = self.db()
        g = db.get_game(game)
        if not g:
            await interaction.response.send_message(
                f"❌ 找不到遊戲 `{game}`，用 `/games` 查看所有選項。", ephemeral=True
            )
            return

        target = player or interaction.user
        game_id, _, display_name, score_type = g
        unit = SCORE_TYPE_UNIT.get(score_type, "分")
        guild_id = str(interaction.guild_id)
        season = db.get_season(guild_id, game_id)
        rows = db.get_history(guild_id, str(target.id), game_id)
        total = db.get_user_total(guild_id, str(target.id), game_id)

        embed = discord.Embed(
            title=f"{display_name} ─ {target.display_name} 的紀錄 (S{season})",
            color=discord.Color.blurple()
        )
        embed.add_field(name="賽季累計", value=f"`{total}{unit}`", inline=False)
        embed.set_footer(text=SCORE_TYPE_LABEL.get(score_type, ""))

        if not rows:
            embed.description = "這個賽季還沒有紀錄。"
        else:
            lines = []
            for pts, note, by, ts in rows:
                sign = "+" if pts >= 0 else ""
                note_str = f" ─ {note}" if note else ""
                date = ts[:10]
                lines.append(f"`{sign}{pts}{unit}`{note_str} *({date} by {by})*")
            embed.description = "\n".join(lines)

        await interaction.response.send_message(embed=embed)

    @history.autocomplete("game")
    async def history_game_autocomplete(self, interaction, current):
        return await game_autocomplete(self._get_games())(interaction, current)

    # ── /games ───────────────────────────────────────────────

    @app_commands.command(name="games", description="查看所有遊戲項目")
    async def games(self, interaction: discord.Interaction):
        rows = self._get_games()
        embed = discord.Embed(title="🎮 支援的遊戲", color=discord.Color.purple())
        embed.description = "\n".join(
            f"• **{display}** ─ `{name}`  {SCORE_TYPE_LABEL.get(stype, '')}"
            for _, name, display, stype in rows
        )
        embed.set_footer(text="管理員可用 /addgame 新增遊戲")
        await interaction.response.send_message(embed=embed)

    # ── /undo ────────────────────────────────────────────────

    @app_commands.command(name="undo", description="刪除玩家最後一筆分數紀錄")
    @app_commands.describe(game="遊戲項目", player="要撤銷的玩家")
    async def undo(
        self,
        interaction: discord.Interaction,
        game: str,
        player: discord.Member
    ):
        db = self.db()
        g = db.get_game(game)
        if not g:
            await interaction.response.send_message(f"❌ 找不到遊戲 `{game}`", ephemeral=True)
            return

        game_id, _, display_name = g
        success = db.delete_last_score(
            str(interaction.guild_id), str(player.id), game_id
        )
        if success:
            await interaction.response.send_message(
                f"↩️ 已刪除 **{player.display_name}** 在 {display_name} 的最後一筆紀錄。"
            )
        else:
            await interaction.response.send_message(
                f"❌ 找不到 **{player.display_name}** 的紀錄。", ephemeral=True
            )

    @undo.autocomplete("game")
    async def undo_game_autocomplete(self, interaction, current):
        return await game_autocomplete(self._get_games())(interaction, current)


async def setup(bot):
    await bot.add_cog(Scores(bot))
