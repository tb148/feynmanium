"""The main file of the bot."""
import argparse
import asyncio
import logging
import math
import pathlib
import secrets

import discord
import toml
import uvloop
from discord import app_commands
from discord.ext import commands, tasks  # type: ignore[attr-defined]

parser = argparse.ArgumentParser()
parser.add_argument(
    "-c",
    "--conf-file",
    default="config.toml",
    type=pathlib.Path,
    help="the file to read configuration",
)
parser.add_argument(
    "-l",
    "--log-file",
    default="fy.log",
    type=pathlib.Path,
    help="the file to record logging events",
)
parser.add_argument(
    "-q", "--quiet", action="count", default=0, help="decrease output verbosity"
)
parser.add_argument(
    "-s",
    "--stockfish",
    default="stockfish/stockfish_14_x64",
    type=pathlib.Path,
    help="the path to find stockfish",
)
parser.add_argument("token", help="the token of the bot")
args = parser.parse_args()
(conf_file, log_file, quiet, sf_path, token) = (
    args.conf_file,
    args.log_file,
    args.quiet,
    args.stockfish,
    args.token,
)
handler = logging.FileHandler(filename=log_file, encoding="utf-8", mode="w")
config = toml.load(conf_file)


class Bot(commands.AutoShardedBot):
    """The class of the bot."""

    async def on_command_error(self, ctx: commands.Context, err, /):
        """Send an error message."""
        await super().on_command_error(ctx, err)
        err_msg = secrets.choice(config["bot"]["err-msgs"])
        err_type = err.__class__.__name__
        await ctx.send(f"{err_msg}\n```{err_type}: {err}```")

    async def setup_hook(self):
        """Set up the bot."""
        for ext in config["bot"]["bot-exts"]:
            await self.load_extension(f"feynmanium.cogs.{ext}")
        for guild in config["bot"]["bot-glds"]:
            await self.tree.sync(guild=discord.Object(guild))
        status.start()
        print(secrets.choice(config["bot"]["rdy-msgs"]))


bot = Bot(
    commands.when_mentioned,
    help_command=commands.MinimalHelpCommand(
        dm_help=None, dm_help_threshold=config["bot"]["help-len"]
    ),
    case_insensitive=config["bot"]["case-insv"],
    description=config["bot"]["bot-desc"],
    owner_ids=config["bot"]["ownr-ids"],
    intents=discord.Intents.default(),
)


@tasks.loop(seconds=config["bot"]["stat-freq"])
async def status():
    """Change the status of the bot."""
    await bot.change_presence(
        activity=discord.Game(secrets.choice(config["bot"]["stat-msgs"]))
    )


@bot.hybrid_command(
    name=config["bot"]["roll"]["name"],
    enabled=config["bot"]["roll"]["enbl"],
    hidden=config["bot"]["roll"]["hide"],
    help=config["bot"]["roll"]["desc"],
)
@app_commands.guilds(*config["bot"]["bot-glds"])
@app_commands.describe(
    siz=config["bot"]["roll"]["siz"], cnt=config["bot"]["roll"]["cnt"]
)
async def roll(
    ctx: commands.Context,
    siz: commands.Range[int, 2, 1000],
    cnt: commands.Range[int, 1, 400] = 1,
):
    """Roll dice."""
    result = [secrets.randbelow(_) + 1 for _ in range(cnt)]
    total = sum(result)
    res_str = ", ".join([str(_) for _ in result])
    await ctx.send(
        f"You rolled {cnt}d{siz} and get a {total}!\n```\n{res_str}\n```"
    )


@bot.hybrid_command(
    name=config["bot"]["8ball"]["name"],
    enabled=config["bot"]["8ball"]["enbl"],
    hidden=config["bot"]["8ball"]["hide"],
    help=config["bot"]["8ball"]["desc"],
)
@app_commands.guilds(*config["bot"]["bot-glds"])
@app_commands.describe(qry=config["bot"]["8ball"]["qry"])
async def eight_ball(ctx: commands.Context, *, qry: str = "Is it?"):
    """Asks the magic 8-ball."""
    result = secrets.choice(config["bot"]["8ball"]["msgs"])
    await ctx.send(f"> {qry}\n{result}")


@bot.hybrid_command(
    name=config["bot"]["ping"]["name"],
    enabled=config["bot"]["ping"]["enbl"],
    hidden=config["bot"]["ping"]["hide"],
    help=config["bot"]["ping"]["desc"],
)
@app_commands.guilds(*config["bot"]["bot-glds"])
async def ping(ctx: commands.Context):
    """Test the latency."""
    result = math.ceil(bot.latency * 1000)
    await ctx.send(f"Pong! The ping took {result} ms.")


def setup():
    """Start the bot."""
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    bot.run(token, log_handler=handler, log_level=(1 + quiet) * logging.DEBUG)
