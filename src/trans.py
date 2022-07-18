"""Translation commands."""
import googletrans
import toml
from discord import app_commands
from discord.ext import commands

config = toml.load("config.toml")
trans = googletrans.Translator()


class TransCog(
    commands.Cog,
    name=config["trans"]["name"],
    description=config["trans"]["desc"],
):
    """Translation commands."""

    def __init__(self, bot: commands.AutoShardedBot):
        """Initialize the cog."""
        self.bot = bot

    @commands.hybrid_command(
        name=config["trans"]["trans"]["name"],
        enabled=config["trans"]["trans"]["enbl"],
        hidden=config["trans"]["trans"]["hide"],
        help=config["trans"]["trans"]["desc"],
    )
    @app_commands.guilds(*config["trans"]["glds"])
    @app_commands.describe(
        dest=config["trans"]["trans"]["dest"],
        src=config["trans"]["trans"]["src"],
        text=config["trans"]["trans"]["text"],
    )
    async def trans(
        self, ctx: commands.Context, dest: str, src: str = "auto", *, text: str
    ):
        """Translates text."""
        res = trans.translate(text, dest, src)
        await ctx.send(
            "{}:\n> {}\n{}:\n> {}".format(
                googletrans.LANGUAGES[res.src],
                res.origin,
                googletrans.LANGUAGES[res.dest],
                res.text,
            )
        )

    @commands.hybrid_command(
        name=config["trans"]["lang"]["name"],
        enabled=config["trans"]["lang"]["enbl"],
        hidden=config["trans"]["lang"]["hide"],
        help=config["trans"]["lang"]["desc"],
    )
    @app_commands.guilds(*config["trans"]["glds"])
    @app_commands.describe(text=config["trans"]["lang"]["text"])
    async def lang(self, ctx: commands.Context, *, text: str):
        """Detects language of text."""
        res = trans.detect(text)
        await ctx.send(
            "{}:\n> {}".format(googletrans.LANGUAGES[res.lang], text)
        )

    @commands.hybrid_command(
        name=config["trans"]["code"]["name"],
        enabled=config["trans"]["code"]["enbl"],
        hidden=config["trans"]["code"]["hide"],
        help=config["trans"]["code"]["desc"],
    )
    @app_commands.guilds(*config["trans"]["glds"])
    async def code(self, ctx):
        """Lists language codes."""
        await ctx.send(
            "Available language codes:\n{}".format(
                ", ".join(
                    [
                        "{} - {}".format(key, value)
                        for (key, value) in googletrans.LANGUAGES.items()
                    ]
                )
            )
        )


async def setup(bot):
    """Sets up the extension."""
    await bot.add_cog(TransCog(bot))
