"""Commands related to chess."""
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
    _, stockfish = await engine.popen_uci("stockfish/stockfish_14_x64")
    result = await stockfish.play(
        board, chess.engine.Limit(depth=16), options={"Skill Level": level - 1}
    )
    await stockfish.quit()
    if result.move is not None:
        return result.move
    else:
        return chess.Move.null()


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
        self.board, self.color, self.level = board, color, level
        super().__init__(timeout=timeout)
        self.update_dest()

    def get_pgn(self) -> pgn.Game:
        """Gets the PGN of the game."""
        game = pgn.Game.from_board(self.board)
        game.headers["Event"] = "Live Chess"
        game.headers["Site"] = "Discord"
        game.headers["Date"] = datetime.date.today().strftime("%Y.%m.%d")
        game.headers["Round"] = "-"
        if self.color == chess.WHITE:
            game.headers["White"] = self.user.name
            game.headers["Black"] = config["game"]["chess"]["card"][self.level]
        else:
            game.headers["White"] = config["game"]["chess"]["card"][self.level]
            game.headers["Black"] = self.user.name
        return game

    def update_src(self, default: str):
        """Updates the options after selecting a source."""
        squares = {move.from_square for move in self.board.legal_moves}
        self.src.options = []
        for square in squares:
            piece = self.board.piece_type_at(square)
            if piece is not None:
                self.src.options.append(
                    discord.SelectOption(
                        label=chess.square_name(square),
                        description=chess.piece_name(piece),
                        default=(chess.square_name(square) == default),
                    )
                )
        if not self.src.options:
            self.src.options = dummy
        self.src.disabled = False

    def update_dest(self):
        """Updates the options after selecting a target."""
        if self.board.is_game_over():
            self.src.options = dummy
            self.src.disabled = True
        else:
            self.update_src("")
        self.dest.options = dummy
        self.dest.disabled = True

    async def make_move(self):
        """Makes a move."""
        if not self.board.is_game_over() and self.board.turn != self.color:
            self.board.push(await get_move(self.board, self.level))

    async def on_timeout(self):
        """Disable all items on timeout."""
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

    @ui.select(options=dummy, placeholder="Select the source square", row=0)
    async def src(self, interaction: discord.Interaction, select: ui.Select):
        """Selects the source square."""
        if interaction.user != self.user:
            return
        await interaction.response.defer()
        self.update_src(select.values[0])
        self.dest.options = [
            discord.SelectOption(
                label=self.board.san(move), description=self.board.lan(move)
            )
            for move in self.board.legal_moves
            if move.from_square == chess.parse_square(select.values[0])
        ]
        self.dest.disabled = False
        await interaction.edit_original_message(view=self)

    @ui.select(options=dummy, placeholder="Select the target square", row=1)
    async def dest(self, interaction: discord.Interaction, select: ui.Select):
        """Selects the target square."""
        if interaction.user != self.user:
            return
        await interaction.response.defer()
        self.board.push_san(select.values[0])
        await self.make_move()
        self.update_dest()
        fen = self.board.fen()
        await interaction.edit_original_message(
            content=f"`{fen}`",
            attachments=[
                discord.File(
                    io.BytesIO(
                        cairosvg.svg2png(get_svg(self.board, self.color))
                    ),
                    "board.png",
                ),
                discord.File(
                    io.BytesIO(bytes(str(self.get_pgn()), "utf-8")), "game.pgn"
                ),
            ],
            view=self,
        )


class ChessCog(  # type: ignore[call-arg]
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
        ctx: commands.Context,
        lvl: commands.Range[int, 0, 21],
        fst: typing.Optional[bool] = None,
    ):
        """Plays chess."""
        if fst is None:
            fst = bool(random.randrange(2))
        view = ChessView(chess.Board(), fst, lvl, user=ctx.author)
        await view.make_move()
        fen = view.board.fen()
        view.message = await ctx.send(
            f"`{fen}`",
            files=[
                discord.File(
                    io.BytesIO(cairosvg.svg2png(get_svg(view.board, fst))),
                    "board.png",
                ),
                discord.File(
                    io.BytesIO(bytes(str(view.get_pgn()), "utf-8")), "game.pgn"
                ),
            ],
            view=view,
        )

    @commands.hybrid_command(
        name=config["game"]["anlys"]["name"],
        enabled=config["game"]["anlys"]["enbl"],
        hidden=config["game"]["anlys"]["hide"],
        help=config["game"]["anlys"]["desc"],
    )
    @app_commands.guilds(*config["game"]["glds"])
    @app_commands.describe(fen=config["game"]["anlys"]["fen"])
    async def anlys(self, ctx: commands.Context, fen: str):
        """Gets some analysis for chess."""
        await ctx.defer()
        board = chess.Board(fen)
        _, stockfish = await engine.popen_uci("stockfish/stockfish_14_x64")
        info = await stockfish.analyse(board, engine.Limit(depth=20))
        await stockfish.quit()
        score: engine.Score = info["score"].white()
        wdl = round(score.wdl(model="lichess").expectation() * 100, 2)
        if score == engine.Mate(0):
            result = "#"
        elif score.is_mate():
            mate = score.mate()
            if mate is not None:
                result = "#" + str(mate)
            else:
                result = "#-0"
        else:
            result = str(score.score()) + "cp"
        await ctx.send(
            f"White has an advantage of {result}, which is a {wdl}% probability of winning.",
            file=discord.File(
                io.BytesIO(cairosvg.svg2png(get_svg(board, chess.WHITE))),
                "board.png",
            ),
        )


async def setup(bot):
    """Sets up the extension."""
    await bot.add_cog(ChessCog(bot))
