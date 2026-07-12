"""
INTERFACE STREAMLIT MOBILE ALLÉGÉE ET ULTRA-MODULAIRE (APP_WEB.PY)
"""
import streamlit as st
import arabic_reshaper
from bidi.algorithm import get_display
from gui.langues import DICTIONNAIRE_LANGUES
from core.web_processing import executer_calculs_zakat_web, executer_partage_heritage_web

def fmt_ar(t):
    try: return get_display(arabic_reshaper.reshape(t))
    except: return t

st.set_page_config(page_title="Hayaati Mobile Pro", page_icon="🕌", layout="centered")

# Configuration de la charte graphique de prestige
st.markdown("<style>.main{background-color:#f9fafb;} h1{color:#f59e0b; text-align:center; font-weight:bold; margin-bottom:2px;} .basmala{color:#064e3b; text-align:center; font-size:16px; font-weight:bold;} .salam{color:#d97706; text-align:center; font-size:14px; font-weight:bold; margin-bottom:20px;} .logo-container{text-align:center; margin-bottom:10px;} div.stButton>button{background-color:#064e3b; color:white; width:100%; height:45px; font-weight:bold; border-radius:8px;}</style>", unsafe_allow_html=True)

# Barre latérale de contrôle
st.sidebar.markdown("### ⚙️ CONFIGURATION GLOBALE")
langue = st.sidebar.selectbox("Language / Harshe", ["FR", "EN", "AR", "HA", "ES", "ZH"])
lang = DICTIONNAIRE_LANGUES[langue]
devise = st.sidebar.selectbox("Currency / Monnaie", ["€", "$", "£", "CFA", "¥", "₦", "GH₵", "SAR", "AED", "KWD", "DZD", "MAD", "TND"])
madhhab = st.sidebar.selectbox("Fiqh / Madhhab", ["Maliki", "Hanafi", "Shafi'i", "Hanbali"])

# Sceau vectoriel et En-tête sacré RTL
st.markdown(f'<div class="logo-container"><svg width="80" height="80" viewBox="0 0 80 80"><circle cx="40" cy="40" r="38" fill="#064e3b" stroke="#d97706" stroke-width="2"/><circle cx="40" cy="40" r="34" fill="#064e3b" stroke="#f59e0b" stroke-width="0.5"/><text x="40" y="44" font-family="Arial" font-size="30" font-weight="bold" fill="#f59e0b" text-anchor="middle">ح</text><text x="40" y="60" font-family="Arial" font-size="10" font-weight="bold" fill="#ffffff" text-anchor="middle">{fmt_ar("حياتي")}</text></svg></div>', unsafe_allow_html=True)
st.markdown("<h1>H A Y A A T I</h1>", unsafe_allow_html=True)
st.markdown(f"<p class='basmala'>{fmt_ar('حياتي — بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ')}</p>", unsafe_allow_html=True)
st.markdown(f"<p class='salam'>{fmt_ar('السَّلَامُ عَلَيْكُمْ وَرَحْمَةُ اللهِ وَبَرَكَاتُهُ')}</p>", unsafe_allow_html=True)

# Bloc d'identité permanent pour éviter les doublons
st.markdown(f"#### 👤 {lang.get('her_pop_exceptions_titre', 'Profil')}")
c1, col2 = st.columns(2)
prenom = c1.text_input("Prénom :", value="Abdourazak")
nom = col2.text_input("Nom :", value="Bénéficiaire")
pays = c1.text_input("Pays :", value="Niger")
ville = col2.text_input("Ville :", value="Niamey")
telephone = st.text_input("Téléphone :", value="+227 00 00 00 00")
st.markdown("---")

# Routage des onglets tactiles mobiles
t_zk = "Zaƙka" if langue == "HA" else "Zakat"
t_her = "Rabon Gado" if langue == "HA" else "Heritage"
tab_zk, tab_her = st.tabs([t_zk, t_her])

# --- MODULE 1 : ZAKAT INTERACTIVE ---
with tab_zk:
    st.markdown(f"### 🏦 {lang['zk_titre']}")
    cours = st.number_input(f"{lang['zk_lbl_cours']} ({devise})", min_value=0.0, value=68.50, key="c_o")
    cash = st.number_input(f"{lang['zk_lbl_cash']} ({devise})", min_value=0.0, value=0.0, key="c_c")
    bijoux = st.number_input(f"{lang['zk_lbl_bijoux']} ({devise})", min_value=0.0, value=0.0, key="c_b")
    stocks = st.number_input(f"{lang['zk_lbl_stocks']} ({devise})", min_value=0.0, value=0.0, key="c_s")
    pro_cash = st.number_input(f"{lang['zk_lbl_pro_cash']} ({devise})", min_value=0.0, value=0.0, key="c_p")
    dettes = st.number_input(f"{lang['zk_lbl_dettes']} ({devise})", min_value=0.0, value=0.0, key="c_d")
    recolte = st.number_input(lang["zk_lbl_recolte"], min_value=0.0, value=0.0, key="c_r")
    elevage = st.number_input(lang["zk_lbl_elevage"], min_value=0, value=0, key="c_e")

    if st.button(lang["zk_btn_calculer"], key="b_zk"):
        if cours <= 0: st.error(lang["zk_err_cours"])
        else:
            res = executer_calculs_zakat_web(stocks, pro_cash, dettes, cash, bijoux, cours, madhhab, recolte, elevage)
            st.markdown(f"#### {lang['zk_rep_titre']}")
            if res["financier"]["eligible"]: st.success(f"{lang['zk_rep_fin']}{res['financier']['montant_zakat_du']:.2f} {devise}")
            else: st.warning(lang["zk_rep_fin_non"])
            if res["agricole"]["eligible"]: st.info(f"{lang['zk_rep_agri']}{res['agricole']['zakat_due_kg']:.1f}{lang['zk_unite_kg']}")
            else: st.write(lang["zk_rep_agri_non"])
            if res["elevage"]["eligible"]: st.info(f"{lang['zk_rep_el']}{res['elevage']['moutons_dus']}{lang['zk_unite_tetes']}")
            else: st.write(lang["zk_rep_el_non"])

# --- MODULE 2 : HERITAGE INTERACTIF ---
with tab_her:
    st.markdown(f"### 📜 {lang['her_titre']}")
    capital = st.number_input(f"{lang['her_lbl_capital']} ({devise})", min_value=0.0, value=24000.0, key="h_cap")
    hors_mariage = st.checkbox("⚖️ Filiation : Enfant né hors mariage")
    
    st.write(f"**{lang['her_lbl_famille']}**")
    cf_n = {}
    cf_n["epouse"] = st.number_input(lang["her_chk_epouse"], min_value=0, max_value=4, value=0, key="n_ep")
    cf_n["epoux"] = st.number_input(lang["her_chk_epoux"], min_value=0, max_value=1, value=0, key="n_ex")
    cf_n["fils"] = st.number_input("Nombre de Fils", min_value=0, value=0, key="n_fi")
    cf_n["fille"] = st.number_input("Nombre de Filles", min_value=0, value=0, key="n_fe")
    
    f_brute = [c for c, v in cf_n.items() if v > 0]
    if st.checkbox(lang["her_chk_pere"], key="f_pe"): f_brute.append("pere")
    if st.checkbox(lang["her_chk_mere"], key="f_me"): f_brute.append("mere")
    if st.checkbox(lang["her_chk_grand_pere"], key="f_gp"): f_brute.append("grand_pere")
    
    cf_n["frere_germain"] = st.number_input(lang["her_chk_frere"], min_value=0, value=0, key="n_fg")
    if cf_n["frere_germain"] > 0: f_brute.append("frere_germain")
    cf_n["frere_uterin"] = st.number_input(lang["her_chk_frere_ut"], min_value=0, value=0, key="n_fu")
    if cf_n["frere_uterin"] > 0: f_brute.append("frere_uterin")
    cf_n["oncle"] = st.number_input(lang["her_chk_oncle"], min_value=0, value=0, key="n_on")
    if cf_n["oncle"] > 0: f_brute.append("oncle")

    exceptions = []
    if f_brute:
        st.markdown(f"##### ⚠️ {lang['her_btn_exceptions']}")
        for m in list(set(f_brute)):
            if st.checkbox(f"Exclure {m.upper()}", key=f"w_ex_{m}"): exceptions.append(m)

    if st.button(lang["her_btn_partager"], key="b_her"):
        if not f_brute: st.warning(lang["err_num"])
        else:
            res_h = executer_partage_heritage_web(cf_n, f_brute, exceptions, hors_mariage)
            st.markdown(f"#### {lang['her_res_titre']}")
            if res_h["is_kalalah"]: st.info("💡 CAS KALÂLAH DÉTECTÉ")
            st.write(f"**{lang['her_lbl_retenus']}**")
            for h, frac in res_h["ventilation"].items():
                nb_p = cf_n.get(h, 1)
                nb_p = 1 if nb_p == 0 else nb_p
                part_t = capital * frac
                st.success(f"• {h.upper()} (x{nb_p}) : {frac*100:.1f}% -> {part_t:.2f} {devise} ({part_t/nb_p:.2f}/p)")
            if res_h["exclus_totaux"]:
                st.write(f"**{lang['her_lbl_exclus']}**")
                for e in res_h["exclus_totaux"]: st.warning(f"• {e.upper()}")
