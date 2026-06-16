from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'sondagepro'

urlpatterns = [
    # Home page
    path('', views.accueil, name='accueil'),

    # User onboarding: inscription & connexion
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('connexion/check-superuser/', views.check_superuser, name='check_superuser'),
    path('deconnexion/', LogoutView.as_view(next_page='sondagepro:accueil'), name='logout'),

    # Creator dashboard
    path('tableau-bord/', views.tableau_bord, name='tableau_bord'),

    # Participation routes (join by code)
    path('rejoindre/', views.rejoindre, name='rejoindre'),
    path('s/<str:code>/', views.sondage_detail, name='sondage_detail'),
    path('s/<str:code>/pseudo/', views.sondage_pseudo, name='sondage_pseudo'),
    path('s/<str:code>/repondre/', views.sondage_repondre, name='sondage_repondre'),

    # Questionnaire creation & editing
    path('questionnaire/creer/', views.questionnaire_create, name='questionnaire_create'),
    path('questionnaire/<int:questionnaire_id>/editer/', views.questionnaire_edit, name='questionnaire_edit'),
    path('questionnaire/<int:questionnaire_id>/question/ajouter/', views.question_add, name='question_add'),
    path('question/<int:question_id>/supprimer/', views.question_delete, name='question_delete'),
    path('questionnaire/<int:questionnaire_id>/supprimer/', views.questionnaire_delete, name='questionnaire_delete'),

    # Questionnaire detail (participant flow)
    path('questionnaire/<int:questionnaire_id>/', views.questionnaire_detail, name='questionnaire_detail'),

    # Results & live data endpoints
    path('questionnaire/<int:questionnaire_id>/resultats/', views.resultats_questionnaire, name='resultats_questionnaire'),
    path('questionnaire/<int:questionnaire_id>/resultats/live/', views.resultats_live_data, name='resultats_live_data'),

    # Reply to a theme inside a questionnaire
    path('theme/<int:theme_id>/repondre/', views.theme_repondre, name='theme_repondre'),

    # Global results (admin only)
    path('resultats/', views.resultats_global, name='resultats_global'),

    # Superuser administration panel
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/utilisateurs/', views.admin_utilisateurs, name='admin_utilisateurs'),
    path('admin-panel/utilisateurs/<int:user_id>/', views.admin_utilisateur_detail, name='admin_utilisateur_detail'),
    path('admin-panel/questionnaires/', views.admin_questionnaires, name='admin_questionnaires'),
]
