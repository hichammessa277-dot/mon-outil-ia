"""
mon-outil-ia - Assistant d'Étude Intelligent
===========================================
Application éducative propulsée par Streamlit et le SDK OpenAI (v1.0+).
Permet aux étudiants de simplifier des cours denses, de générer des quiz interactifs
avec scoring en direct, et de créer des flashcards de révision prêtes pour Anki.

Licence : MIT
"""

import json
import os
from typing import Any, Dict, List, Optional
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError, OpenAIError

# Chargement automatique des variables d'environnement (.env)
load_dotenv()

# ==============================================================================
# CONFIGURATION DE LA PAGE STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="mon-outil-ia | Assistant d'Étude Intelligent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Styles CSS personnalisés pour une interface moderne et soignée
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .card {
        border-radius: 12px;
        padding: 1.2rem;
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        margin-bottom: 1rem;
    }
    .flashcard-front {
        font-weight: 700;
        color: #1E40AF;
        font-size: 1.1rem;
    }
    .flashcard-back {
        color: #1F2937;
        margin-top: 0.5rem;
        border-top: 1px dashed #CBD5E1;
        padding-top: 0.5rem;
    }
    .score-badge {
        font-size: 1.3rem;
        font-weight: 700;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        display: inline-block;
        margin: 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# DONNÉES D'EXEMPLE POUR TEST IMMÉDIAT
# ==============================================================================
SAMPLE_COURSE = """Le modèle OSI (Open Systems Interconnection) est un standard de communication en réseau développé par l'ISO en 1984. Il structure la communication informatique en 7 couches distinctes, chacune ayant un rôle spécifique :

1. Couche Physique (Couche 1) : Transmission brute des bits sur un média physique (câbles cuivre, fibre optique, ondes Wi-Fi).
2. Couche Liaison de données (Couche 2) : Transmission fiable de trames entre deux nœuds adjacents. Gestion des adresses physiques MAC et détection d'erreurs (ex: Ethernet, Wi-Fi 802.11).
3. Couche Réseau (Couche 3) : Routage des paquets à travers des réseaux hétérogènes et adressage logique IP (IPv4, IPv6, routeurs).
4. Couche Transport (Couche 4) : Communication de bout en bout entre processus. Gestion de la fiabilité, du contrôle de flux et de la segmentation (ex: TCP orienté connexion avec accusé de réception, UDP non orienté connexion et rapide).
5. Couche Session (Couche 5) : Établissement, gestion et fermeture des sessions entre applications (ex: RPC, NetBIOS).
6. Couche Présentation (Couche 6) : Traduction, chiffrement et compression des données (ex: TLS/SSL, formats JPEG, ASCII).
7. Couche Application (Couche 7) : Interface directe avec les logiciels utilisateurs pour les protocoles réseau (ex: HTTP, HTTPS, DNS, SMTP, FTP).

Ce modèle est principalement théorique et pédagogique. Le modèle TCP/IP (composé de 4 couches) est celui réellement déployé sur Internet, mais le modèle OSI reste la référence absolue pour le diagnostic et la compréhension des protocoles."""


# ==============================================================================
# INITIALISATION DU CLIENT OPENAI
# ==============================================================================
def init_openai_client(api_key: Optional[str]) -> Optional[OpenAI]:
    """
    Initialise et retourne une instance du client OpenAI.
    Retourne None si aucune clé n'est fournie.
    """
    if not api_key or not api_key.strip():
        return None
    return OpenAI(api_key=api_key.strip())


# ==============================================================================
# FONCTIONS LOGIQUES ET APPELS À L'API OPENAI
# ==============================================================================
def call_summarize(
    client: OpenAI,
    model: str,
    text: str,
    style: str,
    temperature: float = 0.3,
) -> str:
    """
    Génère une simplification ou un résumé adapté au profil de révision choisi.
    """
    system_prompts = {
        "Vulgarisation simple (Méthode Feynman)": (
            "Tu es un tuteur pédagogique exceptionnel adepte de la méthode Feynman. "
            "Simplifie ce cours comme si tu l'expliquais à un débutant ou un collégien curieux. "
            "Utilise des analogies concrètes du quotidien, un ton bienveillant, et évite le jargon "
            "complexe sans le définir immédiatement."
        ),
        "Synthèse universitaire structurée": (
            "Tu es un professeur d'université rigoureux. Produis une synthèse structurée, "
            "exhaustive et académique de ce texte. Organise la réponse avec des titres hiérarchisés, "
            "les définitions formelles, les mécanismes clés et les implications pratiques."
        ),
        "Fiche mémo & Points clés": (
            "Tu es un spécialiste de la mémorisation active. Synthétise ce cours sous forme de "
            "fiche mémo ultraclair : 1) Les 3 à 5 concepts cardinaux en bullet points, "
            "2) Les pièges à éviter / confusions fréquentes, 3) Un mini-glossaire des définitions clés."
        ),
    }

    selected_prompt = system_prompts.get(
        style, system_prompts["Synthèse universitaire structurée"]
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": selected_prompt},
            {
                "role": "user",
                "content": f"Voici le texte du cours à traiter :\n\n{text}",
            },
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def call_generate_quiz(
    client: OpenAI,
    model: str,
    text: str,
    num_questions: int = 5,
    difficulty: str = "Intermédiaire",
    temperature: float = 0.4,
) -> Dict[str, Any]:
    """
    Génère un QCM structuré sous format JSON garanti.
    """
    system_prompt = (
        "Tu es un enseignant concepteur de quiz d'évaluation pédagogique. "
        "Génère un quiz à choix multiples (QCM) rigoureusement basé sur le texte fourni.\n"
        "Tu DOIS retourner STRICTEMENT un objet JSON valide avec la structure suivante :\n"
        "{\n"
        '  "quiz": [\n'
        "    {\n"
        '      "id": 1,\n'
        '      "question": "Texte précis de la question",\n'
        '      "options": ["A) Première option", "B) Deuxième option", "C) Troisième option", "D) Quatrième option"],\n'
        '      "correct_answer": "A",\n'
        '      "explanation": "Explication pédagogique claire prouvant pourquoi c\'est la bonne réponse."\n'
        "    }\n"
        "  ]\n"
        "}\n"
        f"Consignes : Génère exactement {num_questions} questions de niveau {difficulty}."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Texte du cours :\n\n{text}"},
        ],
        response_format={"type": "json_object"},
        temperature=temperature,
    )

    raw_json = response.choices[0].message.content or "{}"
    return json.loads(raw_json)


def call_generate_flashcards(
    client: OpenAI,
    model: str,
    text: str,
    num_cards: int = 6,
    temperature: float = 0.4,
) -> Dict[str, Any]:
    """
    Génère une série de flashcards (Recto / Verso) au format JSON.
    """
    system_prompt = (
        "Tu es un expert en sciences de l'apprentissage et répétition espacée (Spaced Repetition). "
        "Extrait les concepts cardinaux, définitions et distinctions cruciales du texte sous forme de flashcards.\n"
        "Tu DOIS retourner STRICTEMENT un objet JSON valide avec la structure suivante :\n"
        "{\n"
        '  "flashcards": [\n'
        "    {\n"
        '      "id": 1,\n'
        '      "front": "Notion ou question claire au recto",\n'
        '      "back": "Réponse synthétique, précise et facile à mémoriser au verso",\n'
        '      "category": "Thème ou mot-clé associé"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        f"Consignes : Génère exactement {num_cards} flashcards à fort impact de mémorisation."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Texte du cours :\n\n{text}"},
        ],
        response_format={"type": "json_object"},
        temperature=temperature,
    )

    raw_json = response.choices[0].message.content or "{}"
    return json.loads(raw_json)


# ==============================================================================
# GESTION DES VARIABLES DE SESSION (SESSION STATE)
# ==============================================================================
if "course_text" not in st.session_state:
    st.session_state.course_text = ""
if "summary_result" not in st.session_state:
    st.session_state.summary_result = None
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "flashcards_data" not in st.session_state:
    st.session_state.flashcards_data = None


# ==============================================================================
# BARRE LATÉRALE (SIDEBAR) - CONFIGURATION & PARAMÈTRES
# ==============================================================================
with st.sidebar:
    st.image(
        "https://raw.githubusercontent.com/feathericons/feather/master/icons/book-open.svg",
        width=50,
    )
    st.title("🎓 mon-outil-ia")
    st.caption("Assistant IA Open-Source pour Réviser & Apprendre Plus Vite")
    st.divider()

    # Gestion de la Clé API OpenAI
    st.subheader("🔑 Clé API OpenAI")
    env_api_key = os.getenv("OPENAI_API_KEY", "")

    if env_api_key:
        st.success("Clé API détectée depuis l'environnement (`.env`) ✅")
        use_custom_key = st.checkbox("Remplacer par une autre clé API", value=False)
        if use_custom_key:
            api_key_input = st.text_input(
                "Entrez votre clé API OpenAI",
                type="password",
                help="Votre clé commence par 'sk-...' et reste locale.",
            )
            active_api_key = api_key_input.strip() if api_key_input else env_api_key
        else:
            active_api_key = env_api_key
    else:
        st.warning("Aucune variable `OPENAI_API_KEY` trouvée dans le fichier `.env`.")
        active_api_key = st.text_input(
            "Entrez votre clé API OpenAI",
            type="password",
            placeholder="sk-proj-...",
            help="Votre clé API est utilisée pour vos requêtes et n'est jamais enregistrée sur un serveur externe.",
        )

    st.divider()

    # Sélection du modèle et hyperparamètres
    st.subheader("⚙️ Configuration Modèle")
    selected_model = st.selectbox(
        "Modèle IA",
        options=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
        index=0,
        help="gpt-4o-mini est le modèle optimal pour les étudiants : ultra rapide, intelligent et très économique.",
    )

    temperature = st.slider(
        "Créativité / Température",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.1,
        help="Une température basse garantit des réponses plus factuelles et rigoureuses.",
    )

    st.divider()
    st.markdown("### 📌 À propos")
    st.markdown(
        """
        **mon-outil-ia** est un projet communautaire destiné aux lycéens et étudiants du supérieur.
        - [Code Source GitHub](#)
        - Licence : **MIT**
        - Frameworks : Streamlit & OpenAI v1+
        """
    )


# ==============================================================================
# INTERFACE PRINCIPALE
# ==============================================================================
st.markdown('<div class="main-title">🎓 Assistant d\'Étude Intelligent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Collez un cours complexe ou vos notes brutes pour obtenir instantanément des explications vulgarisées, un quiz interactif ou des flashcards Anki.</div>',
    unsafe_allow_html=True,
)

# Zone d'entrée du cours
st.subheader("1. 📄 Votre texte ou cours")

col_btn1, col_btn2, _ = st.columns([1.5, 1.2, 3])
with col_btn1:
    if st.button("📋 Charger un cours d'exemple (Modèle OSI)"):
        st.session_state.course_text = SAMPLE_COURSE
        st.rerun()

with col_btn2:
    if st.button("🗑️ Vider le champ"):
        st.session_state.course_text = ""
        st.session_state.summary_result = None
        st.session_state.quiz_data = None
        st.session_state.quiz_answers = {}
        st.session_state.quiz_submitted = False
        st.session_state.flashcards_data = None
        st.rerun()

course_input = st.text_area(
    "Contenu du cours :",
    value=st.session_state.course_text,
    height=200,
    placeholder="Collez ici votre cours, un chapitre de manuel, une transcription ou vos notes de révision...",
    help="Plus le texte est complet, plus les quiz et flashcards seront pertinents.",
)

# Mise à jour de l'état
st.session_state.course_text = course_input

# Affichage du compteur de mots/caractères
words_count = len(course_input.split()) if course_input.strip() else 0
st.caption(f"📊 Longueur actuelle : **{len(course_input)}** caractères | **{words_count}** mots")

st.divider()

# ==============================================================================
# ONGLET DES FONCTIONNALITÉS
# ==============================================================================
tab_summary, tab_quiz, tab_flashcards = st.tabs(
    [
        "📝 Synthèse & Simplification",
        "🎯 Quiz Interactif QCM",
        "💡 Flashcards de Révision",
    ]
)

# Vérification préliminaire de la clé API
client = init_openai_client(active_api_key)


def check_prerequisites() -> bool:
    """Valide la présence de la clé API et du texte source."""
    if not client:
        st.error(
            "⚠️ Veuillez renseigner votre **clé API OpenAI** dans la barre latérale gauche pour lancer la génération."
        )
        return False
    if not st.session_state.course_text.strip():
        st.warning(
            "⚠️ Veuillez coller un extrait de cours ou utiliser le bouton **'Charger un cours d'exemple'** ci-dessus."
        )
        return False
    return True


# ------------------------------------------------------------------------------
# ONGLET 1 : SYNTHÈSE & SIMPLIFICATION
# ------------------------------------------------------------------------------
with tab_summary:
    st.markdown("### 📝 Simplifier & Synthétiser un cours")
    st.write(
        "Transformez les notions abstraites en explications limpides selon votre style d'apprentissage."
    )

    col_style, col_action = st.columns([2.5, 1])
    with col_style:
        summary_style = st.selectbox(
            "Format de vulgarisation souhaité :",
            [
                "Vulgarisation simple (Méthode Feynman)",
                "Synthèse universitaire structurée",
                "Fiche mémo & Points clés",
            ],
            index=0,
        )
    with col_action:
        st.write("")  # alignement vertical
        st.write("")
        btn_generate_summary = st.button("✨ Générer la synthèse", use_container_width=True)

    if btn_generate_summary and check_prerequisites():
        try:
            with st.spinner("Analyse du cours et formulation pédagogique en cours..."):
                result = call_summarize(
                    client=client,
                    model=selected_model,
                    text=st.session_state.course_text,
                    style=summary_style,
                    temperature=temperature,
                )
                st.session_state.summary_result = result
        except AuthenticationError:
            st.error("❌ Échec d'authentification : Votre clé API OpenAI semble invalide ou expirée.")
        except RateLimitError:
            st.error("❌ Limite atteinte : Quota OpenAI dépassé ou trop de requêtes simultanées.")
        except APIConnectionError:
            st.error("❌ Erreur réseau : Impossible de contacter les serveurs OpenAI. Vérifiez votre connexion.")
        except OpenAIError as e:
            st.error(f"❌ Erreur de l'API OpenAI : {str(e)}")
        except Exception as e:
            st.error(f"❌ Une erreur inattendue est survenue : {str(e)}")

    if st.session_state.summary_result:
        st.markdown("---")
        st.markdown(st.session_state.summary_result)
        st.download_button(
            label="💾 Télécharger la fiche de synthèse (.md)",
            data=st.session_state.summary_result,
            file_name="synthese_cours.md",
            mime="text/markdown",
        )


# ------------------------------------------------------------------------------
# ONGLET 2 : QUIZ INTERACTIF
# ------------------------------------------------------------------------------
with tab_quiz:
    st.markdown("### 🎯 Tester ses connaissances (Quiz QCM interactif)")
    st.write(
        "Mettez à l'épreuve votre compréhension grâce à un test généré sur-mesure avec score instantané."
    )

    col_q1, col_q2, col_q3 = st.columns([1, 1, 1.2])
    with col_q1:
        num_questions = st.select_slider(
            "Nombre de questions :", options=[3, 5, 8, 10], value=5
        )
    with col_q2:
        difficulty = st.selectbox(
            "Niveau de difficulté :", ["Facile", "Intermédiaire", "Avancé"], index=1
        )
    with col_q3:
        st.write("")
        st.write("")
        btn_generate_quiz = st.button("🚀 Créer le quiz", use_container_width=True)

    if btn_generate_quiz and check_prerequisites():
        try:
            with st.spinner("Génération des questions et vérification des réponses..."):
                quiz_response = call_generate_quiz(
                    client=client,
                    model=selected_model,
                    text=st.session_state.course_text,
                    num_questions=num_questions,
                    difficulty=difficulty,
                    temperature=temperature,
                )
                st.session_state.quiz_data = quiz_response.get("quiz", [])
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
        except AuthenticationError:
            st.error("❌ Échec d'authentification : Clé API OpenAI invalide.")
        except RateLimitError:
            st.error("❌ Quota OpenAI dépassé. Vérifiez vos crédits sur la plateforme OpenAI.")
        except APIConnectionError:
            st.error("❌ Problème de connexion internet vers l'API OpenAI.")
        except OpenAIError as e:
            st.error(f"❌ Erreur API : {str(e)}")
        except Exception as e:
            st.error(f"❌ Erreur lors de la création du quiz : {str(e)}")

    # Affichage du formulaire de Quiz interactif
    if st.session_state.quiz_data:
        st.markdown("---")
        st.markdown(f"#### 📝 Répondez aux {len(st.session_state.quiz_data)} questions ci-dessous :")

        with st.form(key="quiz_form"):
            for i, q in enumerate(st.session_state.quiz_data):
                q_id = q.get("id", i + 1)
                st.markdown(f"**Question {i+1} : {q.get('question')}**")

                selected_opt = st.radio(
                    f"Sélectionnez votre réponse pour la question {i+1} :",
                    options=q.get("options", []),
                    key=f"radio_q_{q_id}",
                    index=None,
                    label_visibility="collapsed",
                )
                st.session_state.quiz_answers[q_id] = selected_opt
                st.markdown("<br>", unsafe_allow_html=True)

            btn_submit_quiz = st.form_submit_button("✅ Valider mes réponses et voir mon score")

        if btn_submit_quiz:
            st.session_state.quiz_submitted = True

        # Affichage du score et du corrigé
        if st.session_state.quiz_submitted:
            score = 0
            total = len(st.session_state.quiz_data)

            st.markdown("### 🏆 Résultats & Corrigé détaillé")

            for i, q in enumerate(st.session_state.quiz_data):
                q_id = q.get("id", i + 1)
                user_choice = st.session_state.quiz_answers.get(q_id)
                correct_letter = str(q.get("correct_answer", "")).strip().upper()
                explanation = q.get("explanation", "Aucune explication fournie.")

                # Vérification de la correspondance (ex: 'A' correspond à l'option commençant par 'A)')
                is_correct = False
                if user_choice:
                    user_letter = user_choice.strip()[0].upper()
                    if user_letter == correct_letter:
                        is_correct = True
                        score += 1

                with st.expander(
                    f"Question {i+1} : {'✅ Correct' if is_correct else '❌ Incorrect'} - {q.get('question')}",
                    expanded=not is_correct,
                ):
                    st.write(f"**Votre réponse :** {user_choice if user_choice else '*(Aucune sélection)*'}")
                    st.write(f"**Bonne réponse attendue :** Option ({correct_letter})")
                    if is_correct:
                        st.success(f"💡 **Explication :** {explanation}")
                    else:
                        st.error(f"💡 **Explication :** {explanation}")

            # Calcul et affichage final du badge de score
            percentage = int((score / total) * 100) if total > 0 else 0
            if percentage >= 80:
                badge_color = "#DCFCE7; color: #166534"
                appreciation = "🎉 Excellent travail ! La notion est parfaitement maîtrisée."
            elif percentage >= 50:
                badge_color = "#FEF9C3; color: #854D0E"
                appreciation = "👍 Bon résultat ! Quelques relectures cibleront vos dernières hésitations."
            else:
                badge_color = "#FEE2E2; color: #991B1B"
                appreciation = "📚 Révisez encore un peu le cours à l'aide de la fiche de synthèse !"

            st.markdown(
                f"""
                <div class="score-badge" style="background-color: {badge_color};">
                    Score : {score} / {total} ({percentage}%)
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.info(appreciation)


# ------------------------------------------------------------------------------
# ONGLET 3 : FLASHCARDS DE RÉVISION
# ------------------------------------------------------------------------------
with tab_flashcards:
    st.markdown("### 💡 Flashcards de Révision Active")
    st.write(
        "Cartes mémo conçues pour stimuler le rappel actif (Active Recall) et exporter vers Anki."
    )

    col_fc1, col_fc2 = st.columns([2, 1])
    with col_fc1:
        num_cards = st.select_slider("Nombre de flashcards :", options=[4, 6, 8, 12], value=6)
    with col_fc2:
        st.write("")
        st.write("")
        btn_generate_fc = st.button("🎴 Générer les flashcards", use_container_width=True)

    if btn_generate_fc and check_prerequisites():
        try:
            with st.spinner("Conception des cartes de mémorisation active..."):
                fc_response = call_generate_flashcards(
                    client=client,
                    model=selected_model,
                    text=st.session_state.course_text,
                    num_cards=num_cards,
                    temperature=temperature,
                )
                st.session_state.flashcards_data = fc_response.get("flashcards", [])
        except AuthenticationError:
            st.error("❌ Échec d'authentification : Clé API OpenAI invalide.")
        except RateLimitError:
            st.error("❌ Quota OpenAI dépassé.")
        except APIConnectionError:
            st.error("❌ Impossible d'accéder au service OpenAI.")
        except OpenAIError as e:
            st.error(f"❌ Erreur API : {str(e)}")
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération des flashcards : {str(e)}")

    if st.session_state.flashcards_data:
        st.markdown("---")
        cards = st.session_state.flashcards_data

        st.markdown(f"#### 🎴 {len(cards)} Flashcards disponibles :")

        # Affichage interactif en grille de 2 colonnes
        for i in range(0, len(cards), 2):
            cols = st.columns(2)
            for j in range(2):
                idx = i + j
                if idx < len(cards):
                    card = cards[idx]
                    with cols[j]:
                        with st.expander(f"📌 Carte {idx+1} : {card.get('front')}", expanded=False):
                            st.markdown(f"**Recto (Question/Notion) :**\n\n{card.get('front')}")
                            st.divider()
                            st.markdown(f"**Verso (Réponse/Définition) :**\n\n{card.get('back')}")
                            if card.get("category"):
                                st.caption(f"🏷️ Thème : *{card.get('category')}*")

        st.markdown("---")
        st.subheader("📥 Exporter vos flashcards")

        # Génération du format Anki (séparateur point-virgule)
        anki_csv_rows = ["Front;Back;Tag"]
        for card in cards:
            front = card.get("front", "").replace(";", ",").replace("\n", " ")
            back = card.get("back", "").replace(";", ",").replace("\n", " ")
            tag = card.get("category", "mon-outil-ia").replace(";", ",")
            anki_csv_rows.append(f"{front};{back};{tag}")
        anki_csv_data = "\n".join(anki_csv_rows)

        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            st.download_button(
                label="📁 Télécharger pour Anki (CSV / Délimiteur ';')",
                data=anki_csv_data,
                file_name="flashcards_anki.csv",
                mime="text/csv",
                help="Importez directement ce fichier CSV dans Anki en choisissant ';' comme séparateur.",
            )
        with col_exp2:
            # Génération format Markdown
            md_content = "# Flashcards de Révision\n\n"
            for c in cards:
                md_content += f"### {c.get('front')}\n\n**Réponse :** {c.get('back')}\n\n*Thème : {c.get('category')}*\n\n---\n\n"
            st.download_button(
                label="📄 Télécharger au format Markdown (.md)",
                data=md_content,
                file_name="flashcards.md",
                mime="text/markdown",
            )
