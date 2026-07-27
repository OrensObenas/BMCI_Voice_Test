import os
import re
import json
import time
import subprocess
import requests
import psutil
import streamlit as st
from pathlib import Path

# --- Configuration de la page ---
st.set_page_config(
    page_title="BMCI - LiveKit Pipeline Manager",
    page_icon="🎙️",
    layout="wide",
)

# --- Thème visuel personnalisé ---
st.markdown("""
    <style>
        /* Thème sombre premium */
        .main {
            background-color: #0A192F;
            color: #E2E8F0;
        }
        h1, h2, h3 {
            color: #FFFFFF !important;
            font-family: 'Arial', sans-serif;
        }
        .stButton>button {
            background-color: #10B981 !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 6px !important;
            padding: 0.6rem 1.2rem !important;
            font-weight: bold !important;
            transition: all 0.3s ease !important;
        }
        .stButton>button:hover {
            background-color: #059669 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
        }
        .stTextArea textarea {
            background-color: #1E293B !important;
            color: #E2E8F0 !important;
            border: 1px solid #334155 !important;
            border-radius: 6px !important;
        }
        .stTextInput input {
            background-color: #1E293B !important;
            color: #E2E8F0 !important;
            border: 1px solid #334155 !important;
            border-radius: 6px !important;
        }
        .stSelectbox div[data-baseweb="select"] {
            background-color: #1E293B !important;
            color: #E2E8F0 !important;
        }
        .stAlert {
            background-color: #1E293B !important;
            border: 1px solid #334155 !important;
            color: #E2E8F0 !important;
        }
        /* Style console logs */
        .console-logs {
            background-color: #0F172A;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 1rem;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.85rem;
            color: #10B981;
            height: 250px;
            overflow-y: scroll;
            white-space: pre-wrap;
        }
    </style>
""", unsafe_allow_html=True)

# --- Chemins d'accès ---
APP_DIR = Path(__file__).resolve().parent
ENV_PATH = APP_DIR / ".env"
SCENARIO_FILE = APP_DIR / "current_scenario.txt"
LOG_FILE = APP_DIR / "agent_run.log"

# --- Charger la clé Mistral depuis .env ---
def get_mistral_api_key():
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MISTRAL_API_KEY="):
                    return line.strip().split("=")[1]
    return os.environ.get("MISTRAL_API_KEY", "")

# --- Gestion des processus du worker LiveKit ---
def get_agent_status():
    """Vérifie si le script agent.py ou run_agent.py tourne sur la machine."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if cmdline:
                cmd_str = " ".join(cmdline)
                if "run_agent.py" in cmd_str or "agent.py dev" in cmd_str:
                    return True, proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False, None

def start_pipeline():
    """Démarre run_agent.py en arrière-plan."""
    running, pid = get_agent_status()
    if running:
        return f"La pipeline est déjà en cours d'exécution (PID: {pid})."
    
    python_exe = Path(os.sys.executable)
    script_path = APP_DIR / "run_agent.py"
    
    # Ouvrir le fichier de log
    log_f = open(LOG_FILE, "w", encoding="utf-8")
    
    # Lancer le processus en arrière-plan
    subprocess.Popen(
        [str(python_exe), "-u", str(script_path)],
        cwd=str(APP_DIR),
        stdout=log_f,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    )
    time.sleep(1.5)
    return "La pipeline LiveKit a été lancée avec succès !"

def stop_pipeline():
    """Arrête tous les processus liés à la pipeline vocal LiveKit."""
    killed = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if cmdline:
                cmd_str = " ".join(cmdline)
                if "run_agent.py" in cmd_str or "agent.py dev" in cmd_str:
                    proc.terminate()
                    killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    if killed > 0:
        return f"Pipeline arrêtée ({killed} processus terminés)."
    return "Aucun processus de pipeline actif trouvé."

# --- Scénarios prédéfinis de la BMCI ---
PREDEFINED_SCENARIOS = {
    "M. Orens (Retrait Urgent 100K) [Défaut]": """Tu es M. Orens, un client de la banque Atlas Bank. Tu es extrêmement furieux, fâché, agressif et très pressé. 
Tu viens de te déplacer en agence pour retirer 100 000 dirhams en liquide, mais la conseillère t'annonce que la limite de retrait sans préavis est de 50 000 dirhams par jour.

Consignes de rôle pour la simulation :
- Tu es hors de toi, cinglant et agressif. Tu refuses d'emblée toutes les excuses ou explications administratives de la conseillère. Tu trouves absurde et inadmissible de ne pas pouvoir retirer ton propre argent.
- Ton ton est hautain, impatient, irrité et sans filtre. Tu montres ouvertement ton mécontentement ("c'est une blague ?", "vous vous moquez de moi ?", "je m'en fiche de vos limites !").
- Tu n'expliques pourquoi tu as absolument besoin de cette somme (acheter une maison, le vendeur attend l'argent aujourd'hui à midi sinon il vend à quelqu'un d'autre) QUE si la conseillère est très patiente et te le demande poliment.
- Tu es extrêmement méfiant face aux solutions alternatives (comme le virement). Tu ne te laisses convaincre que si la conseillère t'assure patiemment qu'il arrivera aujourd'hui avant midi sans aucun risque de retard.
- Réponds avec des phrases courtes, directes, sèches, agressives et très naturelles (langage parlé). Ne fais pas de longues phrases ou de listes.""",

    "Mme. Kabbaj (Carte Avalée & Voyage Imminent)": """Tu es Mme. Kabbaj, une cliente de la BMCI très inquiète, nerveuse et paniquée.
Ta carte bancaire vient d'être avalée par le guichet automatique de l'agence, et tu as un vol international pour un voyage d'affaires ce soir à 20h. Tu as absolument besoin de ta carte ou d'un moyen de paiement.

Consignes de rôle pour la simulation :
- Tu es très stressée, tu parles vite et tu refuses d'attendre les délais habituels de 48 heures pour récupérer la carte.
- Tu insistes sur le fait que c'est une faute de la banque et que ta vie professionnelle est en jeu si tu pars sans ta carte.
- Tu es réticente à l'idée d'ouvrir une carte de secours temporaire sauf si on t'assure qu'elle est gratuite et activable dans les 10 minutes.
- Ne fais pas de longues phrases. Utilise un vocabulaire familier, pressant et stressé.
- Interdiction de faire des listes de points ou d'écrire en MAJUSCULES.""",

    "M. Tazi (Frais Bancaires Abusifs)": """Tu es M. Tazi, un client fidèle de la BMCI depuis 15 ans. Tu es calme mais froid, ferme et très déterminé.
Tu viens de consulter ton relevé et tu as constaté des frais de tenue de compte exceptionnels de 450 dirhams que tu juges injustifiés et abusifs.

Consignes de rôle pour la simulation :
- Tu refuses de payer ces frais et tu demandes un remboursement immédiat. Tu rappelles ton historique de fidélité et le fait que tu n'as jamais eu d'incident.
- Si le conseiller te parle de conditions générales ou de grilles tarifaires, tu menaces de fermer tous tes comptes et de transférer tes avoirs à la concurrence.
- Tu restes courtois mais extrêmement rigide. Tu n'acceptes pas de compromis à mi-chemin (ex: remboursement partiel). Tu veux le remboursement intégral ou tu demandes à parler au directeur d'agence.
- Reste sur des réponses directes et fermes, sans didascalies entre crochets.""",
}

# --- Générateur de scénario par IA ---
def generate_scenario_ai(instruction: str, api_key: str) -> str:
    if not api_key:
        return "Erreur : Clé d'API Mistral introuvable dans le fichier .env ou non fournie."
    
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""Tu es un expert en formation pour les conseillers de la BMCI. 
Génère le prompt système d'instructions pour un agent vocal de jeu de rôle simulant un client bancaire en fonction de la consigne suivante :
"{instruction}"

Le prompt système doit obligatoirement respecter ces règles :
1. Être écrit à la deuxième personne ("Tu es...") en décrivant le nom du client, sa situation, et son état d'esprit (fâché, stressé, méfiant, etc.).
2. Détailler les consignes précises de comportement (ce qu'il refuse d'abord, ce qu'il accepte sous condition).
3. Inclure impérativement la consigne de formatage textuel suivante à la fin du prompt :
"Instructions importantes pour le formatage du texte :
- Ne génère JAMAIS de texte entre crochets (comme [sighs], [gasp], [laughs] ou [whispers]) ni de texte entre astérisques (comme *soupir*). Tout ton texte doit uniquement être du dialogue parlé.
- N'écris JAMAIS de mots entièrement en MAJUSCULES (comme MON, QUOI, JAMAIS). Les majuscules provoquent des erreurs de prononciation de la synthèse vocale."

Donne uniquement les instructions système prêtes à être copiées, sans aucune phrase d'introduction ni de conclusion."""

    payload = {
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Erreur lors de l'appel à Mistral AI : {e}"


# --- Interface Streamlit ---
st.title("🎙️ BMCI - LiveKit Vocal Pipeline Manager")
st.write("Interface d'administration pour configurer et piloter en temps réel l'agent de simulation bancaire.")

tab_scenario, tab_control = st.tabs(["📝 Gestion du Scénario", "⚡ Contrôle de la Pipeline"])

# --- TAB 1: GESTION DU SCÉNARIO ---
with tab_scenario:
    st.subheader("1. Sélectionner ou Configurer le Scénario")
    
    # Sélection de scénarios prédéfinis
    selected_option = st.selectbox("Choisir un scénario BMCI existant :", list(PREDEFINED_SCENARIOS.keys()))
    predefined_prompt = PREDEFINED_SCENARIOS[selected_option]
    
    st.markdown("---")
    st.subheader("🤖 Générateur de Scénario par IA (Mistral)")
    user_instruction = st.text_area(
        "Consigne de départ (ex: 'Un client dont le virement de 20 000 DH vers l'étranger n'est pas arrivé et qui accuse l'agence d'incompétence') :",
        key="generation_input",
        height=70
    )
    
    if st.button("Générer le scénario sur-mesure"):
        if not user_instruction.strip():
            st.warning("Veuillez saisir une consigne avant de lancer la génération.")
        else:
            with st.spinner("Génération du scénario en cours..."):
                api_key = get_mistral_api_key()
                generated_prompt = generate_scenario_ai(user_instruction, api_key)
                st.session_state["active_prompt"] = generated_prompt
                st.success("Scénario généré avec succès par l'IA !")
    
    st.markdown("---")
    st.subheader("✏️ Édition des Instructions Système Actives")
    
    # Récupérer le prompt actif
    if "active_prompt" not in st.session_state:
        st.session_state["active_prompt"] = predefined_prompt
    
    # Mettre à jour si sélection d'un scénario prédéfini change
    if st.button("Charger le scénario sélectionné ci-dessus"):
        st.session_state["active_prompt"] = predefined_prompt
        
    active_prompt_text = st.text_area(
        "Ce prompt définit les instructions du client IA (lu par l'agent vocal en temps réel) :",
        value=st.session_state["active_prompt"],
        height=280
    )
    
    # Appliquer le scénario
    if st.button("💾 Appliquer ce scénario à l'agent vocal"):
        try:
            with open(SCENARIO_FILE, "w", encoding="utf-8") as f:
                f.write(active_prompt_text)
            st.success("Le scénario a été appliqué avec succès ! La prochaine conversation utilisera ce profil de client.")
        except Exception as e:
            st.error(f"Erreur d'écriture du scénario : {e}")

# --- TAB 2: CONTRÔLE DE LA PIPELINE ---
with tab_control:
    st.subheader("⚡ Supervision de la Pipeline LiveKit")
    
    # Statut actuel
    running, pid = get_agent_status()
    col_status, col_btn_start, col_btn_stop = st.columns([2, 1, 1])
    
    with col_status:
        if running:
            st.markdown(f"**Statut** : 🟢 **Actif** (PID: `{pid}`)")
        else:
            st.markdown("**Statut** : 🔴 **Arrêté**")
            
    with col_btn_start:
        if st.button("🚀 Démarrer l'Agent Vocal"):
            msg = start_pipeline()
            st.info(msg)
            st.rerun()
            
    with col_btn_stop:
        if st.button("🛑 Arrêter l'Agent Vocal"):
            msg = stop_pipeline()
            st.info(msg)
            st.rerun()
            
    st.markdown("---")
    st.subheader("🔗 Tester la conversation vocale")
    st.markdown("""
    Une fois la pipeline démarrée (Statut : Actif), vous pouvez vous connecter au bac à sable WebRTC de la BMCI pour parler en direct avec l'agent :
    
    👉 **[Accéder au Playground LiveKit BMCI](https://internship-obt2eynj.livekit.cloud)**
    
    *(Note : Autorisez l'accès à votre microphone, puis parlez en premier pour lancer le dialogue avec le client)*
    """)
    
    st.markdown("---")
    st.subheader("📋 Logs en temps réel de l'agent")
    
    # Affichage des logs en direct
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                log_lines = f.readlines()[-30:]  # Lire les 30 dernières lignes
            log_content = "".join(log_lines)
            st.markdown(f'<div class="console-logs">{log_content}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.text(f"Impossible de lire les logs : {e}")
    else:
        st.info("Aucun log généré pour le moment. Lancez la pipeline pour commencer.")

    # Bouton de rafraîchissement des logs
    if st.button("🔄 Rafraîchir les logs"):
        st.rerun()
