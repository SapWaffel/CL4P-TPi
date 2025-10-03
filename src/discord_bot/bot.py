# src/discord_bot/bot.py
import time
import logging
import os
from xml.sax import handler

import discord
from discord.ext import commands
import asyncio

from src.config_manager import ConfigManager
from src.discord_bot.logs.rl_log import RelevanceLogger, LogType
from src.discord_bot.util.get_random_quote import get_random_quote
from src.discord_bot.util.is_admin_on_guild import is_admin_on_guild

from util.custom_help_command import CustomHelpCommand

# CONFIG
config = ConfigManager.get_config('discord_bot')
TOKEN = config["token"]
PREFIX = config["prefix"]
MAINTENANCE = config["maintenance"]

# RELEVANCE LOGGING
RelevanceLogger.create_log_file()
RelevanceLogger.write_log_entry("Bot is starting...", "SYSTEM")

# DISCORD NATIVE LOGGING
current_time = time.strftime("%Y-%m-%d_%H-%M-%S")
discord_log_file_name = f"discord_{current_time}"
discord_log_handler = logging.FileHandler(filename=f'config/logs/discord_log/{discord_log_file_name}.log', encoding='utf-8', mode='w')
# remove old log files
max_log_files = config["max_log_files"]
log_files = sorted([f for f in os.listdir('config/logs/discord_log') if f.startswith('discord_') and f.endswith('.log')])
if len(log_files) > max_log_files:
    for old_file in log_files[:-max_log_files]:
        os.remove(os.path.join('config/logs/discord_log', old_file))
        RelevanceLogger.write_log_entry("CL4P-TP Bot", f"Removed old log file: {old_file}")

# BOT INTENTS
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# BOT SETUP
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=CustomHelpCommand())

@bot.event
async def on_ready():
    logging.basicConfig(level=logging.INFO, handlers=[discord_log_handler])
    logging.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    RelevanceLogger.write_log_entry(f"Bot is ready as {bot.user.name} (ID: {bot.user.id})", "SYSTEM")

    # presenece
    if MAINTENANCE:
        RelevanceLogger.write_log_entry("Bot is in maintenance mode", "SYSTEM", type=LogType.WARNING)
        await bot.change_presence(activity=None, status=discord.Status.do_not_disturb)
        await bot.application.edit(description="Currently in maintenance mode.")
    else:
        await bot.change_presence(activity=discord.Game(name="Borderlands 3"), status=discord.Status.online)
        await bot.application.edit(description=get_random_quote())
        RelevanceLogger.write_log_entry("Bot is online and operational", "SYSTEM")
    
@bot.event
async def on_message(message):
    # ignore bot messages
    if message.author.bot:
        return
    # wrong channel
    cmd_channel_name = config["commands_channel_name"]
    if isinstance(message.channel, discord.TextChannel) and message.channel.name != cmd_channel_name:
        await message.delete()
        await message.channel.send(f"{message.author.mention} {ConfigManager.get_config("strings")['error']['wrong_channel'].replace('{channel}', cmd_channel_name)}", delete_after=10)
        return
   # maintenance mode
    if MAINTENANCE:
        await message.channel.send(f"{ConfigManager.get_config('strings')['error']['maintenance']}")
        RelevanceLogger.write_log_entry(f"{message.author}", "attempt to use bot refused (maintenance)", type=LogType.WARNING)
        return
    # process commands
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    # unknown command
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"{ConfigManager.get_config('strings')['error']['unknown_command']}").replace('{prefix}', PREFIX)
        RelevanceLogger.write_log_entry(f"{ctx.author}", f"cmd.{ctx.command} failed (unknown command)", type=LogType.INFO)
        return
    # only in pms
    elif isinstance(error, commands.PrivateMessageOnly):
        RelevanceLogger.write_log_entry(f"{ctx.author}", f"cmd.{ctx.command} failed (private message only)", type=LogType.INFO)
        if is_admin_on_guild(bot, ctx.author.id):
            await ctx.send(f"{ConfigManager.get_config('strings')['error']['private_message_only']}")
        else:
            await ctx.send(f"{ConfigManager.get_config('strings')['error']['no_permission']}")
        return
    # no permission
    elif isinstance(error, commands.MissingPermissions):
        RelevanceLogger.write_log_entry(f"{ctx.author}", f"cmd.{ctx.command} failed (no permission)", type=LogType.INFO)
        await ctx.send(f"{ConfigManager.get_config('strings')['error']['no_permission']}")
        return
    # other errors
    else:
        RelevanceLogger.write_log_entry(f"{ctx.author}", f"cmd.{ctx.command} failed (unknown error: {str(error)})", type=LogType.ERROR)
        raise error
    
# LOAD COGS
async def load_cogs():
    #/src/discord_bot/cogs or deeper directory levels
    for root, dirs, files in os.walk('./src/discord_bot/cogs'):
        for filename in files:
            if filename.endswith('.py'):
                try:
                    await bot.load_extension(f'src.discord_bot.cogs.{filename[:-3]}')
                    RelevanceLogger.write_log_entry(f"Loaded cog: {filename}", "SYSTEM")
                except Exception as e:
                    RelevanceLogger.write_log_entry(f"Failed to load cog: {filename} ({str(e)})", "SYSTEM", type=LogType.ERROR)

if __name__ == '__main__':
    asyncio.run(load_cogs())
    bot.run(TOKEN, log_handler=discord_log_handler, log_level=logging.DEBUG)