import os
import discord
import aiohttp
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = MyClient()

@client.tree.command(name="script", description="Generate a script from an incident")
@app_commands.describe(incident="Describe the incident in detail")
async def script(interaction: discord.Interaction, incident: str):

    # Acknowledge immediately (important for UX)
    await interaction.response.defer(thinking=True)

    payload = {
        "user": interaction.user.name,
        "user_id": interaction.user.id,
        "incident": incident
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(MAKE_WEBHOOK_URL, json=payload) as resp:
                if resp.status != 200:
                    raise Exception("Make webhook failed")

        await interaction.followup.send(
            "🧠 Processing your script. I’ll post it here shortly."
        )

    except Exception as e:
        await interaction.followup.send(
            "❌ Something went wrong while sending data for processing."
        )
        print(e)

client.run(TOKEN)

from fastapi import FastAPI
import uvicorn
import threading

app = FastAPI()

@app.post("/deliver")
async def deliver_script(data: dict):
    channel_id = int(data["channel_id"])
    script = data["script"]

    channel = client.get_channel(channel_id)
    if channel:
        await channel.send(f"🎬 **Your Script**\n\n{script}")

    return {"status": "ok"}

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

threading.Thread(target=run_api).start()
