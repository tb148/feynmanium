"""Mathematical commands."""
import sympy
import toml
from discord import app_commands
from discord.ext import commands

config = toml.load("config.toml")


def parse_raw(expr: str):
    """Turns the expression into the required format."""
    return sympy.S(expr.strip("`").replace("\\", ""), evaluate=False)


def pretty_eq(lhs, rhs):
    """Pretty prints an equality."""
    result = sympy.pretty(sympy.Eq(lhs, rhs, evaluate=False), use_unicode=False)
    return f"```\n{result}\n```"


class MathCog(  # type: ignore[call-arg]
    commands.Cog,
    name=config["math"]["name"],
    description=config["math"]["desc"],
):
    """Mathematical commands."""

    def __init__(self, bot: commands.AutoShardedBot):
        """Initialize the cog."""
        self.bot = bot

    @commands.hybrid_group(
        name=config["math"]["simpl"]["name"],
        enabled=config["math"]["simpl"]["enbl"],
        hidden=config["math"]["simpl"]["hide"],
        help=config["math"]["simpl"]["desc"],
        fallback=config["math"]["simpl"]["name"],
    )
    @app_commands.guilds(*config["math"]["glds"])
    @app_commands.describe(expr=config["math"]["simpl"]["expr"])
    async def simpl(self, ctx: commands.Context, *, expr: str):
        """Simplifies expressions."""
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(raw_expr, sympy.simplify(raw_expr, ratio=sympy.oo))
        )

    @simpl.command(
        name=config["math"]["expn"]["name"],
        enabled=config["math"]["expn"]["enbl"],
        hidden=config["math"]["expn"]["hide"],
        help=config["math"]["expn"]["desc"],
    )
    @app_commands.guilds(*config["math"]["glds"])
    @app_commands.describe(expr=config["math"]["expn"]["expr"])
    async def expn(self, ctx: commands.Context, *, expr: str):
        """Expands expressions."""
        raw_expr = parse_raw(expr)
        await ctx.send(pretty_eq(raw_expr, sympy.expand(raw_expr)))

    @simpl.command(
        name=config["math"]["fact"]["name"],
        enabled=config["math"]["fact"]["enbl"],
        hidden=config["math"]["fact"]["hide"],
        help=config["math"]["fact"]["desc"],
    )
    @app_commands.guilds(*config["math"]["glds"])
    @app_commands.describe(expr=config["math"]["fact"]["expr"])
    async def fact(self, ctx: commands.Context, *, expr: str):
        """Factors expressions."""
        raw_expr = parse_raw(expr)
        await ctx.send(pretty_eq(raw_expr, sympy.factor(raw_expr)))

    @simpl.command(
        name=config["math"]["apart"]["name"],
        enabled=config["math"]["apart"]["enbl"],
        hidden=config["math"]["apart"]["hide"],
        help=config["math"]["apart"]["desc"],
    )
    @app_commands.guilds(*config["math"]["glds"])
    @app_commands.describe(expr=config["math"]["apart"]["expr"])
    async def apart(self, ctx: commands.Context, *, expr: str):
        """Factors expressions."""
        raw_expr = parse_raw(expr)
        await ctx.send(pretty_eq(raw_expr, sympy.apart(raw_expr)))

    @commands.hybrid_group(
        name=config["math"]["calc"]["name"],
        enabled=config["math"]["calc"]["enbl"],
        hidden=config["math"]["calc"]["hide"],
        help=config["math"]["calc"]["desc"],
    )
    @app_commands.guilds(*config["math"]["glds"])
    async def calc(self, ctx: commands.Context, cmd: str):
        """Does calculus."""
        raise commands.CommandNotFound(f'Command "{cmd}" is not found')

    @calc.command(
        name=config["math"]["diff"]["name"],
        enabled=config["math"]["diff"]["enbl"],
        hidden=config["math"]["diff"]["hide"],
        help=config["math"]["diff"]["desc"],
    )
    @app_commands.guilds(*config["math"]["glds"])
    @app_commands.describe(
        var=config["math"]["diff"]["var"], expr=config["math"]["diff"]["expr"]
    )
    async def diff(self, ctx: commands.Context, var: str = "x", *, expr: str):
        """Takes derivatives."""
        raw_var = parse_raw(var)
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(
                sympy.Derivative(raw_expr, raw_var),
                sympy.diff(raw_expr, raw_var),
            )
        )

    @calc.command(
        name=config["math"]["adiff"]["name"],
        enabled=config["math"]["adiff"]["enbl"],
        hidden=config["math"]["adiff"]["hide"],
        help=config["math"]["adiff"]["desc"],
    )
    @app_commands.guilds(*config["math"]["glds"])
    @app_commands.describe(
        var=config["math"]["adiff"]["var"], expr=config["math"]["adiff"]["expr"]
    )
    async def adiff(self, ctx: commands.Context, var: str = "x", *, expr: str):
        """Integrates."""
        raw_var = parse_raw(var)
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(
                sympy.Integral(raw_expr, raw_var),
                sympy.integrate(raw_expr, raw_var),
            )
        )

    @calc.command(
        name=config["math"]["limit"]["name"],
        enabled=config["math"]["limit"]["enbl"],
        hidden=config["math"]["limit"]["hide"],
        help=config["math"]["limit"]["desc"],
    )
    @app_commands.guilds(*config["math"]["glds"])
    @app_commands.describe(
        pos=config["math"]["limit"]["pos"],
        var=config["math"]["limit"]["var"],
        expr=config["math"]["limit"]["expr"],
    )
    async def limit(
        self, ctx: commands.Context, pos: str, var: str = "x", *, expr: str
    ):
        """Computes limits."""
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
        name=config["math"]["solve"]["name"],
        enabled=config["math"]["solve"]["enbl"],
        hidden=config["math"]["solve"]["hide"],
        help=config["math"]["solve"]["desc"],
        fallback=config["math"]["solve"]["name"],
    )
    @app_commands.guilds(*config["math"]["glds"])
    @app_commands.describe(
        var=config["math"]["solve"]["var"], expr=config["math"]["solve"]["expr"]
    )
    async def solve(self, ctx: commands.Context, var: str = "x", *, expr: str):
        """Solves equations."""
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
        name=config["math"]["ineq"]["name"],
        enabled=config["math"]["ineq"]["enbl"],
        hidden=config["math"]["ineq"]["hide"],
        help=config["math"]["ineq"]["desc"],
    )
    @app_commands.guilds(*config["math"]["glds"])
    @app_commands.describe(
        var=config["math"]["ineq"]["var"], expr=config["math"]["ineq"]["expr"]
    )
    async def ineq(self, ctx: commands.Context, var: str = "x", *, expr: str):
        """Solves inequalities."""
        raw_var = parse_raw(var)
        raw_expr = parse_raw(expr)
        await ctx.send(
            pretty_eq(
                sympy.ConditionSet(raw_var, raw_expr, sympy.S.Reals),
                sympy.solveset(raw_expr, raw_var, sympy.S.Reals),
            )
        )

    @solve.command(
        name=config["math"]["roots"]["name"],
        enabled=config["math"]["roots"]["enbl"],
        hidden=config["math"]["roots"]["hide"],
        help=config["math"]["roots"]["desc"],
    )
    @app_commands.guilds(*config["math"]["glds"])
    @app_commands.describe(
        var=config["math"]["roots"]["var"], expr=config["math"]["roots"]["expr"]
    )
    async def roots(self, ctx: commands.Context, var: str = "x", *, expr: str):
        """Finds roots of polynomials."""
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
        name=config["math"]["dsolv"]["name"],
        enabled=config["math"]["dsolv"]["enbl"],
        hidden=config["math"]["dsolv"]["hide"],
        help=config["math"]["dsolv"]["desc"],
    )
    @app_commands.guilds(*config["math"]["glds"])
    @app_commands.describe(
        var=config["math"]["dsolv"]["var"], expr=config["math"]["dsolv"]["expr"]
    )
    async def dsolv(self, ctx: commands.Context, var: str = "x", *, expr: str):
        """Solves differential equations."""
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
    """Sets up the extension."""
    await bot.add_cog(MathCog(bot))
