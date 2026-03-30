import re

from django.db import migrations, models


def _parse_points(raw_value: str | None) -> int:
    if not raw_value:
        return 0
    digits = re.sub(r"[^0-9]", "", raw_value)
    if not digits:
        return 0
    try:
        return int(digits)
    except (TypeError, ValueError):
        return 0


def _format_points(points: int) -> str:
    return f"{points:,} Points".replace(",", "'")


def migrate_reward_snapshot_to_points(apps, schema_editor):
    RewardOutcome = apps.get_model("referrals", "RewardOutcome")

    for reward in RewardOutcome.objects.select_related("referral__job_opening").all().iterator():
        points = _parse_points(reward.reward_display_snapshot)
        if points == 0 and reward.referral_id and reward.referral.job_opening_id:
            points = getattr(reward.referral.job_opening, "reward_points", 0) or 0

        reward.reward_points = points
        reward.reward_display_snapshot = _format_points(points)
        reward.save(update_fields=["reward_points", "reward_display_snapshot"])


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0005_jobopening_reward_points"),
        ("referrals", "0004_alter_referral_status_candidateconsenttoken"),
    ]

    operations = [
        migrations.AddField(
            model_name="rewardoutcome",
            name="reward_points",
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(migrate_reward_snapshot_to_points, migrations.RunPython.noop),
    ]
