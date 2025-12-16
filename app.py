# ==============================================================================
# GEN-CONTROL V1.1.2 - FINAL (Patch Streamlit 2026 - CORRIGÉ LOGOUT)
# ==============================================================================
import streamlit as st
import os
import time
from datetime import datetime
import uuid
import urllib.parse

# Assurez-vous que ces fichiers existent bien dans votre dossier
from database import ThreadSafeDatabase
from security import EnhancedSecurityManager
from physics import IsoWillansModel, ReferenceEngineLibrary, AtmosphericParams
from analytics import DetailedLoadFactorManager, IntelligentAnomalyDetector, AdaptiveLearningEngine
from reports import PDFReportGenerator
from payments import render_payment_page

st.set_page_config(page_title="GEN-CONTROL V1.1", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main-header { font-size: 1.5rem; font-weight: bold; color: #003366; margin-bottom: 1rem; border-bottom: 2px solid #FF4B4B; padding-bottom: 5px; }
    .verdict-box { padding: 15px; border-radius: 8px; text-align: center; margin: 10px 0; font-weight: bold; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .share-btn { display: inline-block; background-color: #25D366; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold; margin-top: 10px; text-align: center; width: 100%; }
    .maintenance-alert { background-color: #e3f2fd; border-left: 5px solid #2196f3; padding: 10px; border-radius: 5px; color: #0d47a1; font-size: 0.9em; margin-top: 10px;}
    .tech-card { background-color: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #b0b0b0; font-size: 0.9em; margin-bottom: 15px; color: #333; }
    .license-warning { background-color: #ffeeba; color: #856404; padding: 10px; border-radius: 5px; border: 1px solid #ffeeba; margin-bottom: 15px;}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_db(): return ThreadSafeDatabase.get_instance()

def init_session():
    if 'db' not in st.session_state: st.session_state.db = get_db()
    if 'security' not in st.session_state: st.session_state.security = EnhancedSecurityManager(st.session_state.db)
    if 'analytics' not in st.session_state: 
        st.session_state.detector = IntelligentAnomalyDetector()
        st.session_state.learning = AdaptiveLearningEngine()
        st.session_state.pdf_gen = PDFReportGenerator()

# --- CORRECTION MAJEURE ICI (NAVIGATION SECURISEE) ---
def render_sidebar():
    # 1. SÉCURITÉ : Si l'utilisateur n'est pas connecté, ON ARRÊTE TOUT.
    # Cela empêche la sidebar de s'afficher une fois déconnecté.
    if 'auth_token' not in st.session_state:
        return None

    with st.sidebar:
        st.title("GEN-CONTROL")
        st.caption("V1.1.2 (Final)")
        
        # Infos Utilisateur
        tier = st.session_state.get('license_tier', 'DISCOVERY')
        user = st.session_state.get('user', 'Utilisateur')
        st.info(f"👤 {user}\n🏷️ Licence : {tier}")
        
        # Menu
        opts = ["📱 Audit Terrain", "🎯 Calibration"]
        if tier == 'DISCOVERY': opts.append("💎 Devenir PRO")
        if tier in ['PRO', 'CORPORATE']: opts.append("🧠 Intelligence")
        if st.session_state.get('role') == 'admin': opts.append("🔐 Admin")
        
        menu = st.radio("Navigation", opts)
        
        st.markdown("---")
        
        # Bouton Déconnexion "Blindé"
        if st.button("Déconnexion", type="primary", use_container_width=True):
            # On utilise .pop(key, None) pour éviter le KeyError si déjà supprimé
            st.session_state.pop('auth_token', None)
            st.session_state.pop('user', None)
            st.session_state.pop('role', None)
            st.rerun()

        st.markdown("---")
        st.warning("⚠️ **AVIS JURIDIQUE**")
        st.markdown("<div style='font-size:0.7em; text-align:justify;'>Outil d'aide à la décision technique (ISO 15550). Résultats non contractuels.</div>", unsafe_allow_html=True)
        
        return menu

def render_auth():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; color:#003366'>🔐 GEN-CONTROL</h1>", unsafe_allow_html=True)
        tab_login, tab_signup = st.tabs(["Connexion", "Créer un compte"])
        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Identifiant")
                password = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("Se connecter"):
                    sec = st.session_state.security; ip = sec.get_remote_ip()
                    success, msg = sec.verify_password(username, password, ip)
                    if success:
                        st.session_state['auth_token'] = sec.create_session_token(username, ip)
                        st.session_state['user'] = username
                        u_data = st.session_state.db.execute_read("SELECT role, license_tier FROM users WHERE username = ?", (username,))
                        st.session_state['role'] = u_data[0]['role'] if u_data else 'user'
                        st.session_state['license_tier'] = u_data[0]['license_tier'] if u_data else 'DISCOVERY'
                        st.rerun()
                    else: st.error(msg)
        with tab_signup:
            st.info("🎁 3 Audits Offerts")
            with st.form("signup_form"):
                c1, c2 = st.columns(2)
                new_user = c1.text_input("Identifiant")
                new_pass = c2.text_input("Mot de passe", type="password")
                email = st.text_input("Email (Obligatoire)")
                phone = st.text_input("WhatsApp")
                company = st.text_input("Société")
                referral = st.text_input("Parrain")
                if st.form_submit_button("Créer"):
                    sec = st.session_state.security; ip = sec.get_remote_ip()
                    if sec.check_signup_abuse(ip): st.error("Trop de comptes.")
                    elif not new_user or not new_pass or not email: st.warning("Champs requis manquants.")
                    else:
                        ok, msg = st.session_state.db.create_user_extended(new_user, new_pass, email, phone, company, referral, ip=ip)
                        if ok: st.success("Créé !"); time.sleep(1); st.rerun()
                        else: st.error(f"Erreur: {msg}")

def render_audit_page():
    tier = st.session_state.get('license_tier', 'DISCOVERY')
    st.markdown(f'<div class="main-header">📱 Audit Terrain <span style="font-size:0.6em; color:grey">({tier})</span></div>', unsafe_allow_html=True)
    db = st.session_state.db
    
    try: aging_val = float(db.get_config_value("AGING_FACTOR", "1.05"))
    except: aging_val = 1.05

    try:
        equipments = db.execute_read("SELECT equipment_id, equipment_name, profile_base, power_kw FROM equipment")
        if not equipments: st.warning("⚠️ Aucun équipement. Allez dans 'Calibration'."); return
        eq_options = {e['equipment_id']: f"{e['equipment_name']} ({e['profile_base']})" for e in equipments}
        selected_id = st.selectbox("Sélectionner l'engin", list(eq_options.keys()), format_func=lambda x: eq_options[x])
        eq_data = next(e for e in equipments if e['equipment_id'] == selected_id)
        last_audit = db.execute_read("SELECT index_end FROM audits WHERE equipment_id = ? ORDER BY timestamp DESC LIMIT 1", (selected_id,))
        suggested_start = float(last_audit[0]['index_end']) if last_audit else 0.