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
import datetime
import io
import secrets
import typing

import cairosvg
import chess
import discord
from chess import engine, pgn, svg
from discord import ui
from discord.ext import commands

from .. import base


async def get_move(path: str, board: chess.Board, level: int) -> chess.Move:
    """Plays a position using stockfish.

    Args:
        path: Path of the stockfish executable.
        board: Position to play.
        level: Skill level of stockfish.

    Returns:
        The move stockfish plays.
    """
    _, api = await engine.popen_uci(path)
    result = await api.play(
        board, engine.Limit(depth=16), options={"Skill Level": level - 1}
    )
    await api.quit()
    if result.move is not None:
        return result.move
    return chess.Move.null()


def get_svg(board: chess.Board, color: chess.Color) -> typing.Any:
    """Renders the SVG of the board.

    Args:
        board: Chessboard to render.
        color: Point of view.

    Returns:
        The rendered SVG.
    """
    result = svg.board(
        board,
        orientation=color,
        lastmove=(None if len(board.move_stack) == 0 else board.peek()),
        check=(board.king(board.turn) if board.is_check() else None),
    )
    return cairosvg.svg2png(result)


class ChessView(ui.View):
    """View for chess.

    Attributes:
        msg: Message that holds the view.
        user: Opponent of the bot.
        path: Path of the stockfish executable.
        name: Name of the bot to use.
        board: Chessboard of the game.
        color: Orientation of the player.
        level: Skill level of stockfish,
    """

    def __init__(
        self,
        board: chess.Board,
        color: bool,
        level: int,
        *,
        ctx: commands.Context[base.Bot],
    ):
        """Initializes the view.

        Args:
            board: Chessboard of the game.
            color: Orientation of the player.
            level: Skill level of stockfish,
            ctx: Context of the view.
        """
        self.msg: typing.Optional[discord.Message] = None
        self.user = ctx.author
        self.path: str = ctx.bot.cfg["feynmanium"]["cogs"]["game"]["path"]
        self.name: str = ctx.bot.cfg["feynmanium"]["cogs"]["game"]["card"][
            level
        ]
        self.board, self.color, self.level = board, color, level
        super().__init__(timeout=300)

    def get_pgn(self) -> pgn.Game:
        """Gets the PGN of the game.

        Returns:
            The PGN of the game.
        """
        game = pgn.Game.from_board(self.board)
        game.headers["Event"] = "Live Chess"
        game.headers["Site"] = "Discord"
        game.headers["Date"] = datetime.date.today().strftime("%Y.%m.%d")
        game.headers["Round"] = "-"
        if self.color == chess.WHITE:
            game.headers["White"] = self.user.name
            game.headers["Black"] = self.name
        else:
            game.headers["White"] = self.name
            game.headers["Black"] = self.user.name
        return game

    def update(self, default: str):
        """Updates the options after selecting a source.

        Args:
            default: Selected source square.
        """
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
            self.src.options = []
        self.src.disabled = False

    async def make_move(self):
        """Makes a move and updates the options."""
        if not self.board.is_game_over() and self.board.turn != self.color:
            self.board.push(await get_move(self.path, self.board, self.level))
        if self.board.is_game_over():
            self.src.options = []
            self.src.disabled = True
        else:
            self.update("")
        self.dest.options = []
        self.dest.disabled = True

    async def on_timeout(self):
        """Disables all items on timeout."""
        for item in self.children:
            if isinstance(item, (ui.Button, ui.Select)):
                item.disabled = True
        if self.msg is not None:
            await self.msg.edit(view=self)

    @ui.select(options=[], placeholder="Select the source square", row=0)
    async def src(self, interaction: discord.Interaction, select: ui.Select):
        """Selects the source square.

        Args:
            interaction: Interaction of the selection.
            select: Select menu of the selection.
        """
        if interaction.user != self.user:
            return
        await interaction.response.defer()
        self.update(select.values[0])
        self.dest.options = [
            discord.SelectOption(
                label=self.board.san(move), description=self.board.lan(move)
            )
            for move in self.board.legal_moves
            if move.from_square == chess.parse_square(select.values[0])
        ]
        self.dest.disabled = False
        await interaction.edit_original_response(view=self)

    @ui.select(options=[], placeholder="Select the target square", row=1)
    async def dest(self, interaction: discord.Interaction, select: ui.Select):
        """Select the target square.

        Args:
            interaction: Interaction of the selection.
            select: Select menu of the selection.
        """
        if interaction.user != self.user:
            return
        await interaction.response.defer()
        self.board.push_san(select.values[0])
        await self.make_move()
        fen = self.board.fen()
        await interaction.edit_original_response(
            content=f"`{fen}`",
            attachments=[
                discord.File(
                    io.BytesIO(get_svg(self.board, self.color)), "board.png"
                ),
                discord.File(
                    io.BytesIO(bytes(str(self.get_pgn()), "utf-8")), "game.pgn"
                ),
            ],
            view=self,
        )


class GameView(ui.View):
    """View for game.

    Attributes:
        msg: Message that holds the view.
        user: Opponent of the bot.
        node: PGN node of the state.
    """

    def __init__(self, node: pgn.GameNode, *, ctx: commands.Context[base.Bot]):
        """Initializes the view.

        Args:
            node: PGN node of the state.
            ctx: Context of the view.
        """
        super().__init__(timeout=300)
        self.msg: typing.Optional[discord.Message] = None
        self.user = ctx.author
        self.node = node
        self.update()

    def update(self):
        """Updates item availability."""
        self.root.disabled = self.node.parent is None
        self.prev.disabled = self.node.parent is None
        self.main.disabled = self.node.is_main_variation()
        self.next.disabled = self.node.is_end()
        self.leaf.disabled = self.node.is_end()
        self.move.options = []
        for child in self.node.variations:
            if child.move is not None:
                self.move.options.append(
                    discord.SelectOption(
                        label=self.node.board().san(child.move),
                        description=self.node.board().san(child.move),
                    )
                )
        if self.move.options:
            self.move.disabled = False
        else:
            self.move.options = []
            self.move.disabled = True

    async def sync(self, interaction: discord.Interaction):
        """Updates the view.

        Args:
            interaction: Interaction of the update.
        """
        self.update()
        await interaction.edit_original_response(
            attachments=[
                discord.File(
                    io.BytesIO(get_svg(self.node.board(), self.node.turn())),
                    "board.png",
                )
            ],
            view=self,
        )

    @ui.button(label="<<", style=discord.ButtonStyle.primary, row=0)
    async def root(self, interaction: discord.Interaction, button: ui.Button):
        """Go to the first move.

        Args:
            interaction: Interaction of the operation.
            button: Button of the operation.
        """
        del button
        if interaction.user != self.user:
            return
        await interaction.response.defer()
        self.node = self.node.game()
        await self.sync(interaction)

    @ui.button(label="<", row=0)
    async def prev(self, interaction: discord.Interaction, button: ui.Button):
        """Go to the previous move.

        Args:
            interaction: Interaction of the operation.
            button: Button of the operation.
        """
        del button
        if interaction.user != self.user:
            return
        await interaction.response.defer()
        result = self.node.parent
        if result is not None:
            self.node = result
        await self.sync(interaction)

    @ui.button(label="<>", row=0)
    async def main(self, interaction: discord.Interaction, button: ui.Button):
        """Go to the main variation.

        Args:
            interaction: Interaction of the operation.
            button: Button of the operation.
        """
        del button
        if interaction.user != self.user:
            return
        await interaction.response.defer()
        parent = self.node.parent
        if parent is not None:
            result = parent.next()
            if result is not None:
                self.node = result
        await self.sync(interaction)

    @ui.button(label=">", row=0)
    async def next(self, interaction: discord.Interaction, button: ui.Button):
        """Go to the next move.

        Args:
            interaction: Interaction of the operation.
            button: Button of the operation.
        """
        del button
        if interaction.user != self.user:
            return
        await interaction.response.defer()
        result = self.node.next()
        if result is not None:
            self.node = result
        await self.sync(interaction)

    @ui.button(label=">>", style=discord.ButtonStyle.primary, row=0)
    async def leaf(self, interaction: discord.Interaction, button: ui.Button):
        """Go to the last move.

        Args:
            interaction: Interaction of the operation.
            button: Button of the operation.
        """
        del button
        if interaction.user != self.user:
            return
        await interaction.response.defer()
        self.node = self.node.end()
        await self.sync(interaction)

    @ui.select(options=[], placeholder="Select the move", row=1)
    async def move(self, interaction: discord.Interaction, select: ui.Select):
        """Go to selected variation.

        Args:
            interaction: Interaction of the selection.
            select: Select menu of the selection.
        """
        if interaction.user != self.user:
            return
        await interaction.response.defer()
        move = self.node.board().parse_san(select.values[0])
        if self.node.has_variation(move):
            self.node = self.node.variation(move)
        await self.sync(interaction)


class GameCog(commands.Cog, name="Chessboard"):
    """Chess related commands.

    Attributes:
        bot: Bot that contains the cog.
    """

    def __init__(self, bot):
        """Initialize the cog."""
        self.bot = bot

    @commands.hybrid_command()
    async def chess(
        self,
        ctx: commands.Context[base.Bot],
        lvl: commands.Range[int, 0, 21],
        fst: typing.Optional[bool] = None,
    ):
        """Plays chess.

        Args:
            ctx: Context of the command.
            lvl: Strength of the opponent.
            fst: Whether to play first in game.
        """
        if fst is None:
            fst = bool(secrets.randbelow(2))
        view = ChessView(chess.Board(), fst, lvl, ctx=ctx)
        await view.make_move()
        fen = view.board.fen()
        view.msg = await ctx.send(
            f"`{fen}`",
            files=[
                discord.File(io.BytesIO(get_svg(view.board, fst)), "board.png"),
                discord.File(
                    io.BytesIO(bytes(str(view.get_pgn()), "utf-8")), "game.pgn"
                ),
            ],
            view=view,
            ephemeral=True,
        )

    @commands.hybrid_command()
    async def anlys(self, ctx: commands.Context[base.Bot], fen: str):
        """Asks for some analysis for chess.

        Args:
            ctx: Context of the command.
            fen: FEN of the game.
        """
        await ctx.defer()
        board = chess.Board(fen)
        _, stockfish = await engine.popen_uci(
            self.bot.cfg["feynmanium"]["cogs"]["game"]["path"]
        )
        info = await stockfish.analyse(board, engine.Limit(depth=20))
        await stockfish.quit()
        score: engine.Score
        try:
            score = info["score"].white()
        except RuntimeError:
            score = engine.Cp(0)
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
            result = str(round(score.score(mate_score=100) / 100, 2))
        await ctx.send(
            f"White has an advantage of {result} ({wdl}%).",
            file=discord.File(
                io.BytesIO(get_svg(board, board.turn)), "board.png"
            ),
            ephemeral=True,
        )

    @commands.hybrid_command()
    async def game(
        self, ctx: commands.Context[base.Bot], file: discord.Attachment
    ):
        """Read a PGN.

        Args:
            ctx: Context of the command.
            file: PGN of the game.
        """
        node = pgn.read_game(
            io.StringIO(str(await file.read(), encoding="utf-8"))
        )
        if node is None:
            await ctx.send("Invalid PGN.", ephemeral=True)
            return
        view = GameView(node, ctx=ctx)
        view.msg = await ctx.send(
            file=discord.File(
                io.BytesIO(get_svg(view.node.board(), view.node.turn())),
                "board.png",
            ),
            view=view,
            ephemeral=True,
        )


async def setup(bot: base.Bot):
    """Set up the extension.

    Args:
        bot: Bot that loads the extension.
    """
    await bot.add_cog(GameCog(bot), guilds=list(bot.glds))


async def teardown(bot: base.Bot):
    """Tear down the extension.

    Args:
        bot: Bot that unloads the extension.
    """
    await bot.remove_cog("Chessboard", guilds=list(bot.glds))
