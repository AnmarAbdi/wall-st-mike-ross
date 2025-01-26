import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json

load_dotenv()

TOKEN = os.getenv("TOKEN")
SERVER_ID = os.getenv("SERVER_ID")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

class Client(commands.Bot):
    async def on_ready(self):
        print(f"Logged in as {self.user}")

        try:
            guild = discord.Object(id=SERVER_ID)
            synced = await self.tree.sync(guild=guild)
            print(f'Synced {len(synced)} commands in guild {guild.id}')
        except Exception as e:
            print(f"Failed to sync commands: {e}")


intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix="!", intents=intents)

GUILD_ID = discord.Object(id=SERVER_ID)

async def send_to_n8n(ticker: str):
    """Helper function to send ticker to n8n workflow"""
    payload = {
        "ticker": ticker.upper(),
        "source": "discord-bot",
        "timestamp": discord.utils.utcnow().isoformat()
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            N8N_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            return await response.json()

@client.tree.command(name="run", description="Type a company's ticker to run earnings analysis.", guild=GUILD_ID)
async def run(interaction: discord.Interaction, ticker: str):
    await interaction.response.send_message(f"Starting analysis for {ticker.upper()}...")


    try:
        n8n_response = await send_to_n8n(ticker)
        
        
        if n8n_response.get("success"):
            analysis_url = n8n_response.get("report_url", "#")
            await interaction.followup.send(
                f"✅ Analysis complete for {ticker.upper()}!\n"
                f"View report: {analysis_url}"
            )
        else:
            await interaction.followup.send(
                f"❌ Could not analyze {ticker.upper()}. "
                f"Error: {n8n_response.get('error', 'Unknown error')}"
            )
            
    except aiohttp.ClientError as e:
        await interaction.followup.send(
            f"🔴 Connection failed to analysis service. Please try again later.\n"
            f"Technical details: {str(e)}"
        )
    except Exception as e:
        await interaction.followup.send(
            f"⚠️ Unexpected error occurred processing {ticker.upper()}.\n"
            f"Error: {str(e)}"
        )

client.run(TOKEN)