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
import secrets
import typing

import discord
from discord.ext import commands


class Bot(commands.AutoShardedBot):
    """The bot client.

    Attributes:
        cfg: Configuration of the bot.
        glds: Guilds the bot belongs to.
    """

    def __init__(
        self, *args, config, guilds: typing.List[discord.Object], **kwargs
    ):
        """Initialize the bot with a configuration.

        Args:
            args: Positional arguments.
            config: Configuration of the bot.
            guilds: Guilds the bot belongs to.
            kwargs: Keyword arguments.
        """
        self.cfg = config
        self.glds = guilds
        super().__init__(*args, **kwargs)

    async def setup_hook(self):
        """Set up the bot."""
        self.add_command(load)
        self.add_command(sync)
        for cog in self.cfg["feynmanium"]["base"]["exts"]:
            await self.load_extension(cog)
        print(secrets.choice(self.cfg["feynmanium"]["base"]["rdy"]))


@commands.command()
async def load(ctx: commands.Context[Bot], ext: str):
    """Loads extensions.

    Args:
        ctx: Context of the command.
        ext: Extension to load.
    """
    await ctx.bot.load_extension(ext)
    await ctx.send(f"Extension {ext} loaded!")


@commands.command()
async def sync(ctx: commands.Context[Bot], gld: typing.Optional[discord.Guild]):
    """Syncs commands.

    Args:
        ctx: Context of the command.
        gld: Guild to sync commands.
    """
    if gld is None:
        await ctx.bot.tree.sync()
    else:
        await ctx.bot.tree.sync(guild=gld)
    await ctx.send(f"Synced commands for {gld}!")
