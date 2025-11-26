# mailapp/forms.py
from django import forms

class EmailForm(forms.Form):
    recipient = forms.EmailField(label='To', max_length=254)
    subject = forms.CharField(max_length=255)
    message = forms.CharField(widget=forms.Textarea)
