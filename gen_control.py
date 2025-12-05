import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import urllib.parse

# ==========================================
# 1. CONFIGURATION & DESIGN (LISIBILITÉ MAXIMALE)
# ==========================================
st.set_page_config(
    page_title="GEN-CONTROL V2",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS CORRECTIF : FORCER LE TEXTE EN BLANC ET AGRANDIR
st.markdown("""
<style>
    /* Fond global sombre professionnel */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    
    /* Forcer tous les labels et textes en BLANC et plus GRAS */
    .stTextInput label, .stNumberInput label, .stSelectbox label, .stRadio label {
        color: #FFFFFF !important;
        font-size: 16px !important;
        font-weight: 600 !important;
    }
    
    /* Champs de saisie plus contrastés */
    .stTextInput input, .stNumberInput input {
        color: #FFFFFF !important;
        background-color: #262730 !important;
        border: 1px solid #444 !important;
    }
    
    /* Titre Principal */
    h1 {
        color: #FF4B4B !important;
        text-transform: uppercase;
        font-weight: 900 !important;
    }
    
    /* Footer DI-SOLUTIONS */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0E1117;
        color: #888;
        text-align: center;
        padding: 10px;
        font-size: 12px;
        border-top: 1px solid #333;
    }
    
    /* Cacher éléments parasites */
    .stDeployButton {display:none;}
    #MainMenu {visibility: hidden;}
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
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>🔐 GEN-CONTROL V2</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #CCC;'>AUDIT & SÉCURITÉ ÉNERGÉTIQUE</h4>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        code_input = st.text_input("CODE D'ACCÈS LICENCE", placeholder="Ex: GEN-XXXX").strip()
        if st.button("DÉVERROUILLER L'ACCÈS 🔓", type="primary", use_container_width=True):
            if code_input:
                is_valid, client_name = check_login(code_input)
                if is_valid:
                    st.session_state.authenticated = True
                    st.session_state.user_info = {"code": code_input, "nom": client_name}
                    log_action(code_input, "LOGIN", f"Succès - {client_name}")
                    st.rerun()
                else:
                    st.error("⛔ Code Invalide ou Expiré.")

# ==========================================
# 6. ÉCRAN AUDIT
# ==========================================
else:
    # Sidebar
    with st.sidebar:
        st.success(f"👤 **{st.session_state.user_info['nom']}**")
        st.caption(f"Licence : {st.session_state.user_info['code']}")
        if st.button("Déconnexion"):
            st.session_state.authenticated = False
            st.session_state.audit_result = None
            st.rerun()

    # HEADER
    st.markdown("### ⛽ GEN-CONTROL V2")
    st.caption("Powered by Cabinet DI-SOLUTIONS")
    st.markdown("---")
    
    # 1. IDENTIFICATION (En Haut, clair et net)
    c1, c2 = st.columns(2)
    with c1:
        entreprise = st.text_input("SITE / IMMATRICULATION", placeholder="Ex: Usine A ou LT 123 AB")
    with c2:
        contact = st.text_input("WHATSAPP CONTACT", placeholder="6XX XX XX XX")

    # 2. SÉLECTEUR
    st.markdown("<br>", unsafe_allow_html=True)
    type_equipement = st.radio("QUEL ÉQUIPEMENT AUDITEZ-VOUS ?", ["🏭 GROUPE ÉLECTROGÈNE", "🚛 CAMION / ENGIN TP"], horizontal=True)

    col_tech1, col_tech2 = st.columns(2)
    facteur_charge = 0.5
    puissance_kw_calcul = 0.0

    if "GROUPE" in type_equipement:
        with col_tech1:
            puissance_input = st.number_input("PUISSANCE GROUPE (kVA)", min_value=10, value=100, step=10)
            puissance_kw_calcul = puissance_input * 0.8 
        with col_tech2:
            scenario = st.selectbox("PROFIL D'UTILISATION", [
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
            puissance_input = st.number_input("PUISSANCE MOTEUR (CV)", min_value=50, value=300, step=10)
            puissance_kw_calcul = puissance_input * 0.7355
        with col_tech2:
            scenario = st.selectbox("TYPE DE MISSION", [
                "🛣️ Route Plate / Vide / Eco - 40%",
                "🏙️ Ville / Livraison / Mixte - 50%",
                "📦 Route Chargée / Vallonnée - 70%",
                "🚜 Chantier TP / Terrain difficile - 80%"
            ])
            if "40%" in scenario: facteur_charge = 0.40
            elif "50%" in scenario: facteur_charge = 0.50
            elif "70%" in scenario: facteur_charge = 0.70
            elif "80%" in scenario: facteur_charge = 0.80

    # 3. DONNÉES CONSO
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📊 Relevés Terrain")
    c_h, c_l, c_p = st.columns(3)
    with c_h:
        heures = st.number_input("DURÉE (Heures)", min_value=1, value=10)
    with c_l:
        litres = st.number_input("CONSO DÉCLARÉE (L)", min_value=1, value=100)
    with c_p:
        prix = st.number_input("PRIX DU LITRE", value=750)

    # BOUTON CALCUL
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("LANCER L'AUDIT DE SÉCURITÉ 🚨", type="primary", use_container_width=True):
        if not entreprise:
            st.warning("Nom du site requis.")
        else:
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
            log_action(st.session_state.user_info['code'], "CALCUL", f"{ecart_pct:.1f}% | {perte:.0f}F | {entreprise}")

    # RÉSULTATS
    if st.session_state.audit_result:
        r = st.session_state.audit_result
        st.markdown("---")
        
        if r['ecart'] > (r['theo'] * 0.12):
            color = "#FF4B4B"
            msg = "ANOMALIE DÉTECTÉE (VOL PROBABLE)"
            icon = "🚨"
        elif r['ecart'] < -(r['theo'] * 0.12):
            color = "#FFA500"
            msg = "SOUS-CONSOMMATION (Erreur Saisie ?)"
            icon = "⚠️"
        else:
            color = "#00C853"
            msg = "CONSOMMATION COHÉRENTE"
            icon = "✅"

        st.markdown(f"""
        <div style="background-color: {color}20; border: 2px solid {color}; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
            <h2 style="color: {color}; margin:0;">{icon} {msg}</h2>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("THÉORIQUE", f"{r['theo']:.1f} L")
        c2.metric("DÉCLARÉ", f"{r['reel']:.1f} L")
        c3.metric("ÉCART", f"{r['ecart']:+.1f} L", delta_color="inverse" if color=="#FF4B4B" else "normal")

        if "VOL" in msg:
            st.error(f"💸 PERTE FINANCIÈRE : {r['perte']:,.0f} FCFA")
            link = f"https://wa.me/237671894095?text=Alerte%20Vol%20{r['site']}%20:%20Ecart%20{r['pct']:.1f}%25"
            st.link_button("📞 CONTACTER L'EXPERT MAINTENANT", link, type="primary", use_container_width=True)

        rapport = f"""AUDIT GEN-CONTROL V2
📅 {datetime.now().strftime('%d/%m/%Y')}
📍 {r['site']}
⚙️ Charge : {r['charge']*100:.0f}%
⛽ Déclaré : {r['reel']:.1f} L | Théorique : {r['theo']:.1f} L
⚠️ ÉCART : {r['ecart']:+.1f} L ({r['pct']:.1f}%)
💰 VALEUR : {r['perte']:,.0f} FCFA
Verdict : {msg}"""
        st.text_area("📄 Rapport (Copier pour le DG)", rapport, height=200)

# FOOTER GLOBAL
st.markdown("""
<div class="footer">
    Application GEN-CONTROL V2 © 2025<br>
    Développé par <strong>Cabinet DI-SOLUTIONS</strong> - Expert Industriel Dr. Tchamdjio
</div>
""", unsafe_allow_html=True)