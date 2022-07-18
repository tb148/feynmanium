"""Some games to play."""
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
stockfish = engine.SimpleEngine.popen_uci("stockfish/stockfish_14_x64")
dummy = [discord.SelectOption(label="dummy")]


def get_move(board: chess.Board, level: int) -> chess.Move:
    """Gets the next move."""
    if level == 0:
        return random.choice(board.legal_moves)
    stockfish.configure({"Skill Level": level - 1})
    result = stockfish.play(board, chess.engine.Limit(depth=16))
    return result.move


class ChessView(ui.View):
    """View for chess."""

    def __init__(
        self,
        board: chess.Board,
        color: bool,
        level: int,
        *,
        timeout: typing.Optional[float] = 120
    ):
        """Initialize the view."""
        if board.turn != color:
            board.push(get_move(board, level))
        self.board, self.color, self.level = board, color, level
        super().__init__(timeout=timeout)
        self._update()

    def get_svg(self) -> str:
        """Gets the SVG of the board."""
        return svg.board(
            self.board,
            orientation=self.color,
            lastmove=(
                None if len(self.board.move_stack) == 0 else self.board.peek()
            ),
            squares=self.board.checkers(),
        )

    def get_pgn(self, user: str) -> pgn.Game:
        """Gets the PGN of the game."""
        game = pgn.Game.from_board(self.board)
        game.headers["Event"] = "Live Chess"
        game.headers["Site"] = "Discord"
        game.headers["Date"] = datetime.date.today().strftime("%Y.%m.%d")
        game.headers["Round"] = "-"
        if self.color == chess.WHITE:
            game.headers["White"] = user
            game.headers["Black"] = config["game"]["chess"]["card"][self.level]
        else:
            game.headers["White"] = config["game"]["chess"]["card"][self.level]
            game.headers["Black"] = user
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

    @ui.select(options=dummy, placeholder="Select the source square", row=0)
    async def _src(self, interaction: discord.Interaction, select: ui.Select):
        """Selects the source square."""
        self._set_squares(select.values[0])
        self.children[1].options = [
            discord.SelectOption(
                label=self.board.san(move), description=self.board.lan(move)
            )
            for move in self.board.legal_moves
            if move.from_square == chess.parse_square(select.values[0])
        ]
        self.children[1].disabled = False
        await interaction.response.edit_message(view=self)

    @ui.select(options=dummy, placeholder="Select the target square", row=1)
    async def _dest(self, interaction: discord.Interaction, select: ui.Select):
        """Selects the target square."""
        self.board.push_san(select.values[0])
        if not self.board.is_game_over():
            self.board.push(get_move(self.board, self.level))
        self._update()
        await interaction.response.edit_message(
            attachments=[
                discord.File(
                    io.BytesIO(cairosvg.svg2png(self.get_svg())), "board.png"
                ),
                discord.File(
                    io.StringIO(self.get_pgn(interaction.user.name)), "game.pgn"
                ),
            ],
            view=self,
        )


class GameCog(
    commands.Cog,
    name=config["game"]["name"],
    description=config["game"]["desc"],
):
    """Some games to play."""

    def __init__(self, bot):
        """Initialize the cog."""
        self.bot = bot

    @commands.hybrid_command(
        name=config["game"]["chess"]["name"],
        enabled=config["game"]["chess"]["enbl"],
        hidden=config["game"]["chess"]["hide"],
        help=config["game"]["chess"]["desc"],
    )
    @app_commands.guilds(*config["game"]["glds"])
    @app_commands.describe(
        lvl=config["game"]["chess"]["lvl"], fst=config["game"]["chess"]["fst"]
    )
    async def chess(
        self,
        ctx,
        lvl: commands.Range[int, 0, 21],
        fst: typing.Optional[bool] = None,
    ):
        """Plays chess."""
        if fst is None:
            fst = bool(random.randrange(2))
        view = ChessView(chess.Board(), fst, lvl)
        await ctx.send(
            files=[
                discord.File(
                    io.BytesIO(cairosvg.svg2png(view.get_svg())), "board.png"
                ),
                discord.File(
                    io.StringIO(view.get_pgn(ctx.author.name)), "game.pgn"
                ),
            ],
            view=view,
        )


async def setup(bot):
    """Sets up the extension."""
    await bot.add_cog(GameCog(bot))
