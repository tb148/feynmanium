"""This file is part of Feynmanium.

Feynmanium is free software: you can redistribute it and/or modify it under the
terms of the GNU Affero General Public License as published by the Free Software
Foundation, either version 3 of theLicense, or (at your option) any later
version.

Feynmanium is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along
with Feynmanium. If not, see <https://www.gnu.org/licenses/>.
"""
import argparse
import asyncio
import logging
import pathlib

import discord
import uvloop
from discord.ext import commands
from tomlkit import toml_file

from . import base


def main():
    """Execute the bot."""
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
        "-q",
        "--quiet",
        action="count",
        default=0,
        help="decrease output verbosity",
    )
    parser.add_argument("token", help="the token of the bot")
    args = parser.parse_args()
    (conf_file, log_file, quiet, token) = (
        args.conf_file,
        args.log_file,
        args.quiet,
        args.token,
    )
    handler = logging.FileHandler(filename=log_file, encoding="utf-8", mode="w")
    config = toml_file.TOMLFile(conf_file).read()

    guilds = [
        discord.Object(guild) for guild in config["feynmanium"]["main"]["glds"]
    ]
    bot = base.Bot(
        commands.when_mentioned,
        config=config,
        guilds=guilds,
        help_command=commands.DefaultHelpCommand(dm_help=None),
        case_insensitive=True,
        description=config["feynmanium"]["main"]["desc"],
        owner_ids=config["feynmanium"]["main"]["ownr"],
        intents=discord.Intents.default(),
    )
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    bot.run(token, log_handler=handler, log_level=(1 + quiet) * logging.DEBUG)
