# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_add_temperature_unit'),
    ]

    operations = [
        migrations.AddField(
            model_name='calendarevent',
            name='location',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='calendarevent',
            name='priority',
            field=models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium', max_length=10),
        ),
        migrations.AddField(
            model_name='calendarevent',
            name='reminder',
            field=models.BooleanField(default=False),
        ),
    ]