from django.db import models
from django.contrib.auth.models import User

class Poste(models.Model):
    code = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=100)

    class Meta:
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    POSTES_CHOICES = [
        ('auditeur', 'Auditeur'),
        ('assistant_comptable', 'Assistant comptable'),
        ('chef_mission', 'Chef mission'),
        ('collaborateur_comptable', 'Collaborateur comptable'),
        ('dirigeant_associe', 'Dirigeant/associé(e)'),
        ('etudiant_stagiaire', 'Étudiant(e)/stagiaire'),
        ('expert_comptable', 'Expert-comptable'),
        ('expert_comptable_memorialiste', 'Expert-comptable mémorialiste'),
        ('manager', 'Manager'),
    ]

    TRANCHES_AGE = [
        ('16_24', '16-24 ans'),
        ('25_30', '25-30 ans'),
        ('31_36', '31-36 ans'),
        ('plus_36', 'Plus de 36 ans'),
    ]

    EXPERIENCES = [
        ('moins_1', 'Moins de 1 an'),
        ('1_3', '1 à 3 ans'),
        ('3_5', '3 à 5 ans'),
        ('plus_5', 'Plus de 5 ans'),
    ]
    
    poste = models.ForeignKey(Poste, on_delete=models.SET_NULL, null=True, blank=True)
    tranche_age = models.CharField(max_length=10, choices=TRANCHES_AGE, default='16_24')
    experience = models.CharField(max_length=10, choices=EXPERIENCES, default='moins_1')

    def __str__(self):
        return f"{self.user.username} - {self.poste.nom if self.poste else 'Poste non défini'}"



class Questionnaire(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    postes_cibles = models.ManyToManyField(Poste, related_name='questionnaires', blank=True)

    def __str__(self):
        return self.titre


class Theme(models.Model):
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='themes')
    titre = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.titre} ({self.questionnaire.titre})"


class Question(models.Model):
    QUESTION_TYPES = [
        ('multiple', 'Choix multiple'),
        ('open', 'Question ouverte'),
        ('wordcloud', 'Nuage de mots'),
        ('matching', 'Correspondance'),
        ('fill_blanks', 'Remplir les blancs'),
    ]

    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='questions')
    texte = models.CharField(max_length=255)
    type_question = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple')
    autoriser_autre = models.BooleanField(default=False)  # ✅ Nouveau champ

    def __str__(self):
        return f"{self.texte} ({self.theme.titre})"



class Choix(models.Model):
    question = models.ForeignKey(Question, related_name='choix', on_delete=models.CASCADE)
    texte = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    matching_pair = models.CharField(max_length=200, blank=True)
    votes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.texte


class Reponse(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True)
    choix = models.ForeignKey(Choix, on_delete=models.CASCADE, null=True, blank=True)
    reponse_texte = models.TextField(blank=True)
    date_reponse = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('utilisateur', 'question')

    def __str__(self):
        question_text = self.question.texte if self.question else "Question inconnue"
        return f"{self.utilisateur.username} - {question_text}"
