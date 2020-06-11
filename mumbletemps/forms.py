from django import forms

from mumbletemps import app_settings


class TempLinkCreateForm(forms.Form):
    DURATIONS = ((3, 3), (6, 6), (12, 2), (24, 24))

    duration = forms.ChoiceField(choices=DURATIONS)


class TempLinkLoginForm(forms.Form):
    name = forms.CharField(max_length=150)
    association = forms.CharField(max_length=10)
