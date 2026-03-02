from django import forms
from .models import Job


class JobForm(forms.ModelForm):
    """Form for creating and editing job postings"""
    
    class Meta:
        model = Job
        fields = ['title', 'description', 'budget', 'deadline', 'required_freelancers']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter job title',
                'maxlength': '200'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe the job requirements, skills needed, and deliverables...',
                'rows': '6'
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter budget amount',
                'step': '0.01',
                'min': '0'
            }),
            'deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'required_freelancers': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of freelancers needed',
                'min': '1',
                'value': '1'
            }),
        }
        labels = {
            'title': 'Job Title',
            'description': 'Job Description',
            'budget': 'Budget ($)',
            'deadline': 'Deadline',
            'required_freelancers': 'Required Freelancers'
        }
    
    def clean_deadline(self):
        """Validate that deadline is not in the past"""
        deadline = self.cleaned_data.get('deadline')
        if deadline:
            from django.utils import timezone
            if deadline < timezone.now().date():
                raise forms.ValidationError("Deadline cannot be in the past.")
        return deadline
    
    def clean_budget(self):
        """Validate that budget is positive"""
        budget = self.cleaned_data.get('budget')
        if budget and budget <= 0:
            raise forms.ValidationError("Budget must be greater than zero.")
        return budget
    
    def clean_required_freelancers(self):
        """Validate that required_freelancers is at least 1"""
        required_freelancers = self.cleaned_data.get('required_freelancers')
        if required_freelancers and required_freelancers < 1:
            raise forms.ValidationError("At least one freelancer is required.")
        return required_freelancers
