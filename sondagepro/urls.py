from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'sondagepro'

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', LogoutView.as_view(next_page='sondagepro:accueil'), name='logout'),

    path('tableau-bord/', views.tableau_bord, name='tableau_bord'),

    # Création de questionnaire (admin)
    path('questionnaire/creer/', views.questionnaire_create, name='questionnaire_create'),

    # Détail d’un questionnaire
    path('questionnaire/<int:questionnaire_id>/', views.questionnaire_detail, name='questionnaire_detail'),

    # Résultats d’un questionnaire (admin)
    path('questionnaire/<int:questionnaire_id>/resultats/', views.resultats_questionnaire, name='resultats_questionnaire'),

    # Détail d’un thème
    path('theme/<int:theme_id>/', views.theme_detail, name='theme_detail'),

    # Répondre à une question
    path('question/<int:question_id>/repondre/', views.question_repondre, name='question_repondre'),

    path('theme/<int:theme_id>/repondre/', views.theme_repondre, name='theme_repondre'),

    path('resultats/', views.resultats_global, name='resultats_global'),
]
