import streamlit as st
import time

# ==========================================
# 1. CONFIGURATION "POLICE & SÉCURITÉ"
# ==========================================
st.set_page_config(
    page_title="GEN-CONTROL | Anti-Vol",
    page_icon="🔒",
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# --- CSS DESIGN (ZARA) ---
st.markdown("""
<style>
    .stApp { background-color: #0F172A; color: #F1F5F9; }
    h1 { color: #38BDF8; text-align: center; font-weight: 900; text-transform: uppercase; }
    .stNumberInput input, .stTextInput input { background-color: #1E293B; color: white; border: 2px solid #475569; border-radius: 8px; font-size: 20px; text-align: center; }
    div.stButton > button[kind="primary"] { background: linear-gradient(180deg, #EAB308 0%, #CA8A04 100%); color: black; font-size: 24px; height: 3em; width: 100%; border: none; border-radius: 10px; font-weight: 900; box-shadow: 0 4px 0 #854D0E; }
    div.stButton > button[kind="primary"]:active { transform: translateY(4px); box-shadow: none; }
    .result-card { background-color: #1E293B; padding: 20px; border-radius: 10px; border: 1px solid #334155; text-align: center; margin-bottom: 10px; }
    .lock-screen { padding: 20px; border: 2px dashed #475569; border-radius: 10px; text-align: center; background-color: #1e293b; margin-top: 20px;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SYSTÈME DE VERROUILLAGE (AXEL)
# ==========================================

# --- DÉFINIR LE MOT DE PASSE ICI ---
MOT_DE_PASSE_SECRET = "GEN2025" 
# (C'est ce code que vous donnerez au client après paiement)

def check_password():
    """Retourne True si l'utilisateur est connecté"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        
    if st.session_state.authenticated:
        return True
        
    st.title("🔒 ACCÈS RESTREINT")
    st.markdown("<div style='text-align: center;'>Logiciel Anti-Vol Carburant</div>", unsafe_allow_html=True)
    
    # Zone de Login
    st.markdown("<br>", unsafe_allow_html=True)
    password = st.text_input("Entrez votre Code d'Accès", type="password", placeholder="1234...")
    
    if st.button("DÉVERROUILLER", type="secondary"):
        if password == MOT_DE_PASSE_SECRET:
            st.session_state.authenticated = True
            st.rerun() # Recharge la page pour afficher l'app
        else:
            st.error("Code incorrect.")
            
    # Zone de Vente (Si pas de code)
    st.markdown("""
    <div class="lock-screen">
        <h3>🛑 Vous n'avez pas de code ?</h3>
        <p>Cet outil professionnel permet de détecter les vols de carburant sur vos groupes électrogènes.</p>
        <p style="color: #FACC15; font-weight: bold;">PRIX : 5 000 FCFA (À vie)</p>
        <hr style="border-color: #334155;">
        <small>Pour obtenir votre code immédiat :</small><br>
        <b>Contactez le Dr Tchamdjio sur WhatsApp</b>
    </div>
    """, unsafe_allow_html=True)
    
    # Lien WhatsApp direct
    whatsapp_url = "https://wa.me/237671894095?text=Bonjour%20Doc,%20je%20veux%20le%20code%20pour%20GEN-CONTROL." 
    # REMPLACEZ LE NUMERO CI-DESSUS PAR LE VÔTRE !
    
    st.markdown(f'<div style="text-align:center"><a href="{whatsapp_url}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:5px; font-weight:bold; margin-top:10px;">👉 ACHETER MON CODE</button></a></div>', unsafe_allow_html=True)
    
    return False

# ==========================================
# 3. APPLICATION (VISIBLE SEULEMENT SI DÉVERROUILLÉE)
# ==========================================

if check_password():
    # --- Si on arrive ici, c'est que le code est bon ---
    
    st.title("⛽ GEN-CONTROL")
    st.caption("L'Anti-Vol de Carburant de Poche | Mode Expert")
    
    if st.button("🔒 Verrouiller l'écran"):
        st.session_state.authenticated = False
        st.rerun()

    st.write("")

    # Formulaire compact
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            kva = st.number_input("Puissance Groupe (kVA)", value=100, step=10)
        with col2:
            hours = st.number_input("Heures de marche", value=5.0, step=0.5)

        st.write("")
        st.markdown("**📊 Charge Estimée (%)**")
        load_percent = st.slider("Niveau de charge", 0, 100, 50)
        
        if load_percent < 30:
            st.caption("⚠️ Risque d'encrassement (Sous-charge)")
        elif load_percent > 80:
            st.caption("🔥 Surcharge possible")

        st.write("")
        st.markdown("**⛽ Carburant Déclaré (Litres)**")
        fuel_declared = st.number_input("Saisir la conso annoncée", value=0.0, step=5.0)

        st.divider()
        check_btn = st.button("🕵🏼 SCANNER MAINTENANT", type="primary")

    if check_btn:
        # Algorithme Marcus
        kw_rating = kva * 0.8 
        load_factor = load_percent / 100
        conso_horaire_theorique = (kw_rating * 0.24) * (0.25 + (0.75 * load_factor))
        total_theorique = conso_horaire_theorique * hours
        ecart = fuel_declared - total_theorique
        prix_litre = 800 
        argent_perdu = ecart * prix_litre

        st.write("")
        
        if fuel_declared == 0:
            st.info(f"ℹ️ Conso attendue : **{conso_horaire_theorique:.1f} L/h**")
            
        elif ecart > (total_theorique * 0.15): 
            st.markdown("""<div style="background-color: #450A0A; border: 2px solid #EF4444; padding: 15px; border-radius: 10px; text-align: center;"><h2 style="color: #EF4444; margin:0;">🚨 SUSPICION DE VOL</h2><p style="color: #FECACA;">Surconsommation détectée</p></div>""", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1: st.markdown(f"""<div class="result-card"><small>Théorique</small><h3 style="color:#4ADE80">{total_theorique:.1f} L</h3></div>""", unsafe_allow_html=True)
            with c2: st.markdown(f"""<div class="result-card"><small>Déclaré</small><h3 style="color:#F87171">{fuel_declared:.1f} L</h3></div>""", unsafe_allow_html=True)
            st.markdown(f"""<div style="text-align: center; margin-top: 10px;"><span style="font-size: 20px;">Manquant : <b>{ecart:.1f} Litres</b></span><br><span style="font-size: 28px; font-weight: bold; color: #FACC15;">💸 ~{argent_perdu:,.0f} FCFA</span><br><small>Perdus sur cette période</small></div>""", unsafe_allow_html=True)
            
        elif ecart < -(total_theorique * 0.15):
            st.warning("⚠️ Consommation anormalement BASSE. Vérifiez les heures.")
            st.metric("Conso Théorique", f"{total_theorique:.1f} L")
            
        else:
            st.markdown("""<div style="background-color: #064E3B; border: 2px solid #34D399; padding: 15px; border-radius: 10px; text-align: center;"><h2 style="color: #34D399; margin:0;">✅ CONSO NORMALE</h2><p style="color: #D1FAE5;">Les chiffres sont cohérents.</p></div>""", unsafe_allow_html=True)
            st.metric("Conso Théorique", f"{total_theorique:.1f} L", delta=f"{ecart:.1f} L")

    st.markdown("<br><div style='text-align: center; color: #475569;'><small>GEN-CONTROL v1.0 | DI-SOLUTIONS © 2025</small></div>", unsafe_allow_html=True)