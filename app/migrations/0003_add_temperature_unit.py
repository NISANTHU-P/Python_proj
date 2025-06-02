# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_calendarevent'),  # Make sure this matches your last migration
    ]

    operations = [
        migrations.AddField(
            model_name='userpreference',
            name='temperature_unit',
            field=models.CharField(choices=[('C', 'Celsius'), ('F', 'Fahrenheit')], default='C', max_length=1),
        ),
    ]
