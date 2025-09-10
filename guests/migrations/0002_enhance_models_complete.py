# Generated manually for enhanced features

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guests', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Create EventCategory model
        migrations.CreateModel(
            name='EventCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('color', models.CharField(default='#007bff', help_text='Hex color code', max_length=7)),
                ('icon', models.CharField(default='fas fa-calendar', help_text='Font Awesome icon class', max_length=50)),
            ],
            options={
                'verbose_name_plural': 'Event Categories',
            },
        ),
        
        # Create EventTemplate model
        migrations.CreateModel(
            name='EventTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('default_location', models.CharField(blank=True, max_length=300)),
                ('default_max_guests', models.IntegerField(blank=True, null=True)),
                ('default_rsvp_deadline_days', models.IntegerField(default=7, help_text='Days before event for RSVP deadline')),
                ('email_template', models.TextField(blank=True, help_text='Default invitation email template')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='guests.eventcategory')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_templates', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        
        # Add fields to Invitation model
        migrations.AddField(
            model_name='invitation',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('sent', 'Sent'), ('opened', 'Opened'), ('responded', 'Responded')], default='draft', max_length=20),
        ),
        migrations.AddField(
            model_name='invitation',
            name='opened_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='invitation',
            name='qr_code',
            field=models.ImageField(blank=True, null=True, upload_to='qr_codes/'),
        ),
        migrations.AddField(
            model_name='invitation',
            name='personal_message',
            field=models.TextField(blank=True, help_text='Personal message for this guest'),
        ),
        
        # Create GuestProfile model
        migrations.CreateModel(
            name='GuestProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='guest_photos/')),
                ('company', models.CharField(blank=True, max_length=200)),
                ('job_title', models.CharField(blank=True, max_length=200)),
                ('website', models.URLField(blank=True)),
                ('social_media', models.JSONField(blank=True, default=dict)),
                ('dietary_preferences', models.TextField(blank=True)),
                ('accessibility_needs', models.TextField(blank=True)),
                ('emergency_contact', models.CharField(blank=True, max_length=200)),
                ('emergency_phone', models.CharField(blank=True, max_length=20)),
                ('preferred_contact_method', models.CharField(choices=[('email', 'Email'), ('phone', 'Phone'), ('sms', 'SMS')], default='email', max_length=20)),
                ('subscribe_newsletter', models.BooleanField(default=False)),
                ('allow_marketing', models.BooleanField(default=False)),
                ('vip_status', models.BooleanField(default=False)),
                ('blacklisted', models.BooleanField(default=False)),
                ('tags', models.CharField(blank=True, help_text='Comma-separated tags', max_length=500)),
                ('guest', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to='guests.guest')),
            ],
        ),
        
        # Create EventAnalytics model
        migrations.CreateModel(
            name='EventAnalytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('emails_sent', models.IntegerField(default=0)),
                ('emails_opened', models.IntegerField(default=0)),
                ('emails_clicked', models.IntegerField(default=0)),
                ('emails_bounced', models.IntegerField(default=0)),
                ('total_responses', models.IntegerField(default=0)),
                ('yes_responses', models.IntegerField(default=0)),
                ('no_responses', models.IntegerField(default=0)),
                ('maybe_responses', models.IntegerField(default=0)),
                ('page_views', models.IntegerField(default=0)),
                ('unique_visitors', models.IntegerField(default=0)),
                ('average_response_time', models.DurationField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('event', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='analytics', to='guests.event')),
            ],
        ),
        
        # Create EmailTemplate model
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('template_type', models.CharField(choices=[('invitation', 'Invitation'), ('reminder', 'Reminder'), ('confirmation', 'Confirmation'), ('update', 'Event Update'), ('thank_you', 'Thank You')], max_length=20)),
                ('subject', models.CharField(max_length=200)),
                ('html_content', models.TextField()),
                ('text_content', models.TextField()),
                ('is_default', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['template_type', 'name'],
            },
        ),
        
        # Create EventWaitlist model
        migrations.CreateModel(
            name='EventWaitlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.IntegerField()),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('notified', models.BooleanField(default=False)),
                ('invitation_sent', models.BooleanField(default=False)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='waitlist', to='guests.event')),
                ('guest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='guests.guest')),
            ],
            options={
                'ordering': ['position'],
                'unique_together': {('event', 'guest')},
            },
        ),
    ]
