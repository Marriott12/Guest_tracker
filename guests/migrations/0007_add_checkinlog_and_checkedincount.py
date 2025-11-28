from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('guests', '0006_guest_can_login_guest_last_login_guest_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='checked_in_count',
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name='CheckInLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('checked_in_at', models.DateTimeField(auto_now_add=True)),
                ('table_number', models.CharField(blank=True, max_length=50)),
                ('seat_number', models.CharField(blank=True, max_length=50)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checkin_logs', to='guests.event')),
                ('invitation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checkin_logs', to='guests.invitation')),
                ('guest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checkin_logs', to='guests.guest')),
                ('checked_in_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
            options={
                'ordering': ['-checked_in_at'],
            },
        ),
    ]
