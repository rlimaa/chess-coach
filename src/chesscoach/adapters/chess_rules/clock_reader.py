import re

# Regex instead of full PGN parsing: reports read clocks from thousands of games.
_CLOCK = re.compile(r"\[%clk (\d+):(\d{2}):(\d{2}(?:\.\d+)?)\]")


class PgnClockReader:
    def clocks(self, pgn: str) -> list[float]:
        return [int(h) * 3600 + int(m) * 60 + float(s) for h, m, s in _CLOCK.findall(pgn)]
