from django.contrib import admin
from .models import Profile, Questionnaire, Theme, Question, Choix, Reponse


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'poste', 'tranche_age', 'experience')
    search_fields = ('user__username', 'poste')
    list_filter = ('poste', 'tranche_age', 'experience')


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('titre', 'description')  # pas de postes_cibles si supprimé
    search_fields = ('titre',)
    # supprimer filter_horizontal si postes_cibles supprimé


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ('titre', 'questionnaire')
    search_fields = ('titre',)
    list_filter = ('questionnaire',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('texte', 'theme', 'type_question')
    search_fields = ('texte',)
    list_filter = ('type_question',)


@admin.register(Choix)
class ChoixAdmin(admin.ModelAdmin):
    list_display = ('texte', 'question', 'is_correct', 'votes')
    search_fields = ('texte',)


@admin.register(Reponse)
class ReponseAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'question', 'choix', 'date_reponse')
    search_fields = ('utilisateur__username',)
    date_hierarchy = 'date_reponse'
