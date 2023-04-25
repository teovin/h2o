# Generated by Django 3.2.18 on 2023-04-12 20:18

from django.db import migrations
from datetime import date


def add_courtlistener(apps, schema_editor):
    """Add CourtListener as a first-order type in the UI"""
    LegalDocumentSource = apps.get_model("main", "LegalDocumentSource")
    if not LegalDocumentSource.objects.filter(name="CourtListener"):
        LegalDocumentSource.objects.create(
            name="CourtListener",
            date_added=date.today(),
            last_updated=date.today(),
            active=False,
            priority=3,
            search_class="CourtListener",
            short_description="CourtListener searches millions of opinions across hundreds of jurisdictions.",
        )


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0044_add_user_groups"),
    ]

    operations = [
        migrations.RunPython(add_courtlistener),
    ]
