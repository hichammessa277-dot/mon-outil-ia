<div align="center">

# 🎓 mon-outil-ia

**L'assistant d'étude intelligent open-source propulsé par Streamlit et l'API OpenAI.**

Transformez des cours denses en synthèses pédagogiques limpides, testez votre compréhension avec des quiz interactifs et révisez efficacement grâce à des flashcards exportables vers Anki.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI_API-v1.0%2B-412991.svg?logo=openai&logoColor=white)](https://platform.openai.com/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

## 📖 Sommaire

- [🌟 Valeur ajoutée & Vision](#-valeur-ajoutée--vision)
- [✨ Fonctionnalités Principales](#-fonctionnalités-principales)
- [🏗️ Architecture Technique](#️-architecture-technique)
- [🚀 Démarrage Rapide](#-démarrage-rapide)
  - [Prérequis](#prérequis)
  - [Installation Pas à Pas](#installation-pas-à-pas)
  - [Lancement de l'Application](#lancement-de-lapplication)
- [🔑 Gestion de la Clé API OpenAI](#-gestion-de-la-clé-api-openai)
- [🌐 Déploiement sur Streamlit Community Cloud](#-déploiement-sur-streamlit-community-cloud)
- [🤝 Guide de Contribution](#-guide-de-contribution)
- [🛣️ Feuille de Route (Roadmap)](#️-feuille-de-route-roadmap)
- [📄 Licence](#-licence)

---

## 🌟 Valeur ajoutée & Vision

Face à la surcharge informationnelle et aux polycopiés de cours de plusieurs dizaines de pages, les étudiants perdent un temps précieux à synthétiser manuellement leurs cours avant même de commencer à réviser.

**`mon-outil-ia`** met la puissance des modèles d'IA générative les plus récents (comme `gpt-4o-mini` et `gpt-4o`) directement au service de l'apprentissage actif :
- **Fini la lecture passive** : passage immédiat à la pratique grâce à des quiz interactifs générés à la volée.
- **Démystification des concepts ardus** : vulgarisation s'appuyant sur la méthode Feynman et analogies concrètes.
- **Mémorisation à long terme** : fiches de révision et flashcards prêtes pour la répétition espacée (Spaced Repetition) sur Anki.

---

## ✨ Fonctionnalités Principales

| Module | Description | Particularité |
| :--- | :--- | :--- |
| **📝 Synthèse & Vulgarisation** | 3 modes d'adaptation : vulgarisation débutant (Feynman), synthèse académique structurée ou fiche mémo à puces. | Téléchargement direct en Markdown (`.md`). |
| **🎯 Quiz Interactif (QCM)** | Génération de 3 à 10 questions avec choix multiples, corrigé détaillé et calcul dynamique du score. | Persistance d'état via `st.session_state` & feedback visuel. |
| **💡 Flashcards de Révision** | Extraction des définitions, formules et notions clés sous forme de cartes Recto / Verso. | Export Anki (`.csv`) avec délimiteur point-virgule et export Markdown. |
| **⚡ Exemple en 1 Clic** | Chargement instantané d'un cours d'exemple sur le modèle réseau OSI. | Permet d'explorer l'outil sans avoir de texte sous la main. |

---

## 🏗️ Architecture Technique

L'application repose sur une architecture légère, découplée et réactive :

```
                          ┌───────────────────────────┐
                          │   Utilisateur / Étudiant  │
                          └─────────────┬─────────────┘
                                        │ (Texte du cours / Notes)
                                        ▼
    ┌───────────────────────────────────────────────────────────────────────┐
    │                        Interface Streamlit (app.py)                   │
    │  - Saisie & configuration (modèle, température, clé API)              │
    │  - Gestion d'état réactive (st.session_state)                         │
    │  - Navigation par onglets & formulaires interactifs                   │
    └───────────────────────────────────┬───────────────────────────────────┘
                                        │
                         Appels API OpenAI (SDK v1+)
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 ▼                                             ▼
    ┌──────────────────────────┐                  ┌──────────────────────────┐
    │   Synthèse / Vulgarisation │                  │   Génération Structurée  │
    │   (Format Markdown brut) │                  │   (response_format=JSON) │
    └──────────────────────────┘                  └─────────────┬────────────┘
                                                                │
                                              ┌─────────────────┴─────────────────┐
                                              ▼                                   ▼
                                     [ Quiz QCM (Objets) ]              [ Flashcards (Recto/Verso) ]
                                              │                                   │
                                              ▼                                   ▼
                                     Correction & Score                  Export Anki (.CSV)
```

### Intégration du SDK OpenAI (`openai>=1.0.0`)
- **JSON Mode Garanti** : Utilisation de `response_format={"type": "json_object"}` pour les quiz et flashcards, éliminant tout risque d'erreur d'analyse syntaxique (parsing).
- **Modèles Supportés** : `gpt-4o-mini` (par défaut, ultra-rapide et économique), `gpt-4o` (haute précision analytique) et `gpt-3.5-turbo`.
- **Résilience & Gestion d'erreurs** : Traitement explicite des exceptions du SDK :
  - `openai.AuthenticationError` : alerte sur clé invalide.
  - `openai.RateLimitError` : gestion des quotas dépassés.
  - `openai.APIConnectionError` : perte de connectivité réseau.

---

## 🚀 Démarrage Rapide

### Prérequis
- **Python 3.9+** installé sur votre machine.
- Une **clé d'API OpenAI** valide ([accessible ici](https://platform.openai.com/api-keys)).

### Installation Pas à Pas

1. **Cloner le dépôt :**
   ```bash
   git clone https://github.com/votre-nom-utilisateur/mon-outil-ia.git
   cd mon-outil-ia
   ```

2. **Créer et activer un environnement virtuel :**
   - **Sous Windows (PowerShell) :**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Sous Linux / macOS :**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Installer les dépendances requises :**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configurer votre clé d'API OpenAI :**
   Dupliquez le fichier `.env.example` en `.env` :
   - **Sous Windows :**
     ```powershell
     copy .env.example .env
     ```
   - **Sous Linux / macOS :**
     ```bash
     cp .env.example .env
     ```
   Ouvrez le fichier `.env` et collez votre clé :
   ```env
   OPENAI_API_KEY=sk-proj-votre_cle_api_secrete_ici
   ```

### Lancement de l'Application

Lancez le serveur local Streamlit :
```bash
streamlit run app.py
```
L'application s'ouvrira automatiquement dans votre navigateur par défaut à l'adresse `http://localhost:8501`.

---

## 🔑 Gestion de la Clé API OpenAI

Pour une flexibilité maximale et une sécurité accrue :
1. **Mode Fichier `.env` (Recommandé en local)** : La clé est détectée automatiquement sans avoir besoin de la ressaisir à chaque redémarrage.
2. **Mode Saisie Directe (Interface graphique)** : Si aucun fichier `.env` n'est configuré, l'application propose un champ masqué sécurisé (`type="password"`) dans la barre latérale. Votre clé reste cantonnée à votre session locale.

---

## 🌐 Déploiement sur Streamlit Community Cloud

Vous pouvez héberger gratuitement ce projet en quelques secondes sur [Streamlit Community Cloud](https://streamlit.io/cloud) :

1. Poussez votre code sur un dépôt GitHub public.
2. Connectez-vous sur Streamlit Cloud et sélectionnez votre dépôt.
3. Définissez le fichier d'entrée : `app.py`.
4. Dans **Advanced Settings > Secrets**, configurez votre clé API :
   ```toml
   OPENAI_API_KEY = "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx"
   ```
5. Cliquez sur **Deploy** !

---

## 🤝 Guide de Contribution

Les contributions de la communauté sont les bienvenues ! Que ce soit pour signaler un bogue, proposer une amélioration ou ajouter de nouvelles fonctionnalités :

1. **Forkez** le projet.
2. **Créez une branche** pour votre fonctionnalité :
   ```bash
   git checkout -b feature/nouvelle-fonctionnalite
   ```
3. **Committez** vos modifications en suivant la convention [Conventional Commits](https://www.conventionalcommits.org/) :
   ```bash
   git commit -m "feat: ajout de l'export PDF des fiches de synthèse"
   ```
4. **Poussez** vers votre branche :
   ```bash
   git push origin feature/nouvelle-fonctionnalite
   ```
5. Ouvrez une **Pull Request** détaillée décrivant vos changements.

---

## 🛣️ Feuille de Route (Roadmap)

- [ ] 📄 **Support direct de fichiers PDF** : Import et extraction automatique de polycopiés et diapositives.
- [ ] 🎙️ **Transcription Audio avec Whisper** : Enregistrement de cours magistraux ou import de mémos vocaux.
- [ ] 📦 **Export `.apkg` natif** : Génération directe de paquets Anki avec métadonnées complètes.
- [ ] 🌐 **Support Multilingue** : Détection automatique et révision de langues vivantes (anglais, espagnol, etc.).

---

## 📄 Licence

Ce projet est sous licence **MIT**. Vous êtes libre de l'utiliser, le modifier et le distribuer, tant pour des projets personnels que commerciaux. Voir le fichier [LICENSE](LICENSE) pour plus de précisions.
