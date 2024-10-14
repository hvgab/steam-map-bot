import discord
from discord.ext import commands
import os

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

COGS_FOLDER = "./cogs"
# load all cog.py files in the cogs/* folders.
for foldername in os.listdir(COGS_FOLDER):
    if not os.path.isdir(os.path.join(COGS_FOLDER, foldername)):
        continue
    for filename in os.listdir(os.path.join(COGS_FOLDER, foldername)):
        if filename.endswith("cog.py"):
            # and not filename in [
            #     "util.py",
            #     "error.py",
            # ]:
            # if the file is a python file and if the file is a cog
            print(f"{foldername}.{filename[:-3]} Loading...")
            bot.load_extension(f"cogs.{foldername}.{filename[:-3]}")
            print(f"{foldername}.{filename[:-3]} Loaded.")


bot.run(os.getenv("DISCORD_TOKEN"))
