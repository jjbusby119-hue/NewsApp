from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Article, Newsletter, CustomUser


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'publisher', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise forms.ValidationError("Title must be at least 5 characters long")
        return title
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content) < 50:
            raise forms.ValidationError("Article content must be at least 50 characters")
        return content


class ArticleApprovalForm(forms.ModelForm):
    """Special form for editors to approve articles"""
    feedback = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Optional feedback for the author"
    )
    
    class Meta:
        model = Article
        fields = ['approved']
        widgets = {
            'approved': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = ['title', 'description', 'articles']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'articles': forms.CheckboxSelectMultiple(),
        }


class CustomUserCreationForm(UserCreationForm):
    """Form for user registration/signup"""
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Select your role in the news platform'
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style password fields
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class CustomLoginForm(forms.Form):
    """Custom login form"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    class Meta:
        model = CustomUser
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
