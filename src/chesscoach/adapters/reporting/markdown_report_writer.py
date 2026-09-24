from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path

from chesscoach.domain.insights import Highlight, TimeClassInsights
from chesscoach.domain.services.statistics import ResultSummary


class MarkdownReportWriter:
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
