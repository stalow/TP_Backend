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


def migrate_reward_display_to_points(apps, schema_editor):
    JobOpening = apps.get_model("jobs", "JobOpening")

    for job in JobOpening.objects.all().iterator():
        points = _parse_points(job.reward_display)
        job.reward_points = points
        job.reward_display = _format_points(points)
        job.save(update_fields=["reward_points", "reward_display"])


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0004_jobopening_activity_sector_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobopening",
            name="reward_points",
            field=models.IntegerField(default=0, help_text="Récompense en points"),
        ),
        migrations.RunPython(migrate_reward_display_to_points, migrations.RunPython.noop),
    ]
