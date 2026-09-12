"""Position-based win rates, independently of currency and profit magnitude."""
from .journal import assess_exit


def exit_category(position):
    assessment = position.get("exit_assessment") or assess_exit(position)
    if assessment.get("source") == "default_rule":
        return "unknown"
    reason = assessment["reason"]
    return reason if reason in {"take", "stop", "manual", "mixed"} else "unknown"


def win_rates(positions, wins, takes, stops):
    return {
        "win_rate": wins / positions * 100 if positions else None,
        "clean_win_rate": takes / (takes + stops) * 100 if takes + stops else None,
    }
