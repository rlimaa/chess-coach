import chess

from chesscoach.domain.value_objects import Color


class PythonChessRules:
    def normalize_move(self, fen: str, text: str) -> str | None:
        board = chess.Board(fen)
        text = text.strip()

        try:
            move = board.parse_san(text)
            return board.san(move)
        except ValueError:
            pass

        if text:
            try:
                move = board.parse_san(text[0].upper() + text[1:])
                return board.san(move)
            except ValueError:
                pass

        try:
            move = chess.Move.from_uci(text.lower())
            if move in board.legal_moves:
                return board.san(move)
        except ValueError:
            pass

        return None

    def render(self, fen: str, perspective: Color) -> str:
        board = chess.Board(fen)
        lines: list[str] = []

        if perspective == Color.WHITE:
            ranks = range(7, -1, -1)
            files = range(8)
        else:
            ranks = range(8)
            files = range(7, -1, -1)

        for rank in ranks:
            squares: list[str] = []
            for file in files:
                square = chess.Square(file + rank * 8)
                piece = board.piece_at(square)
                if piece:
                    squares.append(piece.unicode_symbol())
                else:
                    squares.append("·")
            line = f"{rank + 1} {' '.join(squares)}"
            lines.append(line)

        file_labels = "a b c d e f g h" if perspective == Color.WHITE else "h g f e d c b a"
        lines.append(f"  {file_labels}")

        return "\n".join(lines)
