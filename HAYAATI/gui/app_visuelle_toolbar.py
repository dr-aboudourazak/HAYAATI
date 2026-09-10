"""
BANDEAU ET BARRE DE MENUS DE NAVIGATION (GUI/APP_VISUELLE_TOOLBAR.PY)
Version 5.3 — Sidebar smartphone centrée, padding top dynamique mobile.
Compatible Flet 0.86.2, Python 3.14 & APK Android
"""
from __future__ import annotations
import sys
import flet as ft
from gui.langues import DICTIONNAIRE_LANGUES


def configurer_bandeau_superieur(app):
    if hasattr(app, "barre_outils") and app.barre_outils:
        # 🆕 CORRECTION : padding top pour la barre de statut sur mobile
        plateforme = str(getattr(app.page, "platform", "") or "").upper()
        est_mobile = plateforme in ("ANDROID", "IOS") or hasattr(sys, "getandroidapilevel")
        padding_top = 28 if est_mobile else 0

        app.barre_outils.height = 60 + padding_top
        app.barre_outils.padding = ft.Padding(left=10, top=padding_top, right=10, bottom=0)

    if not hasattr(app.barre_outils, "content") or not isinstance(app.barre_outils.content, ft.Row):
        app.barre_outils.content = ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, expand=True)

    cont = app.barre_outils.content
    cont.controls.clear()

    barre_json = app.txt_global.get("barre_outils", {})
    is_m = app.mode_smartphone_actif

    s_txt = f"👤 {app.nom_utilisateur_connecte}" if app.est_mode_connecte else barre_json.get("visiteur", "👤 Visiteur")
    s_aff = s_txt[:12] if is_m else s_txt

    icone_app = ft.Image(
        src="images/Icone-Hayaati.png",
        width=55, height=55, fit="contain"
    )

    zone_g = ft.Container(
        content=ft.Row([
            icone_app,
            ft.Text(value=str(s_aff), size=11 if is_m else 12, italic=True, color=ft.Colors.GREY_300)
        ], spacing=10, alignment=ft.MainAxisAlignment.START),
        padding=ft.Padding(left=10, top=0, right=0, bottom=0)
    )
    cont.controls.append(zone_g)

    if app.est_mode_connecte:
        txt_m = barre_json.get("mode_live", "🟢 Live / Visiteur") if app.mode_persistant_actif else barre_json.get("mode_tiers", "🟡 Visiteur")

        def on_bascule_bouton(e):
            if app.mode_persistant_actif:
                app.executer_deconnexion_session()
                return
            app.basculer_ecran("CONNEXION")

        btn_mode = ft.ElevatedButton(
            content=ft.Text(str(txt_m).strip() if txt_m else "Mode", size=11, weight=ft.FontWeight.W_500),
            bgcolor="#0f766e" if app.mode_persistant_actif else "#d97706", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=8), 
            on_click=on_bascule_bouton
        )
        cont.controls.append(
            ft.Container(content=btn_mode, alignment=ft.Alignment(0, 0),
                padding=ft.Padding(left=0, top=0, right=10, bottom=0))
        )


def dessiner_boutons_navigation(app):
    if not hasattr(app.barre_navigation, "content") or app.barre_navigation.content is None:
        app.barre_navigation.content = ft.Container(content=ft.Text("Initialisation..."), expand=True)
    c_int = app.barre_navigation.content

    if hasattr(c_int, "controls"): 
        c_int.controls.clear()
    else:
        c_int = ft.Row(scroll=ft.ScrollMode.ADAPTIVE, vertical_alignment=ft.CrossAxisAlignment.CENTER) if app.mode_smartphone_actif else ft.Column(expand=True, spacing=1)
        app.barre_navigation.content = c_int

    m_json, b_json = app.txt_global.get("menu", {}), app.txt_global.get("barre_outils", {})

    if app.mode_persistant_actif:
        boutons = [
            (m_json.get("onboarding", "🏠 Accueil"), "ONBOARDING"),
            (m_json.get("devoirs_hub", "⚖️ Devoirs"), "DEVOIRS"),       
            (m_json.get("inventaire_hub", "📦 Mon Inventaire"), "INVENTAIRE"),
            (m_json.get("madrassa_hub", "🏫 Madrassa"), "MADRASSA"),
            (m_json.get("reglages", "⚙️ Réglages"), "REGLAGES"),
        ]
    else:
        boutons = [
            (m_json.get("onboarding", "🏠 Accueil"), "ONBOARDING"),
            (f"{m_json.get('zakat', '🏦 Zakat')} - {b_json.get('mode_tiers', 'Simulation')}", "ZAKAT_TIERS"), 
            (f"{m_json.get('heritage', '📜 Succession')} - {b_json.get('mode_tiers', 'Simulation')}", "HERITAGE_TIERS"),
            (m_json.get("madrassa_hub", "🏫 Madrassa"), "MADRASSA"),
        ]

    # --- FORMAT SMARTPHONE ---
    if app.mode_smartphone_actif:
        b_el = ft.Row(
            scroll=ft.ScrollMode.ADAPTIVE,
            spacing=5,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER
        )
        for lib, cle in boutons:
            # ⚠️ CORRECTION 09/09/2026 : en mode visiteur, "lib" pour Zakat
            # et Succession vaut par exemple "🏦 Zakat - 🟡 Visiteur" (le
            # texte complet, avec le suffixe de mode ajouté plus haut).
            # L'ancien code faisait lib.split(" ")[-1] directement dessus,
            # ce qui prenait le DERNIER mot de la chaîne entière — donc
            # "Visiteur" (dernier mot du suffixe) au lieu de "Zakat"
            # (dernier mot du libellé réel). On retire d'abord le
            # suffixe " - ..." s'il existe, puis on extrait l'emoji et le
            # mot depuis le libellé de base uniquement. Pour les boutons
            # sans suffixe (Accueil, Madrassa...), split(" - ") ne trouve
            # rien à couper et lib_de_base reste égal à lib, comportement
            # inchangé.
            lib_de_base = lib.split(" - ")[0]
            lib_c = lib_de_base.split(" ")[-1] if " " in lib_de_base else lib_de_base
            em = lib_de_base.split(" ")[0] if " " in lib_de_base else "•"
            est_a = (app.ecran_courant == cle)

            btn_mob = ft.Container(
                content=ft.Column([
                    ft.Text(value=str(em), size=14, text_align=ft.TextAlign.CENTER),
                    ft.Text(value=str(lib_c), size=9, weight=ft.FontWeight.BOLD if est_a else ft.FontWeight.NORMAL, text_align=ft.TextAlign.CENTER)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                bgcolor="#e5e7eb" if est_a else "#f3f4f6",
                padding=ft.Padding(12, 4, 12, 4),
                border_radius=6,
                on_click=lambda e, c=cle: app.basculer_ecran(c)
            )
            b_el.controls.append(btn_mob)
        app.barre_navigation.content = b_el

    # --- FORMAT PC ---
    else:
        m_vert = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=2, expand=True)
        m_vert.controls.append(ft.Container(height=8, bgcolor="#f3f4f6"))
        for lib, cle in boutons:
            est_a = (app.ecran_courant == cle)

            def gerer_survol_bouton(e, c_cle=cle):
                if app.ecran_courant == c_cle: 
                    e.control.bgcolor = "#d1d5db"
                else: 
                    e.control.bgcolor = "#e5e7eb" if e.data == "true" else "#f3f4f6"
                try: e.control.update()
                except Exception: pass

            btn_pc = ft.Container(
                content=ft.Text(value=str(lib), size=12, color=ft.Colors.BLACK87, weight=ft.FontWeight.BOLD if est_a else ft.FontWeight.NORMAL),
                bgcolor="#d1d5db" if est_a else "#f3f4f6", padding=ft.Padding(15, 10, 15, 10), alignment=ft.Alignment(-1, 0),
                on_click=lambda e, t_c=cle: app.basculer_ecran(t_c), on_hover=gerer_survol_bouton
            )
            m_vert.controls.append(btn_pc)
        app.barre_navigation.content = m_vert
