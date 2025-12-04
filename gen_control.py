import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import urllib.parse

# ==========================================
# 1. CONFIGURATION & STYLE
# ==========================================
st.set_page_config(
    page_title="GEN-CONTROL V2",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Style CSS pour cacher les éléments inutiles et styliser les alertes
st.markdown("""
<style>
    .stDeployButton {display:none;}
    .block-container {padding-top: 2rem;}
    div[data-testid="stMetricValue"] {font-size: 1.8rem;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONNEXION DATABASE (GOOGLE SHEETS)
# ==========================================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("⚠️ Erreur de connexion au serveur sécurisé. Vérifiez votre internet.")
    st.stop()

# ==========================================
# 3. GESTION DE L'ÉTAT (SESSION STATE)
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = {}
if 'audit_result' not in st.session_state:
    st.session_state.audit_result = None

# ==========================================
# 4. FONCTIONS UTILITAIRES (MOUCHARD)
# ==========================================

def log_action(code, action, details="-"):
    """Enregistre une action dans l'onglet 'logs'"""
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
    except Exception:
        pass # On ne bloque pas l'appli si le log échoue

def check_login(code_input):
    """Vérifie le code dans l'onglet 'users'"""
    try:
        df_users = conn.read(worksheet="users", ttl=0, usecols=[0, 1, 2, 3])
        # Nettoyage des espaces et conversion en string
        df_users['code_acces'] = df_users['code_acces'].astype(str).str.strip()
        
        user_row = df_users[
            (df_users['code_acces'] == code_input) & 
            (df_users['statut'] == 'ACTIF')
        ]
        
        if not user_row.empty:
            return True, user_row.iloc[0]['client_nom'], user_row.iloc[0]['vendeur']
        else:
            return False, None, None
    except Exception as e:
        st.error(f"Erreur système : {e}")
        return False, None, None

# ==========================================
# 5. ÉCRAN 1 : LE BUNKER (LOGIN)
# ==========================================

if not st.session_state.authenticated:
    st.title("🔒 SÉCURITÉ ÉNERGÉTIQUE")
    st.caption("Cabinet DI-SOLUTIONS | GEN-CONTROL V2")
    st.markdown("---")
    
    st.info("Accès réservé aux clients audités. Entrez votre Code Licence.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        code_input = st.text_input("Code Licence", placeholder="Ex: GEN-2025-X").strip()
    
    if st.button("Déverrouiller l'accès 🔓", type="primary", use_container_width=True):
        if code_input:
            with st.spinner("Authentification en cours..."):
                is_valid, client_name, vendeur = check_login(code_input)
                
                if is_valid:
                    st.session_state.authenticated = True
                    st.session_state.user_info = {
                        "code": code_input, 
                        "nom": client_name,
                        "vendeur": vendeur
                    }
                    log_action(code_input, "LOGIN", f"Succès - {client_name}")
                    st.rerun()
                else:
                    st.error("⛔ Code Invalide ou Expiré.")
                    st.markdown("**Besoin d'un accès ? Contactez le Dr. Tchamdjio au 671 89 40 95**")
        else:
            st.warning("Veuillez saisir un code.")

# ==========================================
# 6. ÉCRAN 2 : LE CALCULATEUR (MAIN APP)
# ==========================================

else:
    # --- HEADER ---
    c1, c2 = st.columns([3, 1])
    with c1:
        st.caption(f"👤 Client : **{st.session_state.user_info['nom']}**")
    with c2:
        if st.button("Déconnexion", type="secondary"):
            st.session_state.authenticated = False
            st.session_state.audit_result = None
            st.rerun()
            
    st.markdown("---")
    st.header("⛽ AUDIT THERMODYNAMIQUE")

    # --- LEAD MAGNET (DONNÉES) ---
    with st.expander("📋 Informations du Site (Requis)", expanded=True):
        col_a, col_b = st.columns(2)
        with col_a:
            entreprise_audit = st.text_input("Nom du Site / Engin", placeholder="Ex: Usine Bassa / Camion 01")
        with col_b:
            contact_whatsapp = st.text_input("Numéro WhatsApp", placeholder="Pour recevoir le rapport")

    # --- SAISIE TECHNIQUE ---
    st.subheader("1. Paramètres Moteur")
    
    col1, col2 = st.columns(2)
    with col1:
        puissance_kva = st.number_input("Puissance Nominale (kVA)", min_value=10, value=100, step=10)
        heures_marche = st.number_input("Heures de Fonctionnement", min_value=1, value=24)
    with col2:
        litres_declares = st.number_input("Carburant Déclaré (Litres)", min_value=0.0, value=50.0)
        prix_litre = st.number_input("Prix du Litre (FCFA)", value=750, step=50)

    # --- RÉGLAGES EXPERTS (Cos Phi) ---
    with st.expander("⚙️ Paramètres Avancés (Ingénierie)"):
        st.caption("Ne modifier que si vous êtes technicien.")
        c_phi, c_dens = st.columns(2)
        with c_phi:
            cos_phi = st.slider("Cos φ (Facteur de Puissance)", 0.6, 1.0, 0.8, 0.05)
        with c_dens:
            densite_fuel = st.number_input("Densité Carburant", value=0.85, step=0.01)

    # --- CALCUL DE CHARGE (AMPÈRES) ---
    st.subheader("2. Calcul de la Charge")
    method_charge = st.radio("Méthode de relevé :", ["👁️ Visuelle (Approximatif)", "⚡ Ampèremètre (Précis)"], horizontal=True)

    if method_charge == "⚡ Ampèremètre (Précis)":
        # I = S / (U * sqrt(3)) -> Pour 400V : I = kVA * 1.44
        i_max = puissance_kva * 1.44
        st.info(f"Intensité Max Théorique : **{i_max:.0f} A**")
        ampere_lu = st.number_input("Ampérage Moyen Lu (A)", min_value=0.0, max_value=float(i_max*1.2))
        
        if i_max > 0:
            charge_calculee = ampere_lu / i_max
            st.metric("Taux de Charge Calculé", f"{charge_calculee*100:.1f} %")
            facteur_charge = charge_calculee
        else:
            facteur_charge = 0.5
    else:
        charge_select = st.select_slider(
            "Niveau d'activité observé",
            options=["Faible (25%)", "Moyen (50%)", "Élevé (75%)", "Max (90%)"],
            value="Moyen (50%)"
        )
        mapping = {"Faible (25%)": 0.25, "Moyen (50%)": 0.50, "Élevé (75%)": 0.75, "Max (90%)": 0.90}
        facteur_charge = mapping[charge_select]

    # --- BOUTON CALCUL ---
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("LANCER L'ANALYSE 🔎", type="primary", use_container_width=True):
        if not entreprise_audit:
            st.warning("Veuillez entrer le nom du Site/Entreprise.")
        else:
            # CŒUR DE CALCUL (WILLANS)
            # P_elec = P_kva * cos_phi
            # Conso (L/h) approx = (0.1 * P_nom + 0.9 * P_nom * charge) * CSP_L_kWh
            # CSP standard diesel = 0.24 L/kWh (variable selon moteurs mais moyenne robuste)
            
            puissance_kw = puissance_kva * cos_phi
            csp = 0.24 # Consommation Spécifique Moyenne (L/kWh)
            
            conso_vide = puissance_kw * csp * 0.1
            conso_charge = puissance_kw * csp * 0.9 * facteur_charge
            
            conso_h_theo = conso_vide + conso_charge
            conso_total_theo = conso_h_theo * heures_marche
            
            diff = litres_declares - conso_total_theo
            percent_diff = (diff / conso_total_theo) * 100 if conso_total_theo > 0 else 0
            perte_financiere = diff * prix_litre

            # Sauvegarde
            st.session_state.audit_result = {
                "theo": conso_total_theo,
                "reel": litres_declares,
                "diff": diff,
                "pct": percent_diff,
                "cash": perte_financiere,
                "site": entreprise_audit
            }
            
            # Log
            log_text = f"Ecart {percent_diff:.1f}% | {perte_financiere:.0f} F | {entreprise_audit}"
            log_action(st.session_state.user_info['code'], "CALCUL", log_text)

    # --- RÉSULTATS ---
    if st.session_state.audit_result:
        res = st.session_state.audit_result
        st.markdown("---")
        
        # Logique Couleur
        if res['diff'] > (res['theo'] * 0.10):
            status_color = "red"
            status_msg = "🚨 ANOMALIE CRITIQUE (VOL SUSPECTÉ)"
            icon = "❌"
        elif res['diff'] < -(res['theo'] * 0.10):
            status_color = "orange"
            status_msg = "⚠️ SOUS-CONSOMMATION (Vérifier Saisie)"
            icon = "❓"
        else:
            status_color = "green"
            status_msg = "✅ CONSOMMATION COHÉRENTE"
            icon = "✔️"

        st.markdown(f"<h3 style='color:{status_color}; text-align:center; border:2px solid {status_color}; padding:10px; border-radius:10px;'>{status_msg}</h3>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Théorique (Willans)", f"{res['theo']:.1f} L")
        c2.metric("Déclaré (Jauge)", f"{res['reel']:.1f} L")
        c3.metric("Écart", f"{res['diff']:.1f} L", delta_color="inverse" if status_color=="red" else "normal")

        if status_color == "red":
            st.error(f"PERTE FINANCIÈRE ESTIMÉE : {res['cash']:,.0f} FCFA")
            
            # BOUTON PANIQUE WHATSAPP
            msg_wa = f"Bonjour Dr Tchamdjio. Alerte sur site {res['site']}. Ecart de {res['pct']:.1f}% ({res['cash']:.0f} FCFA). Besoin d'expertise."
            link_wa = f"https://wa.me/237671894095?text={urllib.parse.quote(msg_wa)}"
            st.link_button("🆘 SIGNALER CETTE ANOMALIE À L'EXPERT", link_wa, type="primary", use_container_width=True)
        
        # RAPPORT TEXTE A COPIER
        st.text_area("📄 Rapport à copier pour la Direction :", 
                     f"""AUDIT ÉNERGÉTIQUE GEN-CONTROL
Date : {datetime.now().strftime('%d/%m/%Y')}
Site : {res['site']}
---------------------------
Puissance : {puissance_kva} kVA
Charge Estimée : {facteur_charge*100:.0f}%
Heures : {heures_marche}h
---------------------------
⛽ Conso. Déclarée : {res['reel']:.1f} L
📉 Conso. Théorique : {res['theo']:.1f} L
⚖️ ÉCART : {res['diff']:.1f} L ({res['pct']:.1f}%)
💰 IMPACT : {res['cash']:,.0f} FCFA
---------------------------
Verdict : {status_msg}
Validé par DI-SOLUTIONS""", height=250)