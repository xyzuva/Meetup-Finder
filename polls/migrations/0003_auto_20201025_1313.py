# Generated by Django 3.1.1 on 2020-10-25 17:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0002_auto_20201025_1311'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comments',
            name='event_date',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name='comments',
            name='event_time',
            field=models.TimeField(null=True),
        ),
    ]