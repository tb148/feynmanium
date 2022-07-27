"""Mathematical commands."""
import sympy
from discord import app_commands
from discord.ext import commands  # type: ignore[attr-defined]

from .. import base

config = base.config


def parse_raw(expr: str):
    """Turn the expression into the required format."""
    return sympy.S(expr.strip("`").replace("\\", ""), evaluate=False)


def pretty_eq(lhs, rhs):
    """Pretty print an equality."""
    result = sympy.pretty(sympy.Eq(lhs, rhs, evaluate=False), use_unicode=False)
    return f"```\n{result}\n```"


class CalcCog(  # type: ignore[call-arg]
    commands.Cog,
    name=config["calc"]["name"],
    description=config["calc"]["desc"],
):
    """Mathematical commands."""

    def __init__(self, bot: commands.AutoShardedBot):
        """Initialize the cog."""
        self.bot = bot

    @commands.hybrid_group(
        name=config["calc"]["simpl"]["name"],
        enabled=config["calc"]["simpl"]["enbl"],
        hidden=config["calc"]["simpl"]["hide"],
        help=config["calc"]["simpl"]["desc"],
        fallback=config["calc"]["simpl"]["name"],
    )
    @app_commands.guilds(*config["calc"]["glds"])
    @app_commands.describe(expr=config["calc"]["simpl"]["expr"])
    async def simpl(self, ctx: commands.Context, *, expr: str):
        """Simplify expressions."""
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(raw_expr, sympy.simplify(raw_expr, ratio=sympy.oo))
        )

    @simpl.command(
        name=config["calc"]["expn"]["name"],
        enabled=config["calc"]["expn"]["enbl"],
        hidden=config["calc"]["expn"]["hide"],
        help=config["calc"]["expn"]["desc"],
    )
    @app_commands.guilds(*config["calc"]["glds"])
    @app_commands.describe(expr=config["calc"]["expn"]["expr"])
    async def expn(self, ctx: commands.Context, *, expr: str):
        """Expand expressions."""
        raw_expr = parse_raw(expr)
        await ctx.send(pretty_eq(raw_expr, sympy.expand(raw_expr)))

    @simpl.command(
        name=config["calc"]["fact"]["name"],
        enabled=config["calc"]["fact"]["enbl"],
        hidden=config["calc"]["fact"]["hide"],
        help=config["calc"]["fact"]["desc"],
    )
    @app_commands.guilds(*config["calc"]["glds"])
    @app_commands.describe(expr=config["calc"]["fact"]["expr"])
    async def fact(self, ctx: commands.Context, *, expr: str):
        """Factor expressions."""
        raw_expr = parse_raw(expr)
        await ctx.send(pretty_eq(raw_expr, sympy.factor(raw_expr)))

    @simpl.command(
        name=config["calc"]["apart"]["name"],
        enabled=config["calc"]["apart"]["enbl"],
        hidden=config["calc"]["apart"]["hide"],
        help=config["calc"]["apart"]["desc"],
    )
    @app_commands.guilds(*config["calc"]["glds"])
    @app_commands.describe(expr=config["calc"]["apart"]["expr"])
    async def apart(self, ctx: commands.Context, *, expr: str):
        """Decompose partial fractions."""
        raw_expr = parse_raw(expr)
        await ctx.send(pretty_eq(raw_expr, sympy.apart(raw_expr)))

    @commands.hybrid_group(
        name=config["calc"]["calc"]["name"],
        enabled=config["calc"]["calc"]["enbl"],
        hidden=config["calc"]["calc"]["hide"],
        help=config["calc"]["calc"]["desc"],
    )
    @app_commands.guilds(*config["calc"]["glds"])
    async def calc(self, ctx: commands.Context, cmd: str):
        """Throw an error."""
        raise commands.CommandNotFound(f'Command "{cmd}" is not found')

    @calc.command(
        name=config["calc"]["diff"]["name"],
        enabled=config["calc"]["diff"]["enbl"],
        hidden=config["calc"]["diff"]["hide"],
        help=config["calc"]["diff"]["desc"],
    )
    @app_commands.guilds(*config["calc"]["glds"])
    @app_commands.describe(
        var=config["calc"]["diff"]["var"], expr=config["calc"]["diff"]["expr"]
    )
    async def diff(self, ctx: commands.Context, var: str = "x", *, expr: str):
        """Take derivatives."""
        raw_var = parse_raw(var)
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(
                sympy.Derivative(raw_expr, raw_var),
                sympy.diff(raw_expr, raw_var),
            )
        )

    @calc.command(
        name=config["calc"]["adiff"]["name"],
        enabled=config["calc"]["adiff"]["enbl"],
        hidden=config["calc"]["adiff"]["hide"],
        help=config["calc"]["adiff"]["desc"],
    )
    @app_commands.guilds(*config["calc"]["glds"])
    @app_commands.describe(
        var=config["calc"]["adiff"]["var"], expr=config["calc"]["adiff"]["expr"]
    )
    async def adiff(self, ctx: commands.Context, var: str = "x", *, expr: str):
        """Calculate integrals."""
        raw_var = parse_raw(var)
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(
                sympy.Integral(raw_expr, raw_var),
                sympy.integrate(raw_expr, raw_var),
            )
        )

    @calc.command(
        name=config["calc"]["limit"]["name"],
        enabled=config["calc"]["limit"]["enbl"],
        hidden=config["calc"]["limit"]["hide"],
        help=config["calc"]["limit"]["desc"],
    )
    @app_commands.guilds(*config["calc"]["glds"])
    @app_commands.describe(
        pos=config["calc"]["limit"]["pos"],
        var=config["calc"]["limit"]["var"],
        expr=config["calc"]["limit"]["expr"],
    )
    async def limit(
        self, ctx: commands.Context, pos: str, var: str = "x", *, expr: str
    ):
        """Compute limits."""
        raw_var = parse_raw(var)
        raw_pos = parse_raw(pos)
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(
                sympy.Limit(raw_expr, raw_var, raw_pos),
                sympy.limit(raw_expr, raw_var, raw_pos),
            )
        )

    @commands.hybrid_group(
        name=config["calc"]["solve"]["name"],
        enabled=config["calc"]["solve"]["enbl"],
        hidden=config["calc"]["solve"]["hide"],
        help=config["calc"]["solve"]["desc"],
        fallback=config["calc"]["solve"]["name"],
    )
    @app_commands.guilds(*config["calc"]["glds"])
    @app_commands.describe(
        var=config["calc"]["solve"]["var"], expr=config["calc"]["solve"]["expr"]
    )
    async def solve(self, ctx: commands.Context, var: str = "x", *, expr: str):
        """Solve equations."""
        raw_var = parse_raw(var)
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(
                sympy.ConditionSet(
                    raw_var, sympy.Eq(raw_expr, 0, evaluate=False)
                ),
                sympy.solveset(raw_expr, raw_var),
            )
        )

    @solve.command(
        name=config["calc"]["ineq"]["name"],
        enabled=config["calc"]["ineq"]["enbl"],
        hidden=config["calc"]["ineq"]["hide"],
        help=config["calc"]["ineq"]["desc"],
    )
    @app_commands.guilds(*config["calc"]["glds"])
    @app_commands.describe(
        var=config["calc"]["ineq"]["var"], expr=config["calc"]["ineq"]["expr"]
    )
    async def ineq(self, ctx: commands.Context, var: str = "x", *, expr: str):
        """Solve inequalities."""
        raw_var = parse_raw(var)
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(
                sympy.ConditionSet(raw_var, raw_expr, sympy.S.Reals),
                sympy.solveset(raw_expr, raw_var, sympy.S.Reals),
            )
        )

    @solve.command(
        name=config["calc"]["roots"]["name"],
        enabled=config["calc"]["roots"]["enbl"],
        hidden=config["calc"]["roots"]["hide"],
        help=config["calc"]["roots"]["desc"],
    )
    @app_commands.guilds(*config["calc"]["glds"])
    @app_commands.describe(
        var=config["calc"]["roots"]["var"], expr=config["calc"]["roots"]["expr"]
    )
    async def roots(self, ctx: commands.Context, var: str = "x", *, expr: str):
        """Find roots of polynomials."""
        raw_var = parse_raw(var)
        raw_expr = parse_raw(expr)
        res_var = var.strip("`").replace("\\", "")
        res_expr = expr.strip("`").replace("\\", "")
        roots = sympy.roots(raw_expr, raw_var, quintics=True, multiple=True)
        if len(roots) == 0:
            await ctx.send(f"Cannot find roots of `{res_var}` on `{res_expr}`")
            return
        await ctx.send(f"The roots of `{res_var}` on `{res_expr}` are")
        for root in roots:
            result = sympy.pretty(root, use_unicode=False)
            await ctx.send(f"```\n{result}\n```")

    @solve.command(
        name=config["calc"]["dsolv"]["name"],
        enabled=config["calc"]["dsolv"]["enbl"],
        hidden=config["calc"]["dsolv"]["hide"],
        help=config["calc"]["dsolv"]["desc"],
    )
    @app_commands.guilds(*config["calc"]["glds"])
    @app_commands.describe(
        var=config["calc"]["dsolv"]["var"], expr=config["calc"]["dsolv"]["expr"]
    )
    async def dsolv(self, ctx: commands.Context, var: str = "x", *, expr: str):
        """Solve differential equations."""
        raw_var = parse_raw(var)
        raw_expr = sympy.parse_expr(
            expr.strip("`").replace("\\", ""),
            local_dict={"D": sympy.Derivative},
        )
        await ctx.send(
            "Solving for `{}` in `{}` gives\n```\n{}\n```".format(
                var.strip("`").replace("\\", ""),
                expr.strip("`").replace("\\", ""),
                sympy.pretty(
                    sympy.dsolve(raw_expr, raw_var), use_unicode=False
                ),
            )
        )


async def setup(bot):
    """Set up the extension."""
    await bot.add_cog(CalcCog(bot))
