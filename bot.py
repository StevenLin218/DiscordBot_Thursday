import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from database import Database

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.db = Database("scores.db")

@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Sync error: {e}")

async def load_cogs():
    for cog in ["cogs.scores", "cogs.admin"]:
        await bot.load_extension(cog)
        print(f"✅ Loaded: {cog}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
