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
import math
import secrets

import discord
from discord.ext import commands, tasks

from .. import base


class MiscCog(commands.Cog, name="Miscellaneous"):
    """Miscellaneous commands.

    Attributes:
        bot: Bot that contains the cog.
    """

    def __init__(self, bot: base.Bot):
        """Initializes the cog.

        Args:
            bot: Bot that contains the cog.
        """
        self.bot = bot
        self.stat.start()  # pylint: disable=no-member

    def cog_unload(self):  # pylint: disable=invalid-overridden-method
        """Stops status change."""
        self.stat.cancel()  # pylint: disable=no-member

    @tasks.loop(seconds=10)
    async def stat(self):
        """Changes the status of the bot."""
        await self.bot.change_presence(
            activity=discord.Game(
                secrets.choice(
                    self.bot.cfg["feynmanium"]["cogs"]["misc"]["stat"]
                )
            )
        )

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context[base.Bot], err: commands.CommandError, /
    ):
        """Alerts the user for an error.

        Args:
            ctx: Context of the command.
            err: Error of the command.
        """
        msg = secrets.choice(self.bot.cfg["feynmanium"]["cogs"]["misc"]["err"])
        await ctx.send(f"{msg}```{err}```", ephemeral=True)

    @commands.hybrid_command()
    async def roll(
        self,
        ctx: commands.Context[base.Bot],
        siz: commands.Range[int, 2, 1000],
        cnt: commands.Range[int, 1, 400] = 1,
    ):
        """Rolls dice."""
        result = [secrets.randbelow(siz) + 1 for _ in range(cnt)]
        total = sum(result)
        res_str = ", ".join([str(_) for _ in result])
        await ctx.send(
            f"You rolled {cnt}d{siz} and get a {total}!```{res_str}```",
            ephemeral=True,
        )

    @commands.hybrid_command(name="8ball")
    async def eight_ball(
        self, ctx: commands.Context[base.Bot], *, qry: str = "Is it?"
    ):
        """Asks the magic 8-ball."""
        result = secrets.choice(
            self.bot.cfg["feynmanium"]["cogs"]["misc"]["ball"]
        )
        await ctx.send(f"> {qry}\n{result}", ephemeral=True)

    @commands.hybrid_command()
    async def ping(self, ctx: commands.Context[base.Bot]):
        """Tests the latency."""
        result = math.ceil(self.bot.latency * 1000)
        await ctx.send(f"Pong! The ping took {result} ms.", ephemeral=True)


async def setup(bot: base.Bot):
    """Set up the extension.

    Args:
        bot: Bot that loads the extension.
    """
    await bot.add_cog(MiscCog(bot), guilds=list(bot.glds))


async def teardown(bot: base.Bot):
    """Tear down the extension.

    Args:
        bot: Bot that unloads the extension.
    """
    await bot.remove_cog("Miscellaneous", guilds=list(bot.glds))
