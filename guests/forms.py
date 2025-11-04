from django import forms
from .models import RSVP, Guest, Event, EmailTemplate

class RSVPForm(forms.ModelForm):
    """Form for guests to respond to invitations"""
    
    class Meta:
        model = RSVP
        fields = ['response', 'plus_ones', 'dietary_restrictions', 'special_requests']
        widgets = {
            'response': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'plus_ones': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '10',
                'placeholder': '0'
            }),
            'dietary_restrictions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Please list any dietary restrictions or allergies...'
            }),
            'special_requests': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any special requests or comments...'
            }),
        }
        labels = {
            'response': 'Will you be attending?',
            'plus_ones': 'Number of additional guests',
            'dietary_restrictions': 'Dietary restrictions or allergies',
            'special_requests': 'Special requests or comments',
        }

class GuestForm(forms.ModelForm):
    """Form for adding new guests"""
    send_invitation = forms.BooleanField(
        required=False,
        label="Send invitation email immediately (if adding to an event)",
        initial=True
    )
    
    class Meta:
        model = Guest
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'notes']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class EventForm(forms.ModelForm):
    """Form for creating/editing events"""
    
    class Meta:
        model = Event
        fields = ['name', 'description', 'date', 'location', 'rsvp_deadline', 'max_guests']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'rsvp_deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'max_guests': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }

class BulkInviteForm(forms.Form):
    """Form for bulk inviting guests to an event"""
    guests = forms.ModelMultipleChoiceField(
        queryset=Guest.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        
        if event:
            # Exclude guests who are already invited to this event
            already_invited = event.invitations.values_list('guest_id', flat=True)
            self.fields['guests'].queryset = Guest.objects.exclude(id__in=already_invited)

class EmailTemplateForm(forms.ModelForm):
    """Form for creating email templates"""
    
    class Meta:
        model = EmailTemplate
        fields = ['name', 'template_type', 'subject', 'html_content', 'text_content']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'template_type': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'html_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'text_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        }

class BulkEmailForm(forms.Form):
    """Form for sending bulk emails"""
    SEND_TO_CHOICES = [
        ('all', 'All Invitees'),
        ('pending', 'Pending Responses Only'),
        ('confirmed', 'Confirmed Attendees Only'),
        ('declined', 'Declined Attendees Only'),
    ]
    
    event = forms.ModelChoiceField(
        queryset=Event.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    template = forms.ModelChoiceField(
        queryset=EmailTemplate.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        empty_label="Use Default Template"
    )
    
    send_to = forms.ChoiceField(
        choices=SEND_TO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='pending'
    )
    
    include_qr_code = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Include QR Code in email'
    )
