# Generated by Django 2.2.16 on 2020-10-13 12:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0069_auto_20201013_1237'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='TempCollaborator',
            new_name='ContentCollaborator',
        ),
    ]