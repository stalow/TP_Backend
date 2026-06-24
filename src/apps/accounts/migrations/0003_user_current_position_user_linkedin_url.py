from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_expertise_areas_user_network_cities_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='current_position',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='user',
            name='linkedin_url',
            field=models.URLField(blank=True),
        ),
    ]
