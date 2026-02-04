import os
import asyncio
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from fastapi import FastAPI
from dotenv import load_dotenv

# ---------- ENV ----------

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")
GUILD_ID = int(os.getenv("GUILD_ID"))

if not DISCORD_TOKEN or not MAKE_WEBHOOK_URL or not GUILD_ID:
    raise RuntimeError("Missing required environment variables")

# ---------- DISCORD BOT ----------

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- FASTAPI ----------

app = FastAPI()

# ---------- SLASH COMMAND ----------

@bot.tree.command(name="script", description="Generate a script from an incident")
@app_commands.describe(incident="Describe the incident")
async def script(interaction: discord.Interaction, incident: str):
    await interaction.response.defer(thinking=True)

    payload = {
        "user": interaction.user.name,
        "user_id": interaction.user.id,
        "channel_id": interaction.channel_id,
        "incident": incident,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(MAKE_WEBHOOK_URL, json=payload) as resp:
                if resp.status != 200:
                    raise RuntimeError("Make webhook failed")

        await interaction.followup.send("🧠 Processing your script…")

    except Exception as e:
        await interaction.followup.send("❌ Failed to send request.")
        print("Webhook error:", e)

# ---------- BOT EVENTS ----------

@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    # Copy global commands → guild (instant visibility)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)

    print("Commands in guild:", [c.name for c in bot.tree.get_commands(guild=guild)])
    print("Bot is in guild:", bot.get_guild(GUILD_ID).name)
    print(f"🤖 Logged in as {bot.user}")

# ---------- MAKE → DISCORD CALLBACK ----------

@app.post("/deliver")
async def deliver_script(data: dict):
    channel_id = int(data.get("channel_id"))
    script = data.get("script")

    channel = bot.get_channel(channel_id)
    if channel and script:
        await channel.send(f"🎬 **Your Script**\n\n{script}")

    return {"status": "ok"}

# ---------- STARTUP ----------

@app.on_event("startup")
async def startup_event():
    print("🚀 FastAPI startup event fired")
    asyncio.create_task(bot.start(DISCORD_TOKEN))
