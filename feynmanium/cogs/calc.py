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
import sympy
from discord.ext import commands

from .. import base


def parse_raw(expr: str):
    """Parses an expression.

    Args:
        expr: Expression to parse.

    Returns:
        The parsed expression.
    """
    return sympy.S(expr.strip("`").replace("\\", ""), evaluate=False)


def pretty_eq(lhs, rhs) -> str:
    """Prettifies an equality.

    Args:
        lhs: Left hand side.
        rhs: Right hand side.

    Returns:
        The prettified equality.
    """
    result = sympy.pretty(sympy.Eq(lhs, rhs, evaluate=False), use_unicode=False)
    return f"```{result}```"


class CalcCog(commands.Cog, name="Mathematics"):
    """Mathematical commands.

    Attributes:
        bot: The bot that contains the cog.
    """

    def __init__(self, bot: base.Bot):
        """Initializes the cog.

        Args:
            bot: The bot that contains the cog.
        """
        self.bot = bot

    @commands.hybrid_group(fallback="simpl")
    async def simpl(self, ctx: commands.Context[base.Bot], *, expr: str):
        """Simplifies expressions.

        Args:
            ctx: Context of the command.
            expr: Expression to simplify.
        """
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(raw_expr, sympy.simplify(raw_expr, ratio=sympy.oo)),
            ephemeral=True,
        )

    @simpl.command()
    async def expn(self, ctx: commands.Context[base.Bot], *, expr: str):
        """Expands expressions.

        Args:
            ctx: Context of the command.
            expr: Expression to expand.
        """
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(raw_expr, sympy.expand(raw_expr)), ephemeral=True
        )

    @simpl.command()
    async def fact(self, ctx: commands.Context[base.Bot], *, expr: str):
        """Factors expressions.

        Args:
            ctx: Context of the command.
            expr: Expression to factor.
        """
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(raw_expr, sympy.factor(raw_expr)), ephemeral=True
        )

    @simpl.command()
    async def apart(self, ctx: commands.Context[base.Bot], *, expr: str):
        """Decomposes partial fractions.

        Args:
            ctx: Context of the command.
            expr: Expression to decompose.
        """
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(raw_expr, sympy.apart(raw_expr)), ephemeral=True
        )

    @commands.hybrid_group()
    async def calc(self, ctx: commands.Context[base.Bot], cmd: str):
        """Calculus commands.

        Args:
            ctx: Context of the command.
            cmd: Command to call.
        """
        raise commands.CommandNotFound(f'Command "{cmd}" is not found')

    @calc.command()
    async def diff(
        self, ctx: commands.Context[base.Bot], var: str = "x", *, expr: str
    ):
        """Calculates derivatives.

        Args:
            ctx: Context of the command.
            var: Variable to calculate derivatives.
            expr: Expression to calculate derivatives.
        """
        raw_var = parse_raw(var)
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(
                sympy.Derivative(raw_expr, raw_var),
                sympy.diff(raw_expr, raw_var),
            ),
            ephemeral=True,
        )

    @calc.command()
    async def adiff(
        self, ctx: commands.Context[base.Bot], var: str = "x", *, expr: str
    ):
        """Calculates integrals.

        Args:
            ctx: Context of the command.
            var: Variable to calculate integrals.
            expr: Expression to calculate integrals.
        """
        raw_var = parse_raw(var)
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(
                sympy.Integral(raw_expr, raw_var),
                sympy.integrate(raw_expr, raw_var),
            ),
            ephemeral=True,
        )

    @calc.command()
    async def limit(
        self,
        ctx: commands.Context[base.Bot],
        pos: str,
        var: str = "x",
        *,
        expr: str,
    ):
        """Calculates limits.

        Args:
            ctx: Context of the command.
            pos: Position to calculate limits.
            var: Variable to calculate limits.
            expr: Expression to calculate limits.
        """
        raw_var = parse_raw(var)
        raw_pos = parse_raw(pos)
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(
                sympy.Limit(raw_expr, raw_var, raw_pos),
                sympy.limit(raw_expr, raw_var, raw_pos),
            ),
            ephemeral=True,
        )

    @commands.hybrid_group(fallback="solve")
    async def solve(
        self, ctx: commands.Context[base.Bot], var: str = "x", *, expr: str
    ):
        """Solves equations.

        Args:
            ctx: Context of the command.
            var: Variable to solve.
            expr: Expression to solve.
        """
        raw_var = parse_raw(var)
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(
                sympy.ConditionSet(
                    raw_var, sympy.Eq(raw_expr, 0, evaluate=False)
                ),
                sympy.solveset(raw_expr, raw_var),
            ),
            ephemeral=True,
        )

    @solve.command()
    async def ineq(
        self, ctx: commands.Context[base.Bot], var: str = "x", *, expr: str
    ):
        """Solves inequalities.

        Args:
            ctx: Context of the command.
            var: Variable to solve.
            expr: Expression to solve.
        """
        raw_var = parse_raw(var)
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(
                sympy.ConditionSet(raw_var, raw_expr, sympy.S.Reals),
                sympy.solveset(raw_expr, raw_var, sympy.S.Reals),
            ),
            ephemeral=True,
        )

    @solve.command()
    async def roots(
        self, ctx: commands.Context[base.Bot], var: str = "x", *, expr: str
    ):
        """Finds roots of polynomials.

        Args:
            ctx: Context of the command.
            var: Variable to solve.
            expr: Expression to solve.
        """
        raw_var = parse_raw(var)
        raw_expr = parse_raw(expr)
        res_var = var.strip("`").replace("\\", "")
        res_expr = expr.strip("`").replace("\\", "")
        roots = sympy.roots(
            raw_expr,
            raw_var,
            multiple=True,
            quintics=self.bot.cfg["feynmanium"]["cogs"]["calc"]["five"],
        )
        if len(roots) == 0:
            await ctx.send(
                f"Solving for `{res_var}` in `{res_expr}` failed.",
                ephemeral=True,
            )
            return
        await ctx.send(
            f"Solving for `{res_var}` in `{res_expr}` gives:", ephemeral=True
        )
        for root in roots:
            result = sympy.pretty(root, use_unicode=False)
            await ctx.send(f"```{result}```", ephemeral=True)

    @solve.command()
    async def dsolv(
        self, ctx: commands.Context[base.Bot], var: str = "f(x)", *, expr: str
    ):
        """Solves differential equations.

        Args:
            ctx: Context of the command.
            var: Function to solve.
            expr: Expression to solve.
        """
        raw_var = parse_raw(var)
        raw_expr = sympy.parse_expr(
            expr.strip("`").replace("\\", ""),
            local_dict={"D": sympy.Derivative},
        )
        res_var = var.strip("`").replace("\\", "")
        res_expr = expr.strip("`").replace("\\", "")
        result = sympy.pretty(
            sympy.dsolve(raw_expr, raw_var), use_unicode=False
        )
        await ctx.send(
            f"Solving for `{res_var}` in `{res_expr}` gives: ```{result}```",
            ephemeral=True,
        )


async def setup(bot: base.Bot):
    """Set up the extension.

    Args:
        bot: Bot that loads the extension.
    """
    await bot.add_cog(CalcCog(bot), guilds=list(bot.glds))


async def teardown(bot: base.Bot):
    """Tear down the extension.

    Args:
        bot: Bot that unloads the extension.
    """
    await bot.remove_cog("Mathematics", guilds=list(bot.glds))
