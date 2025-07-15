from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from .models import Questionnaire, Theme, Question, Choix, Reponse, Profile
from .forms import CustomUserCreationForm, EmailLoginForm, QuestionnaireForm
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict


User = get_user_model()

def accueil(request):
    return render(request, 'accueil.html')


def inscription(request):
    if request.method == "POST":
        print("🟡 Données POST reçues :", request.POST)  # Affiche les données envoyées par le formulaire

        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            print("✅ Formulaire valide")
            user = form.save()

            if not hasattr(user, 'profile'):
                print("❌ Le profil n’a pas été créé.")
                messages.error(request, "Une erreur est survenue lors de la création du profil.")
                return redirect('sondagepro:accueil')

            print("✅ Profil associé à :", user.username)
            print("📌 Poste :", user.profile.poste)
            print("📌 Tranche d'âge :", user.profile.tranche_age)
            print("📌 Expérience :", user.profile.experience)

            login(request, user)
            return redirect('sondagepro:tableau_bord')
        else:
            print("❌ Erreurs de formulaire :", form.errors)
    else:
        form = CustomUserCreationForm()

    return render(request, "inscription.html", {'form': form})



def connexion(request):
    if request.method == 'POST':
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            identifiant = form.cleaned_data['identifiant']
            user = None
            try:
                user = User.objects.get(username=identifiant)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(email=identifiant)
                except User.DoesNotExist:
                    pass

            if user:
                login(request, user)
                return redirect('sondagepro:tableau_bord')
            else:
                form.add_error('identifiant', "Aucun utilisateur trouvé avec cet identifiant.")
    else:
        form = EmailLoginForm()
    return render(request, 'connexion.html', {'form': form})


@login_required
def tableau_bord(request):
    user_profile = getattr(request.user, 'profile', None)
    if not user_profile:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('sondagepro:accueil')

    questionnaires = Questionnaire.objects.filter(postes_cibles=user_profile.poste).distinct()
    return render(request, 'tableau_bord.html', {
        'questionnaires': questionnaires,
        'categorie': user_profile.poste.nom if user_profile.poste else "Non défini"
    })


@login_required
def questionnaire_detail(request, questionnaire_id):
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    user_profile = getattr(request.user, 'profile', None)

    if not user_profile or not questionnaire.postes_cibles.filter(id=user_profile.poste.id).exists():
        return HttpResponseForbidden("Ce questionnaire n'est pas destiné à votre catégorie.")

    themes = []
    for theme in questionnaire.themes.all():
        questions = theme.questions.all()
        deja_repondu = all(
            Reponse.objects.filter(utilisateur=request.user, question=q).exists()
            for q in questions
        )
        if not deja_repondu:
            themes.append(theme)

    return render(request, 'questionnaire_detail.html', {
        'questionnaire': questionnaire,
        'themes': themes,
    })


@login_required
def theme_detail(request, theme_id):
    theme = get_object_or_404(Theme, id=theme_id)
    questionnaire = theme.questionnaire
    user_profile = getattr(request.user, 'profile', None)
    if not user_profile or not questionnaire.postes_cibles.filter(id=user_profile.poste.id).exists():
        return HttpResponseForbidden("Ce thème n'est pas destiné à votre catégorie.")
    questions = theme.questions.all()
    return render(request, 'theme_detail.html', {
        'theme': theme,
        'questions': questions,
    })


@login_required
def question_repondre(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    questionnaire = question.theme.questionnaire
    user_profile = getattr(request.user, 'profile', None)
    
    if not user_profile or not questionnaire.postes_cibles.filter(id=user_profile.poste.id).exists():
        return HttpResponseForbidden("Cette question n'est pas destinée à votre catégorie.")
    
    if Reponse.objects.filter(utilisateur=request.user, question=question).exists():
        messages.warning(request, "Vous avez déjà répondu à cette question.")
        return redirect('sondagepro:theme_detail', theme_id=question.theme.id)

    if request.method == 'POST':
        if question.type_question in ['multiple', 'matching']:
            choix_id = request.POST.get('choix')
            autre_texte = request.POST.get('autre_texte')

            if not choix_id:
                messages.error(request, "Veuillez sélectionner une réponse.")
                return redirect('sondagepro:question_repondre', question_id=question.id)

            if choix_id.startswith('autre_') and question.autoriser_autre:
                if autre_texte and autre_texte.strip():
                    Reponse.objects.create(
                        utilisateur=request.user,
                        question=question,
                        reponse_texte=autre_texte.strip()
                    )
                else:
                    messages.error(request, "Veuillez remplir le champ 'Autre'.")
                    return redirect('sondagepro:question_repondre', question_id=question.id)
            else:
                choix = get_object_or_404(Choix, id=choix_id, question=question)
                Reponse.objects.create(utilisateur=request.user, question=question, choix=choix)
                choix.votes += 1
                choix.save()

        else:
            reponse_texte = request.POST.get('reponse_texte')
            if not reponse_texte:
                messages.error(request, "Veuillez saisir une réponse.")
                return redirect('sondagepro:question_repondre', question_id=question.id)
            Reponse.objects.create(utilisateur=request.user, question=question, reponse_texte=reponse_texte)

        messages.success(request, "Votre réponse a été enregistrée !")
        return redirect('sondagepro:theme_detail', theme_id=question.theme.id)

    # 🎯 Affichage du formulaire
    choixs = question.choix.all() if question.type_question in ['multiple', 'matching'] else None
    return render(request, 'question_repondre.html', {
        'question': question,
        'choixs': choixs,
    })



@login_required
def resultats_questionnaire(request, questionnaire_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Seul l'administrateur peut voir les résultats.")
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    themes = questionnaire.themes.all()
    results = []
    for theme in themes:
        for question in theme.questions.all():
            reponses = Reponse.objects.filter(question=question)
            if question.type_question in ['multiple', 'matching']:
                choixs = question.choix.all()
                data = [{'texte': c.texte, 'votes': c.votes} for c in choixs]
                results.append({'question': question, 'type': question.type_question, 'data': data})
            else:
                textes = reponses.values_list('reponse_texte', flat=True)
                results.append({'question': question, 'type': question.type_question, 'data': list(textes)})
    return render(request, 'resultats_questionnaire.html', {
        'questionnaire': questionnaire,
        'results': results
    })


@login_required
def questionnaire_create(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Seul l'administrateur peut créer des questionnaires.")
    if request.method == 'POST':
        form = QuestionnaireForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Questionnaire créé avec succès.")
            return redirect('sondagepro:tableau_bord')
    else:
        form = QuestionnaireForm()
    return render(request, 'questionnaire_create.html', {'form': form})


@login_required
def theme_repondre(request, theme_id):
    theme = get_object_or_404(Theme, id=theme_id)
    questionnaire = theme.questionnaire

    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith("question_"):
                question_id = key.split("_")[1]
                question = get_object_or_404(Question, id=question_id)

                if Reponse.objects.filter(utilisateur=request.user, question=question).exists():
                    continue  # éviter doublons

                if question.type_question in ['multiple', 'matching']:
                    # Vérifie si c'est une réponse "autre"
                    if value.startswith("autre_") and question.autoriser_autre:
                        autre_texte = request.POST.get(f"autre_texte_{question_id}", "").strip()
                        if autre_texte:
                            Reponse.objects.create(
                                utilisateur=request.user,
                                question=question,
                                reponse_texte=autre_texte
                            )
                    else:
                        # Réponse avec un choix existant
                        try:
                            choix = Choix.objects.get(id=value, question=question)
                            Reponse.objects.create(
                                utilisateur=request.user,
                                question=question,
                                choix=choix
                            )
                            choix.votes += 1
                            choix.save()
                        except Choix.DoesNotExist:
                            pass  # Choix invalide
                else:
                    # Question texte
                    texte = value.strip()
                    if texte:
                        Reponse.objects.create(
                            utilisateur=request.user,
                            question=question,
                            reponse_texte=texte
                        )

        messages.success(request, "Merci pour vos réponses.")
        return redirect("sondagepro:questionnaire_detail", questionnaire.id)

    return redirect("sondagepro:theme_detail", theme_id=theme.id)




@login_required
def resultats_global(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Seul l'administrateur peut consulter les résultats.")

    questionnaires = Questionnaire.objects.all()
    donnees = []

    for questionnaire in questionnaires:
        themes_data = []
        for theme in questionnaire.themes.all():
            questions_data = []
            for question in theme.questions.all():
                reponses = Reponse.objects.filter(question=question)
                if question.type_question in ['multiple', 'matching']:
                    choixs = question.choix.all()
                    choix_data = [{'texte': c.texte, 'votes': c.votes} for c in choixs]
                    # Ajouter aussi les réponses "autre"
                    autres = reponses.filter(choix__isnull=True).exclude(reponse_texte="")
                    autres_data = list(autres.values_list('reponse_texte', flat=True))
                    questions_data.append({
                        'texte': question.texte,
                        'type': 'choix',
                        'choix': choix_data,
                        'autres': autres_data
                    })
                else:
                    textes = list(reponses.values_list('reponse_texte', flat=True))
                    questions_data.append({
                        'texte': question.texte,
                        'type': 'texte',
                        'reponses': textes
                    })
            themes_data.append({'titre': theme.titre, 'questions': questions_data})
        donnees.append({'questionnaire': questionnaire, 'themes': themes_data})

    return render(request, 'resultats_global.html', {'donnees': donnees})
