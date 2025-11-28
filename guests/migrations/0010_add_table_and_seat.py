from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('guests', '0009_add_guest_rank_institution'),
    ]

    operations = [
        migrations.CreateModel(
            name='Table',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=50)),
                ('capacity', models.IntegerField(default=0)),
                ('section', models.CharField(blank=True, max_length=100)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tables', to='guests.Event')),
            ],
            options={'unique_together': {('event', 'number')},},
        ),
        migrations.CreateModel(
            name='Seat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=50)),
                ('assigned_invitation', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_seat', to='guests.Invitation')),
                ('table', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seats', to='guests.Table')),
            ],
            options={'unique_together': {('table', 'number')},},
        ),
    ]
