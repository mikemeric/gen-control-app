import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ==========================================
# 1. CONFIGURATION & DESIGN FESTIF
# ==========================================
st.set_page_config(
    page_title="LIVRE D'OR GIM", 
    page_icon="✍️", 
    layout="centered"
)

# CSS pour le style "Cérémonie"
st.markdown("""
<style>
    .stApp {
        background-color: #ffffff;
        color: #333;
    }
    h1 {
        color: #003366;
        text-align: center;
        font-family: 'Arial Black', sans-serif;
        text-transform: uppercase;
        margin-bottom: 0;
    }
    .subtitle {
        text-align: center;
        color: #FF6600;
        font-weight: bold;
        font-size: 18px;
        margin-top: -10px;
        margin-bottom: 30px;
    }
    .message-card {
        background-color: #f0f8ff;
        padding: 20px;
        border-radius: 15px;
        border-left: 6px solid #FF6600;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .author { font-weight: bold; color: #003366; font-size: 1.1em; }
    .meta { font-size: 0.9em; color: #666; font-style: italic; }
    .msg-text { font-size: 1.2em; margin-top: 10px; color: #222; }
    
    /* Bouton stylisé */
    div.stButton > button:first-child {
        background-color: #003366;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
        padding: 10px;
    }
    div.stButton > button:first-child:hover {
        background-color: #FF6600;
        border: none;
    }
    
    /* Cacher le menu hamburger pour faire plus "App" */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONNEXION GOOGLE SHEETS
# ==========================================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("⚠️ Erreur de connexion au Livre d'Or. Vérifiez Internet.")
    st.stop()

# ==========================================
# 3. SIDEBAR (QR CODE AUTOMATIQUE)
# ==========================================
with st.sidebar:
    st.image("logo_gim.jpg", use_column_width=True)
    st.markdown("### 📱 SCANNEZ-MOI")
    st.info("Invitez les autres parrains à signer le livre d'or en scannant ce code.")
    
    # ASTUCE : Génération automatique du QR Code de la page actuelle
    # On utilise l'API gratuite qrserver.com
    # Note : Une fois déployé, copiez l'URL de votre app ci-dessous
    APP_URL = "https://gim-guestbook.streamlit.app" # <-- METTEZ VOTRE VRAI LIEN ICI SI CONNU
    
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={APP_URL}"
    st.image(qr_code_url, caption="Accès Direct")

# ==========================================
# 4. HEADER AVEC LOGO LOCAL
# ==========================================
c1, c2, c3 = st.columns([3, 2, 3])
with c2:
    try:
        st.image("logo_gim.jpg", use_column_width=True)
    except:
        pass # Fallback silencieux

st.markdown("<h1>📖 LIVRE D'OR</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>CÉRÉMONIE DE PARRAINAGE GIM 2025</p>", unsafe_allow_html=True)

# ==========================================
# 5. FORMULAIRE DE SIGNATURE
# ==========================================
with st.expander("✍️ LAISSER UN MESSAGE (Cliquer ici)", expanded=True):
    with st.form("guestbook_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            nom = st.text_input("Votre Nom *")
            promo = st.text_input("Promo (Ex: 2010)")
        with c2:
            entreprise = st.text_input("Entreprise / Poste *")
        
        message = st.text_area("Votre message pour les étudiants / Le département *", placeholder="Félicitations aux filleuls...")
        
        if st.form_submit_button("PUBLIER MON MESSAGE 🚀"):
            if nom and entreprise and message:
                try:
                    df = conn.read(worksheet="guestbook", ttl=0)
                    new_row = pd.DataFrame([{
                        "date": datetime.now().strftime("%H:%M"),
                        "nom": nom,
                        "promo": promo,
                        "entreprise": entreprise,
                        "message": message
                    }])
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    conn.update(worksheet="guestbook", data=updated_df)
                    st.success("Merci ! Votre message est affiché sur le mur.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur d'enregistrement : {e}")
            else:
                st.warning("Veuillez remplir le Nom, l'Entreprise et le Message.")

# ==========================================
# 6. MUR DES MESSAGES (DISPLAY)
# ==========================================
st.markdown("---")
st.markdown("<h3 style='text-align: center; color: #003366;'>💬 ILS SONT LÀ AUJOURD'HUI...</h3>", unsafe_allow_html=True)

if st.button("🔄 Actualiser le mur"):
    st.rerun()

try:
    df_display = conn.read(worksheet="guestbook", ttl=0)
    if not df_display.empty:
        for index, row in df_display.iloc[::-1].iterrows():
            promo_txt = f" | Promo {row['promo']}" if pd.notna(row['promo']) and row['promo'] != "" else ""
            st.markdown(f"""
            <div class="message-card">
                <div class="author">{row['nom']} <span style="color:#FF6600;">{promo_txt}</span></div>
                <div class="meta">🏢 {row['entreprise']} • 🕒 {row['date']}</div>
                <div class="msg-text">“ {row['message']} ”</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Soyez le premier à écrire un message !")
except Exception:
    st.info("Chargement des messages...")

# ==========================================
# 7. FOOTER
# ==========================================
st.markdown("<div style='text-align: center; margin-top: 50px; border-top: 1px solid #eee; padding-top: 20px; font-size: 0.8em; color: #888;'>Digital Guestbook by DI-SOLUTIONS</div>", unsafe_allow_html=True)