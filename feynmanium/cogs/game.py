"""Commands related to chess."""
import datetime
import io
import secrets
import typing

import cairosvg
import chess
import discord
from chess import engine, pgn, svg
from discord import app_commands, ui
from discord.ext import commands  # type: ignore[attr-defined]

from .. import base

config = base.config
dummy = [discord.SelectOption(label="dummy")]


async def get_move(board: chess.Board, level: int) -> chess.Move:
    """Get the next move."""
    if level == 0:
        return secrets.choice(list(board.legal_moves))
    _, stockfish = await engine.popen_uci(base.sf_path)
    result = await stockfish.play(
        board, chess.engine.Limit(depth=16), options={"Skill Level": level - 1}
    )
    await stockfish.quit()
    if result.move is not None:
        return result.move
    return chess.Move.null()


def get_svg(board: chess.Board, color: chess.Color) -> str:
    """Get the SVG of the board."""
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
        super().__init__(timeout=timeout)
        self.user, self.message = user, None
        self.board, self.color, self.level = board, color, level

    def get_pgn(self) -> pgn.Game:
        """Get the PGN of the game."""
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
        """Update the options after selecting a source."""
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
        """Update the options after selecting a target."""
        if self.board.is_game_over():
            self.src.options = dummy
            self.src.disabled = True
        else:
            self.update_src("")
        self.dest.options = dummy
        self.dest.disabled = True

    async def make_move(self):
        """Make a move."""
        if not self.board.is_game_over() and self.board.turn != self.color:
            self.board.push(await get_move(self.board, self.level))

    async def on_timeout(self):
        """Disable all items on timeout."""
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

    @ui.select(options=dummy, placeholder="Select the source square", row=0)
    async def src(self, interaction: discord.Interaction, select: ui.Select):
        """Select the source square."""
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
        """Select the target square."""
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


class GameView(ui.View):
    """View for game."""

    def __init__(
        self,
        node: pgn.GameNode,
        *,
        user: discord.User,
        timeout: typing.Optional[float] = 300,
    ):
        """Initialize the view."""
        super().__init__(timeout=timeout)
        self.user, self.message = user, None
        self.node = node
        self.update()

    def update(self):
        """Update item availability."""
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
            self.move.options = dummy
            self.move.disabled = True

    async def sync(self, interaction: discord.Interaction):
        """Sync the view."""
        self.update()
        await interaction.edit_original_message(
            attachments=[
                discord.File(
                    io.BytesIO(
                        cairosvg.svg2png(
                            get_svg(self.node.board(), self.node.turn())
                        )
                    ),
                    "board.png",
                )
            ],
            view=self,
        )

    async def on_timeout(self):
        """Disable all items on timeout."""
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

    @ui.button(label="<<", style=discord.ButtonStyle.primary, row=0)
    async def root(self, interaction: discord.Interaction, button: ui.Button):
        """Go to the first move."""
        del button
        if interaction.user != self.user:
            return
        await interaction.response.defer()
        self.node = self.node.game()
        await self.sync(interaction)

    @ui.button(label="<", row=0)
    async def prev(self, interaction: discord.Interaction, button: ui.Button):
        """Go to the last move."""
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
        """Go to the main variation."""
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
        """Go to the next move."""
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
        """Go to the last move."""
        del button
        if interaction.user != self.user:
            return
        await interaction.response.defer()
        self.node = self.node.end()
        await self.sync(interaction)

    @ui.select(options=dummy, placeholder="Select the move", row=1)
    async def move(self, interaction: discord.Interaction, select: ui.Select):
        """Go to selected variation."""
        if interaction.user != self.user:
            return
        await interaction.response.defer()
        move = self.node.board().parse_san(select.values[0])
        if self.node.has_variation(move):
            self.node = self.node.variation(move)
        await self.sync(interaction)


class GameCog(  # type: ignore[call-arg]
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
        """Play chess."""
        if fst is None:
            fst = bool(secrets.randbelow(2))
        view = ChessView(chess.Board(), fst, lvl, user=ctx.author)
        await view.make_move()
        view.update_dest()
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
        """Get some analysis for chess."""
        await ctx.defer()
        board = chess.Board(fen)
        _, stockfish = await engine.popen_uci(base.sf_path)
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
            result = str(round(score.score() / 100, 2))
        await ctx.send(
            f"White has an advantage of {result} ({wdl}%).",
            file=discord.File(
                io.BytesIO(cairosvg.svg2png(get_svg(board, board.turn))),
                "board.png",
            ),
        )

    @commands.hybrid_command(
        name=config["game"]["game"]["name"],
        enabled=config["game"]["game"]["enbl"],
        hidden=config["game"]["game"]["hide"],
        help=config["game"]["game"]["desc"],
    )
    @app_commands.guilds(*config["game"]["glds"])
    async def game(self, ctx: commands.Context, file: discord.Attachment):
        """Read a PGN."""
        node = pgn.read_game(
            io.StringIO(str(await file.read(), encoding="utf-8"))
        )
        view = GameView(node, user=ctx.author)
        view.message = await ctx.send(
            file=discord.File(
                io.BytesIO(
                    cairosvg.svg2png(
                        get_svg(view.node.board(), view.node.turn())
                    )
                ),
                "board.png",
            ),
            view=view,
        )


async def setup(bot):
    """Set up the extension."""
    await bot.add_cog(GameCog(bot))
