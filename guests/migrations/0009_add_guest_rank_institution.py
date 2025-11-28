from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guests', '0008_add_export_checkin_permission'),
    ]

    operations = [
        migrations.AddField(
            model_name='guest',
            name='rank',
            field=models.CharField(blank=True, help_text='Military or professional rank/title', max_length=100),
        ),
        migrations.AddField(
            model_name='guest',
            name='institution',
            field=models.CharField(blank=True, help_text='Institution or unit (e.g., Army Division)', max_length=200),
        ),
    ]
