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
import googletrans
from discord.ext import commands

from .. import base


class TransCog(commands.Cog, name="Translation"):
    """Translation commands.

    Attributes:
        bot: Bot that contains the cog.
        api: Translator of the cog.
    """

    def __init__(self, bot: commands.AutoShardedBot):
        """Initialize the cog with a bot.

        Args:
            bot: Bot that contains the cog.
        """
        self.bot = bot
        self.api = googletrans.Translator()

    @commands.hybrid_command()
    async def trans(
        self,
        ctx: commands.Context[base.Bot],
        dest: str,
        src: str = "auto",
        *,
        text: str,
    ):
        """Translates text.

        Args:
            ctx: Context of the command.
            dest: Language to translate to.
            src: Language to translate from.
            text: Text to translate
        """
        result = self.api.translate(text, dest, src)
        res_src = googletrans.LANGUAGES[result.src.lower()].title()
        res_origin = result.origin
        res_dest = googletrans.LANGUAGES[result.dest.lower()].title()
        res_text = result.text
        await ctx.send(
            f"{res_src}:\n> {res_origin}\n{res_dest}:\n> {res_text}",
            ephemeral=True,
        )

    @commands.hybrid_command()
    async def lang(self, ctx: commands.Context[base.Bot], *, text: str):
        """Detect language of text.

        Args:
            ctx: Context of the command.
            text: Text to detect its language.
        """
        result = self.api.detect(text)
        res_lang = googletrans.LANGUAGES[result.lang.lower()].title()
        await ctx.send(f"{res_lang}:\n> {text}", ephemeral=True)

    @commands.hybrid_command()
    async def code(self, ctx):
        """List language codes."""
        result = ", ".join(
            [
                f"{key} - {value}"
                for (key, value) in googletrans.LANGUAGES.items()
            ]
        )

        await ctx.send(f"Available language codes:\n{result}", ephemeral=True)


async def setup(bot: base.Bot):
    """Set up the extension.

    Args:
        bot: Bot that loads the extension.
    """
    await bot.add_cog(TransCog(bot), guilds=list(bot.glds))


async def teardown(bot: base.Bot):
    """Tear down the extension.

    Args:
        bot: Bot that unloads the extension.
    """
    await bot.remove_cog("Translation", guilds=list(bot.glds))
