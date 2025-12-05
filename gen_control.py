import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import urllib.parse

# ==========================================
# 1. DESIGN "DARK MODE" & CONFIG
# ==========================================
st.set_page_config(
    page_title="GEN-CONTROL V3",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS pour le look "Expert/Sombre" et cacher les éléments Streamlit
st.markdown("""
<style>
    /* Force Dark Theme colors if user theme is light */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .stTextInput > div > div > input {
        color: #FAFAFA;
        background-color: #262730;
    }
    .stNumberInput > div > div > input {
        color: #FAFAFA;
        background-color: #262730;
    }
    /* Cacher menu et footer */
    .stDeployButton {display:none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Style des métriques */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: bold;
    }
    
    /* Bouton principal */
    div.stButton > button:first-child {
        background-color: #FF4B4B;
        color: white;
        font-size: 20px;
        font-weight: bold;
        border-radius: 10px;
        padding: 10px 24px;
        border: none;
    }
    div.stButton > button:first-child:hover {
        background-color: #FF0000;
        border: 1px solid white;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONNEXION DATABASE
# ==========================================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    st.error("⚠️ Erreur réseau. Vérifiez votre connexion.")
    st.stop()

# ==========================================
# 3. SESSION STATE
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = {}
if 'audit_result' not in st.session_state:
    st.session_state.audit_result = None

# ==========================================
# 4. LOGIQUE MÉTIER
# ==========================================
def log_action(code, action, details="-"):
    try:
        df_logs = conn.read(worksheet="logs", ttl=0, usecols=[0, 1, 2, 3])
        new_entry = pd.DataFrame([{
            "date_heure": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "code_utilise": code,
            "action": action,
            "details": details
        }])
        updated_logs = pd.concat([df_logs, new_entry], ignore_index=True)
        conn.update(worksheet="logs", data=updated_logs)
    except:
        pass

def check_login(code_input):
    try:
        df_users = conn.read(worksheet="users", ttl=0, usecols=[0, 1, 2, 3])
        df_users['code_acces'] = df_users['code_acces'].astype(str).str.strip()
        user_row = df_users[(df_users['code_acces'] == code_input) & (df_users['statut'] == 'ACTIF')]
        if not user_row.empty:
            return True, user_row.iloc[0]['client_nom']
        return False, None
    except:
        return False, None

# ==========================================
# 5. ÉCRAN LOGIN
# ==========================================
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: white;'>🔐 GEN-CONTROL</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #888;'>SÉCURITÉ ÉNERGÉTIQUE</h4>", unsafe_allow_html=True)
    st.write("")
    st.write("")
    
    code_input = st.text_input("Entrez votre Code Licence", placeholder="Ex: GEN-2025-X").strip()
    
    if st.button("ACCÉDER AU SYSTÈME", type="primary", use_container_width=True):
        if code_input:
            is_valid, client_name = check_login(code_input)
            if is_valid:
                st.session_state.authenticated = True
                st.session_state.user_info = {"code": code_input, "nom": client_name}
                log_action(code_input, "LOGIN", f"Succès - {client_name}")
                st.rerun()
            else:
                st.error("⛔ Accès Refusé.")

# ==========================================
# 6. ÉCRAN AUDIT (V3)
# ==========================================
else:
    # Sidebar pour déconnexion (plus propre)
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user_info['nom']}**")
        if st.button("Déconnexion"):
            st.session_state.authenticated = False
            st.session_state.audit_result = None
            st.rerun()

    st.markdown("### 🚀 Configuration de l'Audit")
    
    # --- 1. IDENTIFICATION ---
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            entreprise = st.text_input("Site / Immatriculation", placeholder="Ex: Usine A ou LT 123 AB")
        with c2:
            contact = st.text_input("WhatsApp Contact", placeholder="6XX XX XX XX")

    st.markdown("---")

    # --- 2. SÉLECTEUR D'ÉQUIPEMENT ---
    type_equipement = st.radio("Quel équipement auditez-vous ?", ["🏭 Groupe Électrogène", "🚛 Camion / Engin TP"], horizontal=True)

    col_tech1, col_tech2 = st.columns(2)
    
    facteur_charge = 0.5 # Defaut
    puissance_kw_calcul = 0.0

    if type_equipement == "🏭 Groupe Électrogène":
        with col_tech1:
            puissance_input = st.number_input("Puissance du Groupe (kVA)", min_value=10, value=100, step=10)
            # Conversion kVA -> kW (Cos phi 0.8 par défaut)
            puissance_kw_calcul = puissance_input * 0.8 
        
        with col_tech2:
            scenario = st.selectbox("Profil d'utilisation", [
                "🏢 Bureaux / Hôtel (Nuit/Faible) - 30%",
                "🏪 Activité Standard (Moyen) - 50%",
                "🏗️ Chantier / Usine (Élevé) - 75%",
                "⚡ Pleine Puissance (Max) - 90%"
            ])
            if "30%" in scenario: facteur_charge = 0.30
            elif "50%" in scenario: facteur_charge = 0.50
            elif "75%" in scenario: facteur_charge = 0.75
            elif "90%" in scenario: facteur_charge = 0.90

    else: # CAMION
        with col_tech1:
            puissance_input = st.number_input("Puissance Moteur (CV / Chevaux)", min_value=50, value=300, step=10)
            # Conversion CV -> kW (1 CV = 0.7355 kW)
            puissance_kw_calcul = puissance_input * 0.7355
        
        with col_tech2:
            scenario = st.selectbox("Type de Trajet / Mission", [
                "🛣️ Route Plate / Vide / Eco - 40%",
                "🏙️ Ville / Livraison / Mixte - 50%",
                "📦 Route Chargée / Vallonnée - 70%",
                "🚜 Chantier TP / Terrain difficile - 80%"
            ])
            if "40%" in scenario: facteur_charge = 0.40
            elif "50%" in scenario: facteur_charge = 0.50
            elif "70%" in scenario: facteur_charge = 0.70
            elif "80%" in scenario: facteur_charge = 0.80

    # --- 3. DONNÉES CONSO ---
    st.markdown("---")
    c_h, c_l, c_p = st.columns(3)
    with c_h:
        heures = st.number_input("Heures / Durée (h)", min_value=1, value=10)
    with c_l:
        litres = st.number_input("Carburant Déclaré (L)", min_value=1, value=100)
    with c_p:
        prix = st.number_input("Prix du Litre", value=750)

    # --- BOUTON CALCUL ---
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("LANCER L'AUDIT DE SÉCURITÉ 🚨", type="primary", use_container_width=True):
        if not entreprise:
            st.warning("Nom du site requis.")
        else:
            # Moteur de calcul unifié (Willans simplifié)
            # Conso (L/h) = P_kw * CSP * (0.1 + 0.9 * charge)
            # CSP Diesel Industriel ~ 0.24 L/kWh
            csp = 0.24
            
            conso_h_theo = puissance_kw_calcul * csp * (0.1 + (0.9 * facteur_charge))
            total_theo = conso_h_theo * heures
            
            ecart = litres - total_theo
            ecart_pct = (ecart / total_theo) * 100
            perte = ecart * prix

            st.session_state.audit_result = {
                "theo": total_theo, "reel": litres, "ecart": ecart,
                "pct": ecart_pct, "perte": perte, "site": entreprise,
                "charge": facteur_charge, "type": type_equipement
            }
            
            # Log
            log_action(st.session_state.user_info['code'], "CALCUL", f"{ecart_pct:.1f}% | {perte:.0f}F | {entreprise}")

    # --- RÉSULTATS ---
    if st.session_state.audit_result:
        r = st.session_state.audit_result
        st.markdown("---")
        
        # Diagnostic
        if r['ecart'] > (r['theo'] * 0.12): # Tolérance 12%
            color = "#FF4B4B" # Rouge
            msg = "ANOMALIE DÉTECTÉE : VOL SUSPECTÉ"
            icon = "🚨"
        elif r['ecart'] < -(r['theo'] * 0.12):
            color = "#FFA500" # Orange
            msg = "SOUS-CONSOMMATION (Vérifier données)"
            icon = "⚠️"
        else:
            color = "#00C853" # Vert
            msg = "CONSO COHÉRENTE (RAS)"
            icon = "✅"

        # Affichage CARTE
        st.markdown(f"""
        <div style="background-color: {color}20; border: 2px solid {color}; padding: 20px; border-radius: 10px; text-align: center;">
            <h2 style="color: {color}; margin:0;">{icon} {msg}</h2>
            <hr style="border-color: {color}; opacity: 0.3;">
            <div style="display: flex; justify-content: space-around; margin-top: 15px;">
                <div>
                    <div style="font-size: 14px; color: #aaa;">THÉORIQUE</div>
                    <div style="font-size: 24px; font-weight: bold;">{r['theo']:.1f} L</div>
                </div>
                <div>
                    <div style="font-size: 14px; color: #aaa;">DÉCLARÉ</div>
                    <div style="font-size: 24px; font-weight: bold;">{r['reel']:.1f} L</div>
                </div>
                <div>
                    <div style="font-size: 14px; color: #aaa;">ÉCART</div>
                    <div style="font-size: 24px; font-weight: bold; color: {color};">{r['ecart']:+.1f} L</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Call to Action si Vol
        if "VOL" in msg:
            st.error(f"💸 IMPACT FINANCIER : - {r['perte']:,.0f} FCFA")
            whatsapp_url = f"https://wa.me/237671894095?text=Alerte%20Vol%20{r['site']}%20:%20Ecart%20{r['pct']:.1f}%25%20({r['perte']:.0f}F)"
            st.link_button("📞 CONTACTER L'EXPERT MAINTENANT", whatsapp_url, type="primary", use_container_width=True)

        # Rapport Texte
        rapport = f"""AUDIT GEN-CONTROL V3
📅 {datetime.now().strftime('%d/%m/%Y')}
📍 {r['site']} ({r['type']})
⚙️ Charge Estimée : {r['charge']*100:.0f}%
⛽ Conso Déclarée : {r['reel']:.1f} L
📉 Conso Normale : {r['theo']:.1f} L
⚠️ ÉCART : {r['ecart']:+.1f} L ({r['pct']:+.1f}%)
💰 VALEUR : {r['perte']:,.0f} FCFA
Verdict : {msg}"""
        
        st.text_area("📋 Copier le rapport", rapport, height=200)