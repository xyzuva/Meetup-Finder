# Generated by Django 3.1.1 on 2020-11-05 04:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('meetup_finder', '0003_response'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='events',
            options={'permissions': (('permission_code', 'Friendly permission description'),)},
        ),
    ]
