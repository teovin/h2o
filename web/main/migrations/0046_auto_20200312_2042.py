# Generated by Django 2.2.10 on 2020-03-12 20:42

import django.contrib.postgres.fields
from django.db import migrations, models
from main.models import Casebook, ContentNode, TempCollaborator, ContentCollaborator

def migrate_casebooks(app,schema):
    print("About to update anything")
    bulk_collaborators = []
    draft_map = {}
    all_map = {}
    for original_casebook in ContentNode.objects.filter(casebook_id__isnull=True).all():
        new_casebook = Casebook(title = original_casebook.title,
                                subtitle = original_casebook.subtitle,
                                headnote = original_casebook.headnote,
                                old_casebook = original_casebook
        )
        if original_casebook.public:
            new_casebook.state = Casebook.LifeCycle.PUBLISHED.value
        else:
            if original_casebook.draft_mode_of_published_casebook:
                new_casebook.state = Casebook.LifeCycle.DRAFT.value
            elif original_casebook.provenance:
                new_casebook.state = Casebook.LifeCycle.NEWLY_CLONED.value
            else:
                new_casebook.state = Casebook.LifeCycle.PRIVATELY_EDITING.value
        new_casebook.save()
        if original_casebook.draft_mode_of_published_casebook:
            drafted_casebook = original_casebook.provenance[-1]
            draft_map[drafted_casebook] = new_casebook
        new_collaborators = [TempCollaborator(has_attribution= old_collaborator.has_attribution,
                                              can_edit= old_collaborator.can_edit,
                                              user=old_collaborator.user,
                                              casebook=new_casebook)
                             for old_collaborator in ContentCollaborator.objects.filter(content=original_casebook).all()]
        all_map[original_casebook.id] = new_casebook
        bulk_collaborators += new_collaborators
    for draft_id, target in draft_map.items():
        drafted = all_map[draft_id]
        drafted.draft = target
        drafted.save()
    TempCollaborator.objects.bulk_create(bulk_collaborators)
    bulk_content = []
    print("About to update contents")
    for content_node in ContentNode.objects.filter(casebook_id__isnull=False).select_related('casebook').all():
        content_node.new_casebook = all_map[content_node.casebook.id]
        bulk_content.append(content_node)
    ContentNode.objects.bulk_update(bulk_content, fields=['new_casebook'], batch_size=1000)


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0045_contentnode_new_casebook'),
    ]

    operations = [
        migrations.AddField(
            model_name='casebook',
            name='provenance',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.BigIntegerField(), default=list, size=None),
        ),
        migrations.RunPython(migrate_casebooks,migrations.RunPython.noop),
    ]