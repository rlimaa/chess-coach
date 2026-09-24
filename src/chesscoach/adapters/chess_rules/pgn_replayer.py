import io

import chess
import chess.pgn

from chesscoach.application.dto import Ply, ReplayedGame
from chesscoach.application.errors import InvalidGameError
from chesscoach.domain.value_objects import Color


class PgnReplayer:
    def replay(self, pgn: str) -> ReplayedGame:
        game = chess.pgn.read_game(io.StringIO(pgn))
        if game is None or game.errors:
            raise InvalidGameError(f"Unreadable PGN: {game.errors if game else 'empty'}")

        board = game.board()
        plies: list[Ply] = []
        for index, node in enumerate(game.mainline()):
            plies.append(
                Ply(
                    index=index,
                    color=Color.WHITE if board.turn is chess.WHITE else Color.BLACK,
                    san=board.san(node.move),
                    uci=node.move.uci(),
                    fen_before=board.fen(),
                    clock_seconds=node.clock(),
                )
            )
            board.push(node.move)
        return ReplayedGame(plies=tuple(plies), final_fen=board.fen())
