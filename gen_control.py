import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import urllib.parse

# ==========================================
# 1. CONFIGURATION & DESIGN (V2.5)
# ==========================================
st.set_page_config(
    page_title="GEN-CONTROL V2.5",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS : MODE SOMBRE + TEXTES BLANCS (LISIBILITÉ MAXIMALE)
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    /* Textes et Labels en BLANC IMPÉRATIF */
    .stTextInput label, .stNumberInput label, .stSelectbox label, .stRadio label {
        color: #FFFFFF !important;
        font-size: 15px !important;
        font-weight: 600 !important;
    }
    
    /* Inputs */
    .stTextInput input, .stNumberInput input {
        color: #FFFFFF !important;
        background-color: #262730 !important;
        border: 1px solid #555 !important;
    }
    
    /* Titre */
    h1 { color: #FF4B4B !important; text-transform: uppercase; font-weight: 900 !important; }
    
    /* Cache */
    .stDeployButton {display:none;}
    #MainMenu {visibility: hidden;}
    
    /* Footer */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #0E1117; color: #888; text-align: center;
        padding: 10px; font-size: 11px; border-top: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONNEXION DATABASE
# ==========================================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
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
        df_users = conn.read(worksheet="users", ttl=0, usecols=[0, 1, 2, 3, 4])
        df_users['code_acces'] = df_users['code_acces'].astype(str).str.strip()
        user_row = df_users[(df_users['code_acces'] == code_input) & (df_users['statut'] == 'ACTIF')]
        if not user_row.empty:
            machine_lock = user_row.iloc[0].get('machine_lock')
            if pd.isna(machine_lock) or str(machine_lock).strip() == "": machine_lock = None
            return True, user_row.iloc[0]['client_nom'], machine_lock
        return False, None, None
    except:
        return False, None, None

# ==========================================
# 5. ÉCRAN LOGIN
# ==========================================
if not st.session_state.authenticated:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>🔐 GEN-CONTROL V2.5</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #CCC;'>AUDIT EXPERT</h4>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        code_input = st.text_input("CODE LICENCE", placeholder="Ex: GEN-XXXX").strip()
        if st.button("DÉVERROUILLER 🔓", type="primary", use_container_width=True):
            if code_input:
                is_valid, client_name, machine_fixe = check_login(code_input)
                if is_valid:
                    st.session_state.authenticated = True
                    st.session_state.user_info = {"code": code_input, "nom": client_name, "machine": machine_fixe}
                    log_action(code_input, "LOGIN", f"Succès - {client_name}")
                    st.rerun()
                else:
                    st.error("⛔ Code Invalide.")

# ==========================================
# 6. ÉCRAN AUDIT
# ==========================================
else:
    with st.sidebar:
        st.success(f"👤 **{st.session_state.user_info['nom']}**")
        if st.session_state.user_info.get('machine'):
             st.info(f"🔒 Lié à : {st.session_state.user_info['machine']}")
        if st.button("Déconnexion"):
            st.session_state.authenticated = False
            st.session_state.audit_result = None
            st.rerun()

    st.markdown("### ⛽ GEN-CONTROL V2.5")
    st.caption("Powered by Cabinet DI-SOLUTIONS")
    st.markdown("---")
    
    # 1. IDENTIFICATION
    c1, c2 = st.columns(2)
    with c1:
        if st.session_state.user_info.get('machine'):
            entreprise = st.text_input("MATÉRIEL (Verrouillé)", value=st.session_state.user_info['machine'], disabled=True)
        else:
            entreprise = st.text_input("MATÉRIEL / SITE", placeholder="Ex: Toupie Volvo 01")
            if entreprise: st.warning("⚠️ Ce nom sera lié définitivement à ce code.")
    with c2:
        contact = st.text_input("WHATSAPP CONTACT", placeholder="6XX XX XX XX")

    # 2. SÉLECTEUR MATÉRIEL
    st.markdown("<br>", unsafe_allow_html=True)
    type_equipement = st.radio("TYPE DE MATÉRIEL", ["🏭 GROUPE ÉLECTROGÈNE", "🚛 CAMION / ENGIN TP"], horizontal=True)

    facteur_charge = 0.0
    puissance_kw_calcul = 0.0
    mode_calcul = ""

    # ---------------------------------------------------------
    # LOGIQUE GROUPE
    # ---------------------------------------------------------
    if "GROUPE" in type_equipement:
        c_p, c_u = st.columns(2)
        with c_p:
            puissance_input = st.number_input("PUISSANCE GROUPE (kVA)", 10, 5000, 100)
            puissance_kw_calcul = puissance_input * 0.8
        with c_u:
            scenario = st.selectbox("PROFIL UTILISATION", [
                "⚡ Ampèremètre (Précis)",
                "🏢 Bureaux / Hôtel (Faible) - 30%",
                "🏪 Standard (Moyen) - 50%",
                "🏗️ Industrie (Élevé) - 75%",
                "🔥 Pleine Charge - 90%"
            ])
            
            if "Ampèremètre" in scenario:
                i_max = puissance_input * 1.44
                st.caption(f"I Max : {i_max:.0f} A")
                amp = st.number_input("Ampères Lus (A)", 0.0, float(i_max*1.1))
                if i_max > 0: facteur_charge = amp / i_max
                mode_calcul = f"Mesure {amp}A"
            else:
                if "30%" in scenario: facteur_charge = 0.30
                elif "50%" in scenario: facteur_charge = 0.50
                elif "75%" in scenario: facteur_charge = 0.75
                elif "90%" in scenario: facteur_charge = 0.90
                mode_calcul = scenario

    # ---------------------------------------------------------
    # LOGIQUE CAMION (AVEC MODE STATIQUE / PTO)
    # ---------------------------------------------------------
    else: 
        c_p, c_u = st.columns(2)
        with c_p:
            puissance_input = st.number_input("PUISSANCE MOTEUR (CV)", 50, 1000, 400)
            # P_max moteur en kW
            p_max_kw = puissance_input * 0.7355 
            puissance_kw_calcul = p_max_kw # Par défaut, on part du moteur global
        
        with c_u:
            # NOUVEAU SÉLECTEUR V2.5
            mode_camion = st.radio("SITUATION", ["🛣️ Roulage (Route)", "🛑 Statique / Prise de Force (PTO)"])
        
        if mode_camion == "🛣️ Roulage (Route)":
            scenario = st.selectbox("TYPE DE TRAJET", [
                "Vide / Eco / Plat (15%)",
                "Mixte / Ville (25%)",
                "Chargé / Vallonné (40%)",
                "Chantier Difficile (60%)"
            ])
            if "15%" in scenario: facteur_charge = 0.15
            elif "25%" in scenario: facteur_charge = 0.25
            elif "40%" in scenario: facteur_charge = 0.40
            elif "60%" in scenario: facteur_charge = 0.60
            mode_calcul = f"Roulage ({scenario})"
            
        else: # MODE STATIQUE (L'INNOVATION)
            st.info("ℹ️ Calcul basé sur la puissance de l'équipement auxiliaire (Toupie, Grue...).")
            equipement_pto = st.selectbox("QUOI TOURNE ?", [
                "🔄 Toupie Béton (Malaxage) - ~20 kW",
                "🏗️ Grue / Bras Hydraulique - ~30 kW",
                "❄️ Frigo / Clim (Ralenti) - ~10 kW",
                "🚜 Forage / Compresseur - ~45 kW"
            ])
            
            # Ici on force la puissance utilisée, on ignore le % du gros moteur
            p_utile = 0
            if "Toupie" in equipement_pto: p_utile = 20
            elif "Grue" in equipement_pto: p_utile = 30
            elif "Frigo" in equipement_pto: p_utile = 10
            elif "Forage" in equipement_pto: p_utile = 45
            
            # On recalcule le facteur de charge par rapport au moteur principal
            # Ex: 20 kW sur un moteur de 294 kW (400CV) = 6.8% de charge
            if p_max_kw > 0:
                facteur_charge = p_utile / p_max_kw
                # On ajoute une petite marge de friction moteur (5%)
                facteur_charge += 0.05 
            
            mode_calcul = f"Statique ({equipement_pto})"

    # 3. DONNÉES CONSO
    st.markdown("---")
    c_h, c_l, c_p = st.columns(3)
    with c_h:
        heures = st.number_input("DURÉE (Heures)", min_value=0.5, value=8.0, step=0.5)
    with c_l:
        litres = st.number_input("CONSO DÉCLARÉE (L)", min_value=0.0, value=50.0)
    with c_p:
        prix = st.number_input("PRIX DU LITRE", value=828)

    # BOUTON CALCUL
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("LANCER L'AUDIT V2.5 🚀", type="primary", use_container_width=True):
        if not entreprise:
            st.error("Nom du site requis.")
        else:
            # ENREGISTREMENT LOCK
            if not st.session_state.user_info.get('machine'):
                try:
                    df_users = conn.read(worksheet="users", ttl=0)
                    mask = df_users['code_acces'].astype(str).str.strip() == st.session_state.user_info['code']
                    if mask.any():
                        idx = df_users.index[mask][0]
                        df_users.at[idx, 'machine_lock'] = entreprise
                        conn.update(worksheet="users", data=df_users)
                        st.session_state.user_info['machine'] = entreprise
                        st.rerun()
                except: pass

            # MOTEUR WILLANS
            csp = 0.24
            # Formule : P_nom * CSP * (Friction + 0.9 * Charge)
            # Friction à vide = 8%
            conso_h_theo = puissance_kw_calcul * csp * (0.08 + (0.92 * facteur_charge))
            
            total_theo = conso_h_theo * heures
            ecart = litres - total_theo
            ecart_pct = (ecart / total_theo) * 100 if total_theo > 0 else 0
            perte = ecart * prix

            st.session_state.audit_result = {
                "theo": total_theo, "reel": litres, "ecart": ecart,
                "pct": ecart_pct, "perte": perte, "site": entreprise,
                "charge": facteur_charge, "mode": mode_calcul
            }
            log_action(st.session_state.user_info['code'], "CALCUL", f"{ecart_pct:.1f}% | {perte:.0f}F")

    # RÉSULTATS
    if st.session_state.audit_result:
        r = st.session_state.audit_result
        st.markdown("---")
        
        if r['ecart'] > (r['theo'] * 0.10):
            color = "#FF4B4B"
            msg = "ANOMALIE : SURCONSOMMATION"
            icon = "🚨"
        elif r['ecart'] < -(r['theo'] * 0.10):
            color = "#FFA500"
            msg = "SOUS-CONSOMMATION (Check données)"
            icon = "⚠️"
        else:
            color = "#00C853"
            msg = "COHÉRENT (RAS)"
            icon = "✅"

        st.markdown(f"""
        <div style="background-color: {color}20; border: 2px solid {color}; padding: 15px; border-radius: 10px; text-align: center;">
            <h3 style="color: {color}; margin:0;">{icon} {msg}</h3>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Théorique", f"{r['theo']:.1f} L")
        c2.metric("Déclaré", f"{r['reel']:.1f} L")
        c3.metric("Écart", f"{r['ecart']:+.1f} L", delta_color="inverse" if color=="#FF4B4B" else "normal")

        if "ANOMALIE" in msg:
            st.error(f"PERTE : {r['perte']:,.0f} FCFA")
            link = f"https://wa.me/237671894095?text=Alerte%20{r['site']}%20Ecart%20{r['ecart']:.0f}L"
            st.link_button("📞 SIGNALER L'ANOMALIE", link, type="primary", use_container_width=True)

        st.text_area("📋 Rapport Technique", 
f"""AUDIT GEN-CONTROL V2.5
📅 {datetime.now().strftime('%d/%m/%Y')}
📍 {r['site']}
⚙️ Mode : {r['mode']} (Charge {r['charge']*100:.1f}%)
---------------------------
⛽ Déclaré : {r['reel']:.1f} L
📉 Théorique : {r['theo']:.1f} L
⚠️ ÉCART : {r['ecart']:+.1f} L ({r['pct']:+.1f}%)
💰 VALEUR : {r['perte']:,.0f} FCFA
Verdict : {msg}""", height=200)

st.markdown('<div class="footer">GEN-CONTROL V2.5 © DI-SOLUTIONS</div>', unsafe_allow_html=True)