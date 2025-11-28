from django.db import migrations

def add_export_checkin_permission(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Event = apps.get_model('guests', 'Event')
    ct = ContentType.objects.get_for_model(Event)
    Permission.objects.get_or_create(
        codename='export_checkin',
        name='Can export check-in summary',
        content_type=ct,
    )

class Migration(migrations.Migration):
    dependencies = [
        ('guests', '0007_add_checkinlog_and_checkedincount'),
    ]
    operations = [
        migrations.RunPython(add_export_checkin_permission),
    ]
