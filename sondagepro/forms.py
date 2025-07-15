from django import forms
from django.contrib.auth import get_user_model
from .models import Profile, Questionnaire, Choix, Poste

User = get_user_model()

class CustomUserCreationForm(forms.ModelForm):
    poste = forms.ModelChoiceField(
        queryset=Poste.objects.all(),
        empty_label="Choisissez votre poste",
        label="Votre poste actuel",
        required=True
    )
    tranche_age = forms.ChoiceField(choices=Profile.TRANCHES_AGE, label="Tranche d'âge")
    experience = forms.ChoiceField(choices=Profile.EXPERIENCES, label="Expérience")

    class Meta:
        model = User
        fields = ('username',)  # 👈 seulement le nom/pseudo

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Nom"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_unusable_password()  # Aucun mot de passe demandé

        if commit:
            user.save()

            profile, created = Profile.objects.get_or_create(user=user)
            profile.poste = self.cleaned_data['poste']
            profile.tranche_age = self.cleaned_data['tranche_age']
            profile.experience = self.cleaned_data['experience']
            profile.save()

        return user



class EmailLoginForm(forms.Form):
    identifiant = forms.CharField(label="Nom d'utilisateur ou email")


class QuestionnaireForm(forms.ModelForm):
    class Meta:
        model = Questionnaire
        fields = ['titre', 'description', 'postes_cibles']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'postes_cibles': forms.CheckboxSelectMultiple(),
        }


class ChoixForm(forms.ModelForm):
    is_correct = forms.BooleanField(required=False, label="Réponse correcte")
    matching_pair = forms.CharField(max_length=200, required=False, label="Paire correspondante")

    class Meta:
        model = Choix
        fields = ['texte', 'is_correct', 'matching_pair']
