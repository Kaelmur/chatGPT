from django import forms
from .models import Work


class TextForm(forms.ModelForm):

    class Meta:
        model = Work
        fields = ["file"]
