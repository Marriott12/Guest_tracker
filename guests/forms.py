from django import forms
from .models import RSVP, Guest, Event, EmailTemplate
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User

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
        label="📧 Send invitation email immediately after saving",
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    event = forms.ModelChoiceField(
        queryset=Event.objects.all(),
        required=False,
        label="Add to Event (Optional)",
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select an event to add this guest to and optionally send invitation"
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
    
    # Override JSON fields with proper help text
    program_schedule = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '{"items": [{"time": "10:00 AM", "activity": "Opening Ceremony", "description": "Welcome speech"}]}'
        }),
        help_text='Enter as JSON format. Example: {"items": [{"time": "10:00 AM", "activity": "Opening Ceremony", "description": "Welcome speech"}]}',
        label='Program Schedule (JSON)'
    )
    
    menu = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '{"courses": [{"name": "Appetizer", "items": ["Salad", "Soup"]}]}'
        }),
        help_text='Enter as JSON format. Example: {"courses": [{"name": "Appetizer", "items": ["Salad", "Soup"]}]}',
        label='Menu (JSON)'
    )
    
    seating_arrangement = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '{"tables": [{"number": "1", "capacity": 8, "section": "VIP"}]}'
        }),
        help_text='Enter seating details as JSON. Example: {"tables": [{"number": "1", "capacity": 8, "section": "VIP"}]}',
        label='Seating Arrangement (JSON)'
    )
    
    class Meta:
        model = Event
        fields = ['name', 'description', 'date', 'location', 'rsvp_deadline', 'max_guests', 
                  'dress_code', 'parking_info', 'special_instructions', 'program_schedule', 
                  'menu', 'seating_arrangement', 'has_assigned_seating', 'contact_person', 
                  'contact_phone', 'contact_email', 'event_banner']
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
            'dress_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Formal, Military Uniform'}),
            'parking_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'has_assigned_seating': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'event_banner': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_program_schedule(self):
        """Validate and parse program schedule JSON"""
        import json
        data = self.cleaned_data.get('program_schedule', '')
        if not data or data.strip() == '':
            return {}
        try:
            parsed = json.loads(data)
            return parsed
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f'Invalid JSON format for program schedule: {str(e)}')
    
    def clean_menu(self):
        """Validate and parse menu JSON"""
        import json
        data = self.cleaned_data.get('menu', '')
        if not data or data.strip() == '':
            return {}
        try:
            parsed = json.loads(data)
            return parsed
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f'Invalid JSON format for menu: {str(e)}')
    
    def clean_seating_arrangement(self):
        """Validate and parse seating arrangement JSON"""
        import json
        data = self.cleaned_data.get('seating_arrangement', '')
        if not data or data.strip() == '':
            return {}
        try:
            parsed = json.loads(data)
            return parsed
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f'Invalid JSON format for seating arrangement: {str(e)}')

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

class GuestProfileForm(forms.ModelForm):
    """Form for guests to edit their own profile"""
    
    class Meta:
        model = Guest
        fields = ['first_name', 'last_name', 'email', 'phone', 'address']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class UserProfileForm(forms.ModelForm):
    """Form for admins/organizers to edit their profile"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class GuestRegistrationForm(UserCreationForm):
    """Form for guests to create their own account"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'})
    )
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Create associated Guest profile
            Guest.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                phone=self.cleaned_data.get('phone', ''),
                can_login=True
            )
        
        return user
