"""Commands related to chess."""
import asyncio
import datetime
import io
import random
import typing

import cairosvg
import chess
import discord
import toml
from chess import engine, pgn, svg
from discord import app_commands, ui
from discord.ext import commands

config = toml.load("config.toml")
dummy = [discord.SelectOption(label="dummy")]


async def get_move(board: chess.Board, level: int) -> chess.Move:
    """Gets the next move."""
    if level == 0:
        return random.choice(list(board.legal_moves))
    transport, stockfish = await engine.popen_uci("stockfish/stockfish_14_x64")
    result = await stockfish.play(
        board, chess.engine.Limit(depth=16), options={"Skill Level": level - 1}
    ).move
    await stockfish.quit()
    return result


def get_svg(board: chess.Board, color: chess.Color) -> str:
    """Gets the SVG of the board."""
    return svg.board(
        board,
        orientation=color,
        lastmove=(None if len(board.move_stack) == 0 else board.peek()),
        check=(board.king(board.turn) if board.is_check() else None),
    )


class ChessView(ui.View):
    """View for chess."""

    def __init__(
        self,
        board: chess.Board,
        color: bool,
        level: int,
        *,
        user: discord.User,
        timeout: typing.Optional[float] = 300,
    ):
        """Initialize the view."""
        self.user, self.message = user, None
        if board.turn != color:
            board.push(asyncio.run(get_move(board, level)))
        self.board, self.color, self.level = board, color, level
        super().__init__(timeout=timeout)
        self._update()

    def get_pgn(self) -> pgn.Game:
        """Gets the PGN of the game."""
        game = pgn.Game.from_board(self.board)
        game.headers["Event"] = "Live Chess"
        game.headers["Site"] = "Discord"
        game.headers["Date"] = datetime.date.today().strftime("%Y.%m.%d")
        game.headers["Round"] = "-"
        if self.color == chess.WHITE:
            game.headers["White"] = self.user.name
            game.headers["Black"] = config["chess"]["chess"]["card"][self.level]
        else:
            game.headers["White"] = config["chess"]["chess"]["card"][self.level]
            game.headers["Black"] = self.user.name
        return str(game)

    def _set_squares(self, default: str):
        squares = {move.from_square for move in self.board.legal_moves}
        self.children[0].options = [
            discord.SelectOption(
                label=chess.square_name(square),
                description=chess.piece_name(self.board.piece_type_at(square)),
                default=(chess.square_name(square) == default),
            )
            for square in squares
        ]
        self.children[0].disabled = False

    def _update(self):
        if self.board.is_game_over():
            self.children[0].options = dummy
            self.children[0].disabled = True
        else:
            self._set_squares("")
        self.children[1].options = dummy
        self.children[1].disabled = True

    async def on_timeout(self):
        """Disable all items on timeout."""
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

    @ui.select(options=dummy, placeholder="Select the source square", row=0)
    async def _src(self, interaction: discord.Interaction, select: ui.Select):
        """Selects the source square."""
        if interaction.user != self.user:
            return
        await interaction.response.defer()
        self._set_squares(select.values[0])
        self.children[1].options = [
            discord.SelectOption(
                label=self.board.san(move), description=self.board.lan(move)
            )
            for move in self.board.legal_moves
            if move.from_square == chess.parse_square(select.values[0])
        ]
        self.children[1].disabled = False
        await interaction.edit_original_message(view=self)

    @ui.select(options=dummy, placeholder="Select the target square", row=1)
    async def _dest(self, interaction: discord.Interaction, select: ui.Select):
        """Selects the target square."""
        if interaction.user != self.user:
            return
        await interaction.response.defer()
        self.board.push_san(select.values[0])
        if not self.board.is_game_over():
            self.board.push(await get_move(self.board, self.level))
        self._update()
        await interaction.edit_original_message(
            content=self.board.fen(),
            attachments=[
                discord.File(
                    io.BytesIO(
                        cairosvg.svg2png(get_svg(self.board, self.color))
                    ),
                    "board.png",
                ),
                discord.File(io.StringIO(self.get_pgn()), "game.pgn"),
            ],
            view=self,
        )


class ChessCog(
    commands.Cog,
    name=config["chess"]["name"],
    description=config["chess"]["desc"],
):
    """Some games to play."""

    def __init__(self, bot):
        """Initialize the cog."""
        self.bot = bot

    @commands.hybrid_command(
        name=config["chess"]["chess"]["name"],
        enabled=config["chess"]["chess"]["enbl"],
        hidden=config["chess"]["chess"]["hide"],
        help=config["chess"]["chess"]["desc"],
    )
    @app_commands.guilds(*config["chess"]["glds"])
    @app_commands.describe(
        lvl=config["chess"]["chess"]["lvl"], fst=config["chess"]["chess"]["fst"]
    )
    async def chess(
        self,
        ctx: commands.Context,
        lvl: commands.Range[int, 0, 21],
        fst: typing.Optional[bool] = None,
    ):
        """Plays chess."""
        if fst is None:
            fst = bool(random.randrange(2))
        view = ChessView(chess.Board(), fst, lvl, user=ctx.author)
        view.message = await ctx.send(
            view.board.fen(),
            files=[
                discord.File(
                    io.BytesIO(cairosvg.svg2png(get_svg(view.board, fst))),
                    "board.png",
                ),
                discord.File(io.StringIO(view.get_pgn()), "game.pgn"),
            ],
            view=view,
        )

    @commands.hybrid_command(
        name=config["chess"]["anlys"]["name"],
        enabled=config["chess"]["anlys"]["enbl"],
        hidden=config["chess"]["anlys"]["hide"],
        help=config["chess"]["anlys"]["desc"],
    )
    @app_commands.guilds(*config["chess"]["glds"])
    @app_commands.describe(fen=config["chess"]["anlys"]["fen"])
    async def anlys(self, ctx: commands.Context, fen: str):
        await ctx.defer()
        board = chess.Board(fen)
        transport, stockfish = await engine.popen_uci(
            "stockfish/stockfish_14_x64"
        )
        info = await stockfish.analyse(board, engine.Limit(depth=20))
        await stockfish.quit()
        score: engine.Score = info["score"].white()
        wdl = score.wdl(model="lichess").expectation()
        if score == engine.Mate(0):
            result = "#"
        elif score.is_mate():
            result = "#" + score.mate()
        else:
            result = str(score.score()) + "cp"
        await ctx.send(
            "White has an advantage of {}, which is a {}% probability of winning.".format(
                result, round(wdl * 100, 2)
            ),
            file=discord.File(
                io.BytesIO(cairosvg.svg2png(get_svg(board, chess.WHITE))),
                "board.png",
            ),
        )


async def setup(bot):
    """Sets up the extension."""
    await bot.add_cog(ChessCog(bot))
