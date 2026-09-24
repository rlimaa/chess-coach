from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path

from chesscoach.domain.insights import (
    Conversion,
    EngineInsights,
    Highlight,
    MomentRef,
    TimeClassInsights,
    TimePressureErrors,
)
from chesscoach.domain.services.statistics import ResultSummary


class MarkdownReportWriter:
    _MAX_MOMENTS_PER_LIST = 10

    def __init__(self, reports_dir: Path, today: Callable[[], date] = date.today) -> None:
        self._reports_dir = reports_dir
        self._today = today

    def write(
        self,
        username: str,
        insights: TimeClassInsights,
        highlights: Sequence[Highlight],
    ) -> str:
        self._reports_dir.mkdir(parents=True, exist_ok=True)
        today = self._today()
        time_class_value = insights.time_class.value
        filename = f"{today.isoformat()}-{time_class_value}.md"
        filepath = self._reports_dir / filename

        lines: list[str] = []
        lines.append(f"# {username} · {time_class_value} coaching report ({today.isoformat()})")
        lines.append("")

        overall = insights.overall
        lines.append(f"{overall.games} games · score {overall.score_pct:.1f}%")
        lines.append("")

        weaknesses = [h for h in highlights if not h.strength]
        strengths = [h for h in highlights if h.strength]

        lines.append("## Work on")
        if weaknesses:
            for h in weaknesses:
                lines.append(f"- {h.text}")
        else:
            lines.append("- Nothing stands out.")
        lines.append("")

        lines.append("## Keep doing")
        if strengths:
            for h in strengths:
                lines.append(f"- {h.text}")
        else:
            lines.append("- Nothing stands out yet.")
        lines.append("")

        lines.extend(self._openings_section(insights))
        lines.extend(self._how_games_end_section(insights))
        lines.extend(self._clock_section(insights))
        lines.extend(self._habits_section(insights))
        lines.extend(self._opponents_section(insights))
        lines.extend(self._rating_by_month_section(insights))
        lines.extend(self._engine_section(insights))

        content = "\n".join(lines) + "\n"
        filepath.write_text(content)
        return str(filepath)

    def _format_summary(self, summary: ResultSummary) -> str:
        w_d_l = f"{summary.wins}/{summary.draws}/{summary.losses}"
        return f"{summary.games} | {w_d_l} | {summary.score_pct:.1f}%"

    def _openings_section(self, insights: TimeClassInsights) -> list[str]:
        lines = [
            "## Openings",
            "| Color | Opening | Games | W/D/L | Score |",
            "|---|---|---|---|---|",
        ]
        for opening in insights.openings:
            lines.append(
                f"| {opening.color.value} | {opening.family} | "
                f"{self._format_summary(opening.summary)} |"
            )
        lines.append("")
        return lines

    def _how_games_end_section(self, insights: TimeClassInsights) -> list[str]:
        lines = ["## How games end"]

        lines.append("| Lost by | Games |")
        lines.append("|---|---|")
        for termination, count in insights.losses_by_termination.items():
            lines.append(f"| {termination} | {count} |")
        lines.append("")

        lines.append("| Won by | Games |")
        lines.append("|---|---|")
        for termination, count in insights.wins_by_termination.items():
            lines.append(f"| {termination} | {count} |")
        lines.append("")

        return lines

    def _clock_section(self, insights: TimeClassInsights) -> list[str]:
        lines = ["## Clock"]

        if insights.clock is None:
            lines.append("No clock data.")
        else:
            clock = insights.clock
            lines.append("| | Games | W/D/L | Score |")
            lines.append("|---|---|---|---|")
            lines.append(
                f"| In time trouble (<10% clock) | {self._format_summary(clock.in_trouble)} |"
            )
            lines.append(f"| Otherwise | {self._format_summary(clock.not_in_trouble)} |")
            lines.append(f"Losses on time: {clock.losses_on_time} of {clock.losses}")

        lines.append("")
        return lines

    def _habits_section(self, insights: TimeClassInsights) -> list[str]:
        lines = ["## Habits"]

        lines.append("| | Games | W/D/L | Score |")
        lines.append("|---|---|---|---|")
        lines.append(
            f"| First game of a sitting | {self._format_summary(insights.streaks.fresh)} |"
        )
        lines.append(f"| After a win | {self._format_summary(insights.streaks.after_win)} |")
        lines.append(f"| After a loss | {self._format_summary(insights.streaks.after_loss)} |")
        lines.append(
            f"| After 2+ losses | {self._format_summary(insights.streaks.after_two_plus_losses)} |"
        )
        lines.append("")

        if insights.by_session_position:
            lines.append("| | Games | W/D/L | Score |")
            lines.append("|---|---|---|---|")
            for item in insights.by_session_position:
                lines.append(f"| {item.label} | {self._format_summary(item.summary)} |")
            lines.append("")

        if insights.by_day_part:
            lines.append("| | Games | W/D/L | Score |")
            lines.append("|---|---|---|---|")
            for day_part, summary in insights.by_day_part.items():
                lines.append(f"| {day_part.value} | {self._format_summary(summary)} |")
            lines.append("")

        if insights.by_weekday:
            lines.append("| | Games | W/D/L | Score |")
            lines.append("|---|---|---|---|")
            for item in insights.by_weekday:
                lines.append(f"| {item.label} | {self._format_summary(item.summary)} |")
            lines.append("")

        return lines

    def _opponents_section(self, insights: TimeClassInsights) -> list[str]:
        lines = [
            "## Opponents",
            "| Opponent | Games | W/D/L | Score | Expected |",
            "|---|---|---|---|---|",
        ]
        for bucket in insights.by_rating_gap:
            games = bucket.summary.games
            w_d_l = f"{bucket.summary.wins}/{bucket.summary.draws}/{bucket.summary.losses}"
            score = f"{bucket.summary.score_pct:.1f}%"
            expected = f"{bucket.expected_score_pct:.1f}%"
            lines.append(f"| {bucket.label} | {games} | {w_d_l} | {score} | {expected} |")
        lines.append("")
        return lines

    def _rating_by_month_section(self, insights: TimeClassInsights) -> list[str]:
        lines = ["## Rating by month", "| Month | Rating | Games |", "|---|---|---|"]
        for month_rating in insights.rating_by_month:
            month_str = f"{month_rating.year}-{month_rating.month:02d}"
            lines.append(f"| {month_str} | {month_rating.rating} | {month_rating.games} |")
        lines.append("")
        return lines

    def _engine_section(self, insights: TimeClassInsights) -> list[str]:
        lines = ["## Engine analysis"]

        if insights.engine is None:
            analyzed = insights.analyzed_games
            msg = (
                f"{analyzed} games analyzed so far; engine findings need at least 20. "
                "The nightly job adds more."
            )
            lines.append(msg)
            lines.append("")
            return lines

        engine = insights.engine
        lines.append(self._engine_accuracy_line(engine))
        lines.append("")
        lines.extend(self._engine_phase_table(engine))
        if engine.time_pressure is not None:
            lines.append(self._engine_time_pressure_line(engine.time_pressure))
            lines.append("")
        lines.append(self._engine_conversion_line(engine.conversion))
        lines.append("")
        lines.append(self._engine_punished_line(engine))
        lines.append("")
        self._add_moment_list(lines, "Missed mates", engine.missed_mates)
        self._add_moment_list(lines, "Unpunished blunders", engine.unpunished)
        self._add_moment_list(lines, "Thrown winning positions", engine.conversion.thrown)

        return lines

    def _engine_accuracy_line(self, engine: EngineInsights) -> str:
        accuracy_str = f"{engine.accuracy:.1f}%" if engine.accuracy is not None else "-"
        opponent_accuracy_str = (
            f"{engine.opponent_accuracy:.1f}%" if engine.opponent_accuracy is not None else "-"
        )
        return (
            f"{engine.games} analyzed games · accuracy {accuracy_str} "
            f"(opponents {opponent_accuracy_str})"
        )

    def _engine_phase_table(self, engine: EngineInsights) -> list[str]:
        header = (
            "| Phase | Your moves | Avg win % lost | Inaccuracies | "
            "Mistakes | Blunders | Serious per 100 |"
        )
        lines = [header, "|---|---|---|---|---|---|---|"]
        for phase_errors in engine.by_phase:
            phase_name = phase_errors.phase.value.lower()
            serious_per_100 = f"{phase_errors.serious_per_100:.1f}"
            row = (
                f"| {phase_name} | {phase_errors.moves} | "
                f"{phase_errors.avg_win_pct_loss:.2f} | {phase_errors.inaccuracies} | "
                f"{phase_errors.mistakes} | {phase_errors.blunders} | {serious_per_100} |"
            )
            lines.append(row)
        lines.append("")
        return lines

    def _engine_time_pressure_line(self, time_pressure: TimePressureErrors) -> str:
        low_rate = time_pressure.low_rate
        normal_rate = time_pressure.normal_rate
        return (
            f"Under 10% of the clock: {low_rate:.1f}% of moves are mistakes "
            f"or blunders ({normal_rate:.1f}% otherwise)."
        )

    def _engine_conversion_line(self, conversion: Conversion) -> str:
        return (
            f"Converted {conversion.converted} of {conversion.winning_games} "
            f"clearly winning positions ({conversion.rate:.1f}%)."
        )

    def _engine_punished_line(self, engine: EngineInsights) -> str:
        punished_count = engine.punish_opportunities - len(engine.unpunished)
        return f"Opponent blunders punished: {punished_count} of {engine.punish_opportunities}."

    def _add_moment_list(
        self, lines: list[str], heading: str, moments: tuple[MomentRef, ...]
    ) -> None:
        if moments:
            lines.append(f"### {heading}")
            for i, moment in enumerate(moments):
                if i >= self._MAX_MOMENTS_PER_LIST:
                    break
                move_label = self._format_move_label(moment.ply)
                best_move = moment.best_move_san or "-"
                lines.append(
                    f"- [move {move_label}]({moment.game_url}) {moment.san}, best {best_move}"
                )
            lines.append("")

    def _format_move_label(self, ply: int) -> str:
        if ply % 2 == 0:
            return str(ply // 2 + 1)
        return f"{ply // 2 + 1}..."
