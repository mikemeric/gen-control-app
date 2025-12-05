import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ==========================================
# CONFIGURATION & DESIGN FESTIF
# ==========================================
st.set_page_config(page_title="LIVRE D'OR GIM", page_icon="✍️", layout="centered")

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
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CONNEXION (MÊME QUE GEN-CONTROL)
# ==========================================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    st.error("Erreur de connexion au Livre d'Or.")
    st.stop()

# ==========================================
# HEADER
# ==========================================
st.image("https://via.placeholder.com/800x200/003366/FFFFFF?text=LIVRE+D'OR+GIM+2025", use_column_width=True)
st.markdown("<h3 style='text-align: center; color: #FF6600;'>Laissez une trace pour les générations futures</h3>", unsafe_allow_html=True)

# ==========================================
# FORMULAIRE DE SIGNATURE
# ==========================================
with st.expander("✍️ SIGNER LE LIVRE D'OR (Cliquer ici)", expanded=True):
    with st.form("guestbook_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            nom = st.text_input("Votre Nom *")
            promo = st.text_input("Promo (Ex: 2010)")
        with c2:
            entreprise = st.text_input("Entreprise / Poste *")
        
        message = st.text_area("Votre message pour les étudiants / Le département *")
        
        if st.form_submit_button("PUBLIER MON MESSAGE 🚀"):
            if nom and entreprise and message:
                try:
                    # Lecture des données existantes
                    df = conn.read(worksheet="guestbook", ttl=0)
                    
                    # Création nouvelle ligne
                    new_row = pd.DataFrame([{
                        "date": datetime.now().strftime("%H:%M"),
                        "nom": nom,
                        "promo": promo,
                        "entreprise": entreprise,
                        "message": message
                    }])
                    
                    # Concaténation et Sauvegarde
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    conn.update(worksheet="guestbook", data=updated_df)
                    
                    st.success("Merci ! Votre message est affiché.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur d'enregistrement : {e}")
            else:
                st.warning("Veuillez remplir le Nom, l'Entreprise et le Message.")

# ==========================================
# MUR DES MESSAGES (DISPLAY)
# ==========================================
st.markdown("---")
st.subheader("💬 ILS SONT LÀ AUJOURD'HUI...")

if st.button("🔄 Actualiser le mur"):
    st.rerun()

try:
    # Lecture sans cache pour avoir le direct
    df_display = conn.read(worksheet="guestbook", ttl=0)
    
    if not df_display.empty:
        # On inverse pour avoir le dernier en haut
        for index, row in df_display.iloc[::-1].iterrows():
            promo_txt = f" | Promo {row['promo']}" if row['promo'] else ""
            
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
    st.info("Le livre d'or est prêt à recevoir vos signatures.")

# FOOTER
st.markdown("<div style='text-align: center; margin-top: 30px; font-size: 0.8em; color: #888;'>Digital Guestbook by DI-SOLUTIONS</div>", unsafe_allow_html=True)