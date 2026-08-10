"""
EXTENSION ALGORITHMIQUE DES ALERTES SHARIA (GUI/PAGE_ONBOARDING_ALERTS.PY)
Version 4.4 — Logs explicites, f-strings sans \n, SnackBar robuste
"""
from __future__ import annotations
from datetime import datetime, timedelta
import json
import os
import sys
import sqlite3
from pathlib import Path
import flet as ft

from core.agenda_engine import AgendaEngine
from core.time_engine import gregorien_vers_hegiri, obtenir_evenement_hegiri
from core.notification_engine import notifier_via_scheduler, _is_android
from gui.langues import DICTIONNAIRE_LANGUES


# ============================================================================
# DÉDOUBLONNAGE PERSISTANT AVEC LOGS EXPLICITES
# ============================================================================
class _DedupJournalier:
    def __init__(self, nom_fichier: str = "hayaati_notif_dedup.json"):
        self.chemin = Path(__file__).parent.parent.parent / nom_fichier
        self._data: dict = {}
        self._charger()

    def _charger(self):
        if self.chemin.exists():
            try:
                with open(self.chemin, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                print(f"[DEDUP] Fichier charge : {self.chemin}")
            except Exception:
                self._data = {}
        else:
            print(f"[DEDUP] Fichier inexistant : {self.chemin}")

    def _sauver(self):
        try:
            with open(self.chemin, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False)
        except Exception as exc:
            print(f"[DEDUP] Sauvegarde impossible : {exc}")

    def deja_envoye(self, cle: str) -> bool:
        auj = datetime.now().strftime("%Y-%m-%d")
        result = self._data.get(cle) == auj
        if result:
            print(f"[DEDUP] BLOQUE '{cle}' — deja envoye le {auj}")
        else:
            print(f"[DEDUP] PERMIS '{cle}' — pas encore envoye aujourd'hui")
        return result

    def marquer_envoye(self, cle: str):
        self._data[cle] = datetime.now().strftime("%Y-%m-%d")
        self._sauver()
        print(f"[DEDUP] MARQUE '{cle}' comme envoye aujourd'hui")

    def reinitialiser(self):
        self._data.clear()
        if self.chemin.exists():
            try:
                self.chemin.unlink()
                print("[DEDUP] Fichier supprime")
            except Exception as exc:
                print(f"[DEDUP] Echec suppression : {exc}")


_dedup = _DedupJournalier()


def obtenir_chemin_base_donnees() -> str:
    nom_db = "hayaati_private.db"
    if _is_android():
        d_and = os.path.dirname(sys.executable) if hasattr(sys, "executable") else os.getcwd()
        chemin = os.path.join(d_and, nom_db)
        if not os.path.exists(chemin):
            c_orig = os.path.join("core", nom_db)
            if os.path.exists(c_orig):
                try:
                    import shutil
                    shutil.copy(c_orig, chemin)
                except Exception:
                    return c_orig
        return chemin
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "core", nom_db))


def _obtenir_heure_fadjr() -> str:
    try:
        main_mod = sys.modules.get("main")
        if main_mod and hasattr(main_mod, "APPLICATION_HAYAATI_INSTANCE"):
            app = main_mod.APPLICATION_HAYAATI_INSTANCE
            if hasattr(app, "horaires_prieres_aujourdhui") and app.horaires_prieres_aujourdhui:
                return app.horaires_prieres_aujourdhui.get("Fajr", "05:00")
    except Exception:
        pass
    return "05:00"


def compiler_alertes_espace_prive(
    c_fin: dict, c_sp: dict, net: float, dev: str, fiqh: str,
    user_id: str | None = None, ajustement_lune: int = 0,
    page_flet: ft.Page | None = None, scheduler=None,
):
    print("[ALERTES] === compiler_alertes_espace_prive ===")
    moteur_agenda = AgendaEngine()
    txt_onb = DICTIONNAIRE_LANGUES.actif.get("onboarding", {})
    txt_mouh = DICTIONNAIRE_LANGUES.actif.get("mouhasabah", {})

    maintenant = datetime.now()
    heure_fadjr_str = _obtenir_heure_fadjr()

    try:
        h_f, m_f = map(int, heure_fadjr_str.split(":"))
        instant_bascule = maintenant.replace(hour=h_f, minute=m_f, second=0, microsecond=0) - timedelta(hours=1)
    except Exception:
        instant_bascule = maintenant.replace(hour=4, minute=0, second=0, microsecond=0)

    date_etude_sharia = maintenant - timedelta(days=1) if maintenant < instant_bascule else maintenant

    prieres_profil = {p: c_sp.get(p, 0) for p in ["fajr", "dhouhr", "asr", "maghrib", "isha"]}
    manquees = moteur_agenda.evaluer_prieres_manquees_en_direct(prieres_profil, madhhab_actif=fiqh)
    print(f"[ALERTES] Prieres manquees : {manquees}")

    prieres_json = txt_mouh.get("prieres", {})
    if manquees:
        trad_manquees = [prieres_json.get(p, p.capitalize()) for p in manquees]
        chaine_prieres = ", ".join(trad_manquees)
        txt_pr = txt_onb.get("prieres_manquees", "VIGILANCE PRIERE : {}").format(chaine_prieres)
        bg_c, fg_c = "#fee2e2", "#991b1b"
    else:
        txt_pr = txt_onb.get("prieres_ok", "Excellent.")
        bg_c, fg_c = "#d1fae5", "#166534"

    txt_cal = ""
    h_date = gregorien_vers_hegiri(
        date_etude_sharia.year, date_etude_sharia.month, date_etude_sharia.day,
        ajustement_fiqh=ajustement_lune,
    )

    cle_mois = "mois_nom_" + str(h_date["mois_num"])
    nom_mois_traduit = txt_onb.get(cle_mois, h_date["mois_nom"])
    txt_cal += "📅 " + str(h_date["jour"]) + " " + str(nom_mois_traduit) + " " + str(h_date["annee"]) + " AH\n\n"

    if date_etude_sharia.weekday() == 4:
        txt_cal += txt_onb.get("joumouah", "VENDREDI.\n\n")

    if user_id:
        try:
            with sqlite3.connect(obtenir_chemin_base_donnees()) as conn:
                curseur = conn.cursor()
                curseur.execute("SELECT date_naissance FROM comptes_utilisateurs WHERE user_id = ?", (str(user_id),))
                db_res = curseur.fetchone()
            if db_res and db_res[0]:
                date_naiss = datetime.strptime(db_res[0], "%Y-%m-%d")
                jours_solaires = (date_etude_sharia - date_naiss).days
                age_islamique = jours_solaires / 354.367
                txt_cal += txt_onb.get("age_islamique", "AGE : {:.1f} ans.\n").format(age_islamique)
                if (date_etude_sharia.day, date_etude_sharia.month) == (date_naiss.day, date_naiss.month):
                    txt_cal += txt_onb.get("anniversaire_alerte", "RAPPEL RE-CYCLE ANNUEL.\n\n")
        except Exception:
            pass

    evenement_lunaire = obtenir_evenement_hegiri(h_date["mois_num"], h_date["jour"])
    phrase_traduite = None
    if evenement_lunaire:
        cle_evt = str(evenement_lunaire).strip()
        dict_evt = txt_onb.get("evenements", {})
        if cle_evt == "evt_jours_blancs":
            phrase_traduite = txt_onb.get("jours_blancs")
        elif cle_evt.startswith("evt_dhu_hijjah_"):
            jour_idx = cle_evt.split("_")[-1]
            base = dict_evt.get("evt_dhu_hijjah_base", "10 PREMIERS JOURS DE DHU AL-HIJJAH (Jour {}) : Multipliez le Tasbih et le Takbir.")
            try:
                phrase_traduite = base.format(jour_idx)
            except Exception:
                phrase_traduite = base
        else:
            phrase_traduite = dict_evt.get(cle_evt)
        if phrase_traduite:
            txt_cal += str(phrase_traduite) + "\n\n"

    txt_cal += txt_onb.get("entete_devotion", "EXAMEN DE VIGILANCE SPIRITUELLE DU JOUR :\n")

    nawafil = int(c_sp.get("nawafil", 0))
    sadaqah = int(c_sp.get("sadaqah", 0))
    txt_cal += txt_onb.get("nawafil_ok" if nawafil == 1 else "nawafil_ko", "").format("") + "\n"
    txt_cal += txt_onb.get("sadaqah_ok" if sadaqah == 1 else "sadaqah_ko", "").format("") + "\n\n"

    deja_fait_hadj = int(c_sp.get("deja_fait_hadj", 0))
    seuil_hadj = 3500000.0 if dev in ("XOF", "FCFA") else 5500.0
    if net >= seuil_hadj:
        if deja_fait_hadj == 1:
            txt_cal += txt_onb.get("hadj_ok", "HADJ ACCOMPLI.\n")
        else:
            txt_cal += txt_onb.get("hadj_ko", "APTITUDE HADJ ACTIVE ({:.0f} {}).\n").format(net, dev)

    if h_date["mois_num"] == 1:
        txt_cal += txt_onb.get("fin_muharram", "CHRONOLOGIE : MOUHARRAM.\n\n")

    txt_cal += txt_onb.get("general_devotion", "MEMOIRE DU QUOTIDIEN.")

    print(f"[ALERTES] page_flet={page_flet is not None}, scheduler={scheduler is not None}")

    if page_flet:
        if manquees:
            print("[ALERTES] Test envoi prieres...")
            # 🆕 DEDUP PAR PRIÈRE : chaque prière manquée a sa propre clé journalière
            prieres_non_notifiees = [p for p in manquees if not _dedup.deja_envoye(f"priere:{p}")]
            if prieres_non_notifiees:
                trad_manquees_filtre = [prieres_json.get(p, p.capitalize()) for p in prieres_non_notifiees]
                chaine_prieres_filtre = ", ".join(trad_manquees_filtre)
                titre = "HAYAATI - " + str(txt_mouh.get("cadre_obligations", "Prieres Echues")).replace(":", "").strip()
                corps = str(txt_onb.get("prieres_manquees", "VIGILANCE PRIERE : {}")).format(chaine_prieres_filtre)
                corps = corps.replace("⚠️ ", "").replace("\n", " ").strip()
                print(f"[ALERTES] Envoi NOTIF PRIERES : {titre}")
                notifier_via_scheduler(scheduler, page_flet, titre, corps)
                for p in prieres_non_notifiees:
                    _dedup.marquer_envoye(f"priere:{p}")
            else:
                print("[ALERTES] Prieres SKIP (toutes deja envoyees)")
        else:
            print("[ALERTES] Aucune priere manquee → pas de notif")

        if evenement_lunaire and phrase_traduite:
            print("[ALERTES] Test envoi lunaire...")
            # 🆕 DEDUP PAR ÉVÉNEMENT : clé basée sur mois + jour hégirien
            cle_lunaire = f"lunaire:{h_date['mois_num']}:{h_date['jour']}"
            if not _dedup.deja_envoye(cle_lunaire):
                titre = "HAYAATI - " + str(txt_onb.get("cadre_calendrier", "Chronologie Sacree")).strip()
                corps = str(phrase_traduite).replace("🌟 ", "").replace("📅 ", "").replace("⚪ ", "").strip()
                if "." in corps:
                    corps = corps.split(".")[0] + "."
                print(f"[ALERTES] Envoi NOTIF LUNAIRE : {titre}")
                notifier_via_scheduler(scheduler, page_flet, titre, corps)
                _dedup.marquer_envoye(cle_lunaire)
            else:
                print("[ALERTES] Lunaire SKIP (deja envoye)")
        else:
            print("[ALERTES] Aucun evenement lunaire → pas de notif")
    else:
        print("[ALERTES] page_flet=None → notifications desactivees")

    print("[ALERTES] === FIN ===")
    return txt_pr, txt_cal, bg_c, fg_c


def compiler_et_dessiner_les_3_carrousels(instance_onboarding, txt_cal_complet, txt_onb):
    if not hasattr(instance_onboarding, "layout_principal"):
        return

    lignes = [l.strip() for l in txt_cal_complet.split("\n") if l.strip()]

    devotion_brute = str(txt_onb.get("general_devotion", ""))
    recommandations = [l.strip() for l in devotion_brute.split("\n") if "•" in l]
    if not recommandations:
        recommandations = [
            "📖 Coran : Consacrez un moment aujourd'hui a la lecture.",
            "📿 Adhkar : Evocations du matin et du soir.",
            "🤝 Comportement : Bienveillance et preservation de la langue.",
        ]

    it_chrono, it_patrimoine, it_spirit = [], [], []
    for l in lignes:
        if any(k in l for k in ("📖 MEMOIRE", "📿 EXAMEN", "Coran :", "Adhkar :", "Comportement :")):
            continue
        if any(k in l for k in ("📅", "🎂", "⚪", "📌", "✨", "🌟", "MOUHARRAM", "Aïd", "Achoura")):
            it_chrono.append(l)
        elif any(k in l for k in ("HADJ", "UDHIYAH", "🕋", "🐑", "💰", "Zakat", "Nisab", "Epargne")):
            it_patrimoine.append(l)
        else:
            it_spirit.append(l)

    it_patrimoine.extend(recommandations)
    if not it_spirit:
        it_spirit = [str(txt_onb.get("prieres_ok", "Excellent : Toutes vos prieres sont validees."))]

    def fabriquer_bloc(titre: str, items: list, color: str, bg: str, border: str, cle: str):
        lv = ft.ListView(
            expand=True, spacing=15, padding=ft.Padding(12, 0, 12, 0),
            scroll=ft.ScrollMode.AUTO, horizontal=True,
        )
        for txt_item in items:
            lv.controls.append(
                ft.Container(
                    content=ft.Text(value=str(txt_item), size=11, weight=ft.FontWeight.W_500, color=color, text_align=ft.TextAlign.CENTER),
                    bgcolor=bg, padding=12, border_radius=8, border=ft.Border.all(1, border), width=290, alignment=ft.Alignment(0, 0),
                )
            )
        cadre = ft.Container(
            content=ft.Column([
                ft.Text(value=str(titre), size=12, weight=ft.FontWeight.BOLD, color=color),
                ft.Container(content=lv, height=80),
            ], spacing=4),
            bgcolor=ft.Colors.WHITE, padding=10, border_radius=8, border=ft.Border.all(1, border), height=135,
        )
        setattr(instance_onboarding, f"lv_{cle}", lv)
        return cadre

    titre_chrono = "🌙 " + txt_onb.get("cadre_calendrier", "Chronologie Sacree").strip()
    titre_patrimoine = "💰 " + txt_onb.get("titre_fortune", "Vigilance Patrimoine").strip()
    titre_spirit = "📿 " + txt_onb.get("titre_mouhasabah", "Examen Spirituel").strip()

    cadre_chrono = fabriquer_bloc(titre_chrono, it_chrono, "#0f766e", "#f0fdfa", "#ccfbf1", "chrono")
    cadre_patrimoine = fabriquer_bloc(titre_patrimoine, it_patrimoine, "#b45309", "#fffbeb", "#fef3c7", "patrimoine")
    cadre_spirit = fabriquer_bloc(titre_spirit, it_spirit, "#047857", "#f0fdf4", "#dcfce7", "spirit")

    zone = getattr(instance_onboarding, "zone_statique_des_carrousels", None)
    colonne = ft.Column(controls=[cadre_chrono, cadre_patrimoine, cadre_spirit], spacing=12, scroll=ft.ScrollMode.AUTO)

    if zone is None or zone not in instance_onboarding.layout_principal.controls:
        instance_onboarding.zone_statique_des_carrousels = ft.Container(content=colonne, padding=ft.Padding(0, 5, 0, 5), height=440)
        if hasattr(instance_onboarding, "cadre_calendrier") and instance_onboarding.cadre_calendrier in instance_onboarding.layout_principal.controls:
            instance_onboarding.layout_principal.controls.remove(instance_onboarding.cadre_calendrier)
        instance_onboarding.layout_principal.controls.append(instance_onboarding.zone_statique_des_carrousels)
    else:
        instance_onboarding.zone_statique_des_carrousels.content = colonne

    try:
        _ = instance_onboarding.page
        instance_onboarding.update()
    except RuntimeError:
        pass

    async def _scroll_delay():
        import asyncio
        await asyncio.sleep(0.6)
        for cle in ("chrono", "patrimoine", "spirit"):
            ctrl = getattr(instance_onboarding, f"lv_{cle}", None)
            if ctrl:
                try:
                    await ctrl.scroll_to(offset=60, duration=600)
                except Exception:
                    pass

    if instance_onboarding.page_flet:
        try:
            instance_onboarding.page_flet.run_task(_scroll_delay)
        except Exception:
            pass
