from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Profile, ProfilePoste, Questionnaire, Choix, Reponse
from django.utils import timezone
from django.urls import reverse

class SondageProTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='admin', password='adminpass', email='admin@example.com')
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test@example.com')
        
        # Créer un poste et un profil
        self.poste = ProfilePoste.objects.create(code='stagiaire', nom='Stagiaire')
        self.profile = Profile.objects.create(user=self.user, poste=self.poste, tranche_age='16_24', experience='moins_1')
        
        # Créer un questionnaire pour ce poste
        self.questionnaire = Questionnaire.objects.create(titre="Test Questionnaire", description="...",)
        self.questionnaire.categories.add(self.poste)

        # Créer une question + choix
        self.choix = Choix.objects.create(
            question=None,  # tu dois créer une Question avant si nécessaire
            texte="Option 1"
        )

    def test_questionnaire_creation_restricted(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('sondagepro:questionnaire_create'))
        self.assertEqual(response.status_code, 403)

    def test_redirection_after_inscription(self):
        response = self.client.post(reverse('sondagepro:inscription'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'poste': self.poste.code,
            'tranche_age': '16_24',
            'experience': 'moins_1'
        })
        self.assertRedirects(response, reverse('sondagepro:tableau_bord'))
