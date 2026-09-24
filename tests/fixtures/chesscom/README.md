# Chess.com Test Fixtures

## Source Data

**Date Recorded:** 2026-09-24

**Source URLs Fetched:**
- https://api.chess.com/pub/player/rodigola/games/archives (archives list)
- https://api.chess.com/pub/player/rodigola/games/2026/09 (September 2026 games)
- https://api.chess.com/pub/player/rodigola/games/2026/08 (August 2026 games)

## Games in month.json

| Index | UUID | Time Class | Rules | Rodigola Color | White Result | Black Result | Has Accuracies |
|-------|------|-----------|-------|----------------|--------------|--------------|----------------|
| 1 | b46c5d39-a70d-11f1-8acf-f45fe701000f | blitz | chess | white | win | resigned | no |
| 2 | 4cb8f688-a65f-11f1-8b87-51b40001000f | blitz | chess | black | resigned | win | no |
| 3 | 0564d1c3-94e9-11f1-b5d5-5f0b4701000f | rapid | chess | black | win | checkmated | no |
| 4 | a682b5f0-a0d8-11f1-b84c-1d1f5901000f | bullet | chess | white | win | timeout | no |
| 5 | 99db860c-8c28-11f1-a0d5-0b503501000b | daily | chess | white | win | resigned | yes |
| 6 | 4540010c-a194-11f1-b4a6-d9079701000f | rapid | chess | white | win | checkmated | yes |

## Coverage Notes

The 6 selected games cover:
- **(a) White win:** Games 1, 4, 5, 6 (rodigola plays white and wins)
- **(b) Black loss:** Games 2, 3 (rodigola plays black and loses)
- **(c) Draw:** No draws found in available data (September, August 2026)
- **(d) Accuracies:** Games 5 and 6 have accuracies; games 1-4 without
- **(e) Time classes:** Blitz (games 1-2), Rapid (games 3, 6), Bullet (game 4), Daily (game 5)
- **Variant games:** No non-standard variants (rules != "chess") found in available data

All games include complete PGN notation.
