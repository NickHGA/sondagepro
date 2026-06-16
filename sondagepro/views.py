from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.contrib.auth import get_user_model, login, authenticate
from .models import Questionnaire, Theme, Question, Choix, Reponse, Profile, Poste
from .forms import CustomUserCreationForm, EmailLoginForm, QuestionnaireForm, CreatorCreationForm

User = get_user_model()

def accueil(request):
    return render(request, 'accueil.html')


def inscription(request):
    if request.method == "POST":
        form = CreatorCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Votre compte créateur a été créé avec succès !")
            return redirect('sondagepro:tableau_bord')
    else:
        form = CreatorCreationForm()

    return render(request, "inscription.html", {'form': form})



def connexion(request):
    if request.method == 'POST':
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            identifiant = form.cleaned_data['identifiant']
            mot_de_passe = form.cleaned_data.get('mot_de_passe', '')
            user = None

            # Résoudre l'utilisateur (username ou email)
            try:
                user = User.objects.get(username=identifiant)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(email=identifiant)
                except User.DoesNotExist:
                    pass

            if user is None:
                form.add_error('identifiant', "Aucun utilisateur trouvé avec cet identifiant.")
            elif user.is_superuser or user.has_usable_password():
                # Les utilisateurs avec mot de passe doivent s'authentifier avec
                if not mot_de_passe:
                    form.add_error('mot_de_passe', "Veuillez entrer votre mot de passe.")
                else:
                    authenticated = authenticate(request, username=user.username, password=mot_de_passe)
                    if authenticated:
                        login(request, authenticated)
                        if authenticated.is_superuser:
                            return redirect('sondagepro:admin_dashboard')
                        return redirect('sondagepro:tableau_bord')
                    else:
                        form.add_error('mot_de_passe', "Mot de passe incorrect.")
            else:
                # Participants historiques sans mot de passe
                login(request, user)
                return redirect('sondagepro:tableau_bord')
    else:
        form = EmailLoginForm()
    return render(request, 'connexion.html', {'form': form})


def check_superuser(request):
    """Endpoint AJAX : indique si l'identifiant saisi est un superutilisateur."""
    if request.method != 'POST':
        return JsonResponse({'is_superuser': False})
    identifiant = request.POST.get('identifiant', '').strip()
    if not identifiant:
        return JsonResponse({'is_superuser': False})
    try:
        user = User.objects.get(username=identifiant)
    except User.DoesNotExist:
        try:
            user = User.objects.get(email=identifiant)
        except User.DoesNotExist:
            return JsonResponse({'is_superuser': False})
    # Si c'est un superuser ou s'il a un mot de passe, on retourne True pour afficher le champ mot de passe
    requires_password = user.is_superuser or user.has_usable_password()
    return JsonResponse({'is_superuser': requires_password})


@login_required
def tableau_bord(request):
    questionnaires = Questionnaire.objects.filter(createur=request.user).order_by('-id')
    data = []
    for q in questionnaires:
        nb_questions = Question.objects.filter(theme__questionnaire=q).count()
        # Compter les répondants uniques par utilisateur ou pseudo
        # On utilise une liste ou un ensemble des combinaisons utilisateur/pseudo uniques
        reponses = Reponse.objects.filter(question__theme__questionnaire=q)
        respondents = set()
        for r in reponses:
            if r.utilisateur:
                respondents.add(f"user_{r.utilisateur.id}")
            elif r.pseudo:
                respondents.add(f"pseudo_{r.pseudo.lower()}")
        nb_repondants = len(respondents)
        data.append({
            'questionnaire': q,
            'nb_questions': nb_questions,
            'nb_repondants': nb_repondants,
        })
    return render(request, 'tableau_bord.html', {
        'questionnaires_data': data,
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
    if request.method == 'POST':
        form = QuestionnaireForm(request.POST)
        if form.is_valid():
            questionnaire = form.save(commit=False)
            questionnaire.createur = request.user
            questionnaire.save()
            # Créer automatiquement un thème par défaut nommé "Général"
            Theme.objects.create(questionnaire=questionnaire, titre="Général")
            messages.success(request, "Questionnaire créé avec succès. Ajoutez vos questions !")
            return redirect('sondagepro:questionnaire_edit', questionnaire_id=questionnaire.id)
    else:
        form = QuestionnaireForm()
    return render(request, 'questionnaire_create.html', {'form': form})


@login_required
def questionnaire_edit(request, questionnaire_id):
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    if questionnaire.createur != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'éditer ce questionnaire.")
    
    # Récupérer toutes les questions triées
    questions = Question.objects.filter(theme__questionnaire=questionnaire)
    
    return render(request, 'questionnaire_edit.html', {
        'questionnaire': questionnaire,
        'questions': questions,
    })


@login_required
def question_add(request, questionnaire_id):
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id, createur=request.user)
    if request.method == 'POST':
        texte = request.POST.get('texte', '').strip()
        type_question = request.POST.get('type_question', 'multiple')
        temps_limite = int(request.POST.get('temps_limite', 0))
        
        if not texte:
            messages.error(request, "Le texte de la question ne peut pas être vide.")
            return redirect('sondagepro:questionnaire_edit', questionnaire_id=questionnaire.id)
        
        # Obtenir ou créer le thème par défaut
        theme = questionnaire.themes.first()
        if not theme:
            theme = Theme.objects.create(questionnaire=questionnaire, titre="Général")
            
        question = Question.objects.create(
            theme=theme,
            texte=texte,
            type_question=type_question,
            temps_limite=temps_limite
        )
        
        # Si la question gère les choix (multiple, matching, fill_blanks)
        if type_question in ['multiple', 'matching', 'fill_blanks']:
            i = 0
            while f'choix_texte_{i}' in request.POST:
                choix_texte = request.POST.get(f'choix_texte_{i}', '').strip()
                if choix_texte:
                    is_correct = request.POST.get(f'choix_correct_{i}') == 'on'
                    matching_pair = request.POST.get(f'choix_matching_{i}', '').strip()
                    Choix.objects.create(
                        question=question,
                        texte=choix_texte,
                        is_correct=is_correct,
                        matching_pair=matching_pair
                    )
                i += 1
        
        messages.success(request, "Question ajoutée avec succès.")
    return redirect('sondagepro:questionnaire_edit', questionnaire_id=questionnaire.id)


@login_required
def question_delete(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    questionnaire = question.theme.questionnaire
    if questionnaire.createur == request.user or request.user.is_superuser:
        question.delete()
        messages.success(request, "La question a été supprimée.")
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation de modifier ce questionnaire.")
    return redirect('sondagepro:questionnaire_edit', questionnaire_id=questionnaire.id)


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

    return redirect("sondagepro:questionnaire_detail", questionnaire_id=questionnaire.id)




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
                    total_votes = sum(c.votes for c in choixs)
                    choix_data = [{
                        'texte': c.texte,
                        'votes': c.votes,
                        'pct': round(c.votes / total_votes * 100) if total_votes > 0 else 0,
                    } for c in choixs]
                    autres = reponses.filter(choix__isnull=True).exclude(reponse_texte="")
                    autres_data = list(autres.values_list('reponse_texte', flat=True))
                    questions_data.append({
                        'texte': question.texte,
                        'type': 'choix',
                        'choix': choix_data,
                        'autres': autres_data,
                        'total_votes': total_votes,
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


# ─────────────────────────────────────────────
#  PANNEAU ADMINISTRATION SUPERUTILISATEUR
# ─────────────────────────────────────────────

def superuser_required(view_func):
    """Décorateur combinant login_required + is_superuser."""
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden("Accès réservé aux administrateurs.")
        return view_func(request, *args, **kwargs)
    return _wrapped


@superuser_required
def admin_dashboard(request):
    total_users = User.objects.filter(is_superuser=False).count()
    total_questionnaires = Questionnaire.objects.count()
    total_reponses = Reponse.objects.count()
    # Utilisateurs ayant répondu à au moins une question
    users_actifs = Reponse.objects.values('utilisateur').distinct().count()
    taux = round((users_actifs / total_users * 100) if total_users > 0 else 0)

    derniers_users = User.objects.filter(is_superuser=False).order_by('-date_joined')[:5]

    return render(request, 'admin_dashboard.html', {
        'total_users': total_users,
        'total_questionnaires': total_questionnaires,
        'total_reponses': total_reponses,
        'users_actifs': users_actifs,
        'taux': taux,
        'derniers_users': derniers_users,
    })


@superuser_required
def admin_utilisateurs(request):
    poste_filtre = request.GET.get('poste', '')
    age_filtre = request.GET.get('age', '')
    exp_filtre = request.GET.get('experience', '')

    utilisateurs = User.objects.filter(is_superuser=False).select_related('profile__poste').order_by('username')

    if poste_filtre:
        utilisateurs = utilisateurs.filter(profile__poste__code=poste_filtre)
    if age_filtre:
        utilisateurs = utilisateurs.filter(profile__tranche_age=age_filtre)
    if exp_filtre:
        utilisateurs = utilisateurs.filter(profile__experience=exp_filtre)

    postes = Poste.objects.all()

    return render(request, 'admin_utilisateurs.html', {
        'utilisateurs': utilisateurs,
        'postes': postes,
        'poste_filtre': poste_filtre,
        'age_filtre': age_filtre,
        'exp_filtre': exp_filtre,
        'tranches_age': Profile.TRANCHES_AGE,
        'experiences': Profile.EXPERIENCES,
    })


@superuser_required
def admin_utilisateur_detail(request, user_id):
    utilisateur = get_object_or_404(User, id=user_id, is_superuser=False)
    reponses = Reponse.objects.filter(utilisateur=utilisateur).select_related(
        'question__theme__questionnaire', 'choix'
    ).order_by('question__theme__questionnaire__titre', 'question__theme__titre')

    # Grouper les réponses par questionnaire > thème
    groupes = {}
    for rep in reponses:
        q_titre = rep.question.theme.questionnaire.titre
        t_titre = rep.question.theme.titre
        groupes.setdefault(q_titre, {}).setdefault(t_titre, []).append(rep)

    return render(request, 'admin_utilisateur_detail.html', {
        'utilisateur': utilisateur,
        'groupes': groupes,
        'nb_reponses': reponses.count(),
    })

@superuser_required
def admin_questionnaires(request):
    questionnaires = Questionnaire.objects.prefetch_related('postes_cibles', 'themes').all()

    data = []
    for q in questionnaires:
        # Nombre d'utilisateurs distincts ayant répondu à ce questionnaire
        nb_repondants = Reponse.objects.filter(
            question__theme__questionnaire=q
        ).values('utilisateur').distinct().count()

        # Nombre total de questions
        nb_questions = Question.objects.filter(theme__questionnaire=q).count()

        data.append({
            'questionnaire': q,
            'nb_repondants': nb_repondants,
            'nb_questions': nb_questions,
        })

    return render(request, 'admin_questionnaires.html', {'data': data})


def rejoindre(request):
    """Vérifie le code de sondage saisi et redirige vers la participation."""
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        if not code:
            messages.error(request, "Veuillez entrer un code de sondage.")
            return redirect('sondagepro:accueil')
        try:
            questionnaire = Questionnaire.objects.get(code=code)
            return redirect('sondagepro:sondage_detail', code=code)
        except Questionnaire.DoesNotExist:
            messages.error(request, "Code de sondage invalide.")
            return redirect('sondagepro:accueil')
    return redirect('sondagepro:accueil')


def sondage_detail(request, code):
    """Affiche les questions pour y répondre."""
    questionnaire = get_object_or_404(Questionnaire, code=code.upper())
    
    # Vérification du pseudo en session pour les invités anonymes
    pseudo = request.session.get(f'pseudo_{questionnaire.id}')
    if not pseudo and not request.user.is_authenticated:
        return redirect('sondagepro:sondage_pseudo', code=code)
    
    user_pseudo = request.user.username if request.user.is_authenticated else pseudo
    themes = questionnaire.themes.prefetch_related('questions__choix').all()
    
    # Déterminer les questions déjà répondues par ce participant
    repondues_ids = set()
    if request.user.is_authenticated:
        repondues_ids = set(Reponse.objects.filter(
            utilisateur=request.user, question__theme__questionnaire=questionnaire
        ).values_list('question_id', flat=True))
    elif pseudo:
        repondues_ids = set(Reponse.objects.filter(
            pseudo=pseudo, question__theme__questionnaire=questionnaire
        ).values_list('question_id', flat=True))
        
    toutes_questions = []
    for t in themes:
        toutes_questions.extend(t.questions.all())
        
    deja_fini = len(toutes_questions) > 0 and all(q.id in repondues_ids for q in toutes_questions)
    
    return render(request, 'sondage_repondre.html', {
        'questionnaire': questionnaire,
        'themes': themes,
        'pseudo': user_pseudo,
        'repondues_ids': repondues_ids,
        'deja_fini': deja_fini,
    })


def sondage_pseudo(request, code):
    """Saisie du pseudo pour les participants invités."""
    questionnaire = get_object_or_404(Questionnaire, code=code.upper())
    if request.method == 'POST':
        pseudo = request.POST.get('pseudo', '').strip()
        if not pseudo:
            messages.error(request, "Veuillez entrer un pseudo.")
            return render(request, 'rejoindre_pseudo.html', {'questionnaire': questionnaire})
        
        # Enregistrer le pseudo dans la session
        request.session[f'pseudo_{questionnaire.id}'] = pseudo
        return redirect('sondagepro:sondage_detail', code=code)
        
    return render(request, 'rejoindre_pseudo.html', {'questionnaire': questionnaire})


def sondage_repondre(request, code):
    """Enregistre les réponses du participant."""
    questionnaire = get_object_or_404(Questionnaire, code=code.upper())
    pseudo = request.session.get(f'pseudo_{questionnaire.id}')
    
    if not pseudo and not request.user.is_authenticated:
        return redirect('sondagepro:sondage_pseudo', code=code)
        
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith("question_"):
                question_id = key.split("_")[1]
                question = get_object_or_404(Question, id=question_id)
                
                # Vérifier doublons
                has_voted = False
                if request.user.is_authenticated:
                    has_voted = Reponse.objects.filter(utilisateur=request.user, question=question).exists()
                elif pseudo:
                    has_voted = Reponse.objects.filter(pseudo=pseudo, question=question).exists()
                    
                if has_voted:
                    continue
                    
                if question.type_question in ['multiple', 'matching']:
                    if value.startswith("autre_") and question.autoriser_autre:
                        autre_texte = request.POST.get(f"autre_texte_{question_id}", "").strip()
                        if autre_texte:
                            Reponse.objects.create(
                                utilisateur=request.user if request.user.is_authenticated else None,
                                pseudo=None if request.user.is_authenticated else pseudo,
                                question=question,
                                reponse_texte=autre_texte
                            )
                    else:
                        try:
                            choix = Choix.objects.get(id=value, question=question)
                            Reponse.objects.create(
                                utilisateur=request.user if request.user.is_authenticated else None,
                                pseudo=None if request.user.is_authenticated else pseudo,
                                question=question,
                                choix=choix
                            )
                            choix.votes += 1
                            choix.save()
                        except Choix.DoesNotExist:
                            pass
                else:
                    texte = value.strip()
                    if texte:
                        Reponse.objects.create(
                            utilisateur=request.user if request.user.is_authenticated else None,
                            pseudo=None if request.user.is_authenticated else pseudo,
                            question=question,
                            reponse_texte=texte
                        )
                        
        messages.success(request, "Vos réponses ont été enregistrées avec succès !")
        return redirect('sondagepro:sondage_detail', code=code)
        
    return redirect('sondagepro:sondage_detail', code=code)


def resultats_live_data(request, questionnaire_id):
    """Endpoint JSON retournant les statistiques en temps réel pour le polling."""
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    
    # Compter les répondants uniques
    reponses_q = Reponse.objects.filter(question__theme__questionnaire=questionnaire)
    respondents = set()
    for r in reponses_q:
        if r.utilisateur:
            respondents.add(r.utilisateur.username)
        elif r.pseudo:
            respondents.add(r.pseudo)
    total_repondants = len(respondents)
    pseudos_actifs = sorted(list(respondents))
    
    questions_data = []
    for theme in questionnaire.themes.all():
        for question in theme.questions.all():
            reponses_quest = Reponse.objects.filter(question=question)
            if question.type_question in ['multiple', 'matching', 'fill_blanks']:
                choixs = question.choix.all()
                total_votes = sum(c.votes for c in choixs)
                choix_list = [{
                    'id': c.id,
                    'texte': c.texte,
                    'votes': c.votes,
                    'pct': round(c.votes / total_votes * 100) if total_votes > 0 else 0,
                    'is_correct': c.is_correct,
                    'matching_pair': c.matching_pair
                } for c in choixs]
                
                autres = reponses_quest.filter(choix__isnull=True).exclude(reponse_texte="")
                autres_list = list(autres.values_list('reponse_texte', flat=True))
                
                questions_data.append({
                    'id': question.id,
                    'texte': question.texte,
                    'type': question.type_question,
                    'choix': choix_list,
                    'autres': autres_list,
                    'total_votes': total_votes,
                    'temps_limite': question.temps_limite
                })
            else:
                textes = list(reponses_quest.values_list('reponse_texte', flat=True))
                questions_data.append({
                    'id': question.id,
                    'texte': question.texte,
                    'type': question.type_question,
                    'reponses': textes,
                    'temps_limite': question.temps_limite
                })
                
    return JsonResponse({
        'total_repondants': total_repondants,
        'pseudos_actifs': pseudos_actifs,
        'questions': questions_data
    })


@login_required
def questionnaire_delete(request, questionnaire_id):
    """Supprime un questionnaire si l'utilisateur en est le créateur ou superutilisateur."""
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    if questionnaire.createur == request.user or request.user.is_superuser:
        questionnaire.delete()
        messages.success(request, "Le questionnaire a été supprimé.")
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation de supprimer ce questionnaire.")
    return redirect('sondagepro:tableau_bord')
