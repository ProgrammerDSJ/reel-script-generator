import os
import discord
import aiohttp
import asyncio
from fastapi import FastAPI
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")
GUILD_ID=os.getenv("GUILD_ID")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

app = FastAPI()

# ---------- DISCORD BOT ----------

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")

@tree.command(name="script", description="Generate a script from an incident")
@app_commands.describe(incident="Describe the incident")
async def script(interaction: discord.Interaction, incident: str):
    await interaction.response.defer(thinking=True)

    payload = {
        "user": interaction.user.name,
        "user_id": interaction.user.id,
        "channel_id": interaction.channel_id,
        "incident": incident
    }

    async with aiohttp.ClientSession() as session:
        await session.post(MAKE_WEBHOOK_URL, json=payload)

    await interaction.followup.send("🧠 Processing your script…")

# ---------- FASTAPI ENDPOINT ----------

@app.post("/deliver")
async def deliver_script(data: dict):
    channel = client.get_channel(int(data["channel_id"]))
    if channel:
        await channel.send(f"🎬 **Your Script**\n\n{data['script']}")
    return {"status": "ok"}

# ---------- STARTUP ----------

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(client.start(DISCORD_TOKEN))
    
@client.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    tree.copy_global_to(guild=guild)
    await tree.sync(guild=guild)
    print(f"Commands synced to guild {GUILD_ID}")
    print(f"Logged in as {client.user}")