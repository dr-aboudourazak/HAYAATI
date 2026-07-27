"""
LIVRE DE COMPTES SPIRITUEL (GUI/COMPONENTS/INTERFACE_MOUHASABAH.PY)
Version Finale Intégrale Statique - Totalement compatible Flet 0.86.2, Python 3.14 & APK Android
"""
from __future__ import annotations
import flet as ft
import sqlite3
import asyncio
from datetime import datetime, timedelta
from gui.langues import DICTIONNAIRE_LANGUES
from core.agenda_engine import AgendaEngine
from core.time_engine import gregorien_vers_hegiri

class EcranMouhasabah(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self.mode_mobile = None
        self.moteur_agenda = AgendaEngine()
        self.vars_jeune_dynamique: dict[str, ft.Checkbox] = {} 
        self.mois_simulation_test = None
        self.prieres = ["fajr", "dhouhr", "asr", "maghrib", "isha"]
        
        # --- 1. INSTANCIATION DES COMPOSANTS GRAPHIQUES MATERIAL 3 ---
        # 📂 BLOC 1 : FORMULAIRE STANDARD (PRIÈRES & ACTIONS OBLIGATOIRES)
        self.lbl_cadre_form = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.lbl_prieres = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#4b5563")
        self.chks_p: dict[str, ft.Checkbox] = {}
        
        self.grille_prieres = ft.ResponsiveRow(spacing=5, run_spacing=5)
        for p in self.prieres:
            self.chks_p[p] = ft.Checkbox(value=False, active_color="#064e3b")
            self.grille_prieres.controls.append(ft.Container(content=self.chks_p[p], col={"xs": 6, "sm": 4, "md": 2.4}))

        self.lbl_merite = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#4b5563")
        self.chk_nawafil = ft.Checkbox(value=False, active_color="#064e3b")
        self.chk_sadaqah = ft.Checkbox(value=False, active_color="#064e3b")
        self.chk_hadj = ft.Checkbox(value=False, active_color="#0f766e", label_style=ft.TextStyle(weight=ft.FontWeight.BOLD))

        self.grille_merite = ft.ResponsiveRow(spacing=10, run_spacing=5)
        self.grille_merite.controls.extend([
            ft.Container(content=self.chk_nawafil, col={"xs": 12, "md": 4}),
            ft.Container(content=self.chk_sadaqah, col={"xs": 12, "md": 4}),
            ft.Container(content=self.chk_hadj, col={"xs": 12, "md": 4})
        ])

        self.cadre_form = ft.Container(
            content=ft.Column([
                self.lbl_cadre_form,
                self.lbl_prieres,
                self.grille_prieres,
                ft.Container(height=2),
                self.lbl_merite,
                self.grille_merite
            ], spacing=6),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#064e3b")
        )

        # 📂 BLOC 2 : LE CADRE CONTEXTUEL LUNAIRE FLUIDE MATERIAL 3
        self.lbl_cadre_lunaire = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#d97706")
        self.colonne_lunaire_interne = ft.Column(spacing=4, tight=True)
        self.cadre_lunaire_dynamique = ft.Container(
            content=ft.Column([self.lbl_cadre_lunaire, self.colonne_lunaire_interne], spacing=6),
            bgcolor="#fdfbf7", padding=12, border_radius=8, border=ft.Border.all(1, "#d97706"),
            visible=False
        )

        # Bouton d'enregistrement maître (Syntaxe immunisée Python 3.14)
        self.btn_sauver = ft.ElevatedButton(
            content=ft.Text("Enregistrer", size=13, weight=ft.FontWeight.BOLD),
            bgcolor="#064e3b", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.sauvegarder()
        )

        # 📂 BLOC 3 : CONFINEMENT DE L'HISTORIQUE EN LECTURE SEULE
        self.lbl_cadre_res = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.text_hist = ft.TextField(
            multiline=True, min_lines=2, max_lines=4, text_size=12, read_only=True,
            border_color=ft.Colors.GREY_400, bgcolor="#f9fafb"
        )
        self.cadre_res = ft.Container(
            content=ft.Column([self.lbl_cadre_res, self.text_hist], spacing=6),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#064e3b")
        )

        # Bandeau de statut inférieur muni d'une action interactive de simulation sacrée
        self.lbl_status = ft.Text(size=12, italic=True, color="#4b5563", text_align=ft.TextAlign.CENTER)
        self.c_notif = ft.Container(
            content=ft.GestureDetector(
                content=self.lbl_status,
                on_double_tap=lambda _: self.basculer_mode_simulation_demonstration()
            ),
            bgcolor="#f3f4f6", padding=10, border_radius=6, alignment=ft.Alignment(0, 0)
        )

        # Structure globale défilante
        self.layout_mouhasabah = ft.Column([
            self.cadre_form,
            self.cadre_lunaire_dynamique,
            self.btn_sauver,
            self.cadre_res,
            self.c_notif
        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

        super().__init__(
            content=self.layout_mouhasabah, expand=True, bgcolor="#f8fafc",
            padding=ft.Padding(left=15, right=15, top=15, bottom=15)
        )

        # Liaison avec le gestionnaire de langue i18n
        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_langue)
            
        # 🎯 DÉCLENCHEMENT DE LA TÂCHE DE RAZ QUOTIDIENNE ASYNCHRONE SECURISEE FLET 0.86.2
        if self.page_flet:
            self.page_flet.run_task(self.planifier_reinitialisation_mouhasabah)
            
        self.actualiser_donnees_affichage()

    def action_langue(self, dic: dict):
        """Met à jour l'interface lors d'une modification linguistique globale."""
        self.traduire_page(dic)

    async def planifier_reinitialisation_mouhasabah(self, *args):
        """Calcule l'instant cible 1h avant Fadjr et arme l'attente asynchrone non-bloquante."""
        heure_fadjr_str = "05:00"
        if hasattr(self.app, "horaires_prieres_aujourdhui") and self.app.horaires_prieres_aujourdhui:
            heure_fadjr_str = self.app.horaires_prieres_aujourdhui.get("Fajr", "05:00")
        
        try:
            h_f, m_f = map(int, heure_fadjr_str.split(":"))
            temps_fadjr = datetime.now().replace(hour=h_f, minute=m_f, second=0, microsecond=0)
        except Exception:
            temps_fadjr = datetime.now().replace(hour=5, minute=0, second=0, microsecond=0)

        # Soustraction exacte d'une heure (60 minutes avant le Fadjr)
        instant_raz_cible = temps_fadjr - timedelta(hours=1)
        maintenant = datetime.now()

        if maintenant > instant_raz_cible:
            instant_raz_cible += timedelta(days=1)

        delai_secondes = (instant_raz_cible - maintenant).total_seconds()
        
        # Attente asynchrone thread-safe
        await asyncio.sleep(max(0.1, delai_secondes))
        self.executer_remise_a_zero_quotidienne()

    # ============================================================
    # 🎯 PARTIE 2A : ANIMATION LUNAIRE DYNAMIQUE ET TRADUCTION DE PAGE
    # ============================================================

    def basculer_mode_simulation_demonstration(self):
        """Permet de faire défiler manuellement les mois sacrés en cliquant sur le statut pour tester l'IHM."""
        if self.mois_simulation_test is None: 
            self.mois_simulation_test = 9
        elif self.mois_simulation_test == 9: 
            self.mois_simulation_test = 1
        elif self.mois_simulation_test == 1: 
            self.mois_simulation_test = 12
        else: 
            self.mois_simulation_test = None
        self.actualiser_donnees_affichage()

    def animer_terrain_de_jeu_lunaire(self, mois_h: int, jour_h: int):
        """Anime et injecte des contrôles spécifiques selon le mois du calendrier islamique."""
        self.colonne_lunaire_interne.controls.clear()
        self.vars_jeune_dynamique.clear()
        self.cadre_lunaire_dynamique.visible = False
        
        langue_act = DICTIONNAIRE_LANGUES.actif
        ev = langue_act.get("evenements_islamiques", {})
        onb = langue_act.get("onboarding", {})

        # Surcharges des variables en mode démonstration double-clic
        if self.mois_simulation_test is not None:
            mois_h = self.mois_simulation_test

        # 🌙 CAS 1 : MOIS DE RAMADAN (Mois 9)
        if mois_h == 9:
            nom_m = onb.get("mois_nom_9", "Ramadan")
            self.lbl_cadre_lunaire.value = f"🌙 {nom_m} : {ev.get('evt_ramadan', '')[:40]}"
            self.cadre_lunaire_dynamique.visible = True
            
            chk_ram = ft.Checkbox(value=False, active_color="#064e3b", text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color="#064e3b"))
            chk_ram.label = f"{nom_m} ({jour_h})"
            
            self.vars_jeune_dynamique["ramadan_jeune"] = chk_ram
            self.colonne_lunaire_interne.controls.append(chk_ram)

        # 🌙 CAS 2 : MOIS DE MUHARRAM (Mois 1)
        elif mois_h == 1:
            nom_m = onb.get("mois_nom_1", "Muharram")
            self.lbl_cadre_lunaire.value = f"📿 {nom_m} : {ev.get('evt_achoura', '')[:40]}"
            self.cadre_lunaire_dynamique.visible = True
            
            chk_tassoua = ft.Checkbox(value=False, active_color="#064e3b", label="9 (Tassou'a)")
            chk_achoura = ft.Checkbox(value=False, active_color="#0f766e", label="10 (Achoura)", text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color="#0f766e"))
            
            self.vars_jeune_dynamique["achoura_9"] = chk_tassoua
            self.vars_jeune_dynamique["achoura_10"] = chk_achoura
            self.colonne_lunaire_interne.controls.extend([chk_tassoua, chk_achoura])

        # 🌙 CAS 3 : MOIS DE DHU AL-HIJJAH (Mois 12) -> Suivi des 9 premiers jours & Arafat
        elif mois_h == 12:
            nom_m = onb.get("mois_nom_12", "Dhu al-Hijjah")
            self.lbl_cadre_lunaire.value = f"🌟 {nom_m} : {ev.get('evt_arafa', '')[:40]}"
            self.cadre_lunaire_dynamique.visible = True
            
            chk_neuf = ft.Checkbox(value=False, active_color="#064e3b", label=f"{nom_m} ({jour_h})")
            self.vars_jeune_dynamique["neuf_jours"] = chk_neuf
            self.colonne_lunaire_interne.controls.append(chk_neuf)
            
            if jour_h == 9 or self.mois_simulation_test is not None:
                chk_arafat = ft.Checkbox(value=False, active_color="#b91c1c", label=ev.get("evt_arafa", "Arafat"), text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color="#b91c1c"))
                self.vars_jeune_dynamique["arafat"] = chk_arafat
                self.colonne_lunaire_interne.controls.append(chk_arafat)

        if self.page_flet:
            try: self.update()
            except Exception: pass

    def traduire_page(self, dic: dict):
        """Met à jour les textes de l'écran en lisant uniquement les clés i18n dynamiques du JSON."""
        if not dic:
            return
        m = dic.get("mouhasabah", {})
        menu_json = dic.get("menu", {})
        
        # Configuration des titres de cadres de manière réactive
        self.lbl_cadre_form.value = str(menu_json.get("mouhasabah", "Mouhasabah"))
        self.lbl_prieres.value = str(m.get("cadre_obligations", "Prières :"))
        self.lbl_merite.value = str(menu_json.get("profil", "Actions :"))
        
        # 1. Traduction immédiate des intitulés individuels de coche des 5 prières
        prieres_json = m.get("prieres", {})
        for p in self.prieres:
            self.chks_p[p].label = str(prieres_json.get(p, p.capitalize()))

        # 2. SÉCURITÉ I18N UNIVERSELLE : Lecture directe des clés courtes du dictionnaire actif
        lbl_nawafil = m.get("lbl_nawafil_court", "Nawafil")
        lbl_sadaqah = m.get("lbl_sadaqah_court", "Sadaqah")
        lbl_hadj = m.get("lbl_hadj_court", "Hadj")

        # Injection propre sans manipulation risquée
        self.chk_nawafil.label = f"✅ {lbl_nawafil}"
        self.chk_sadaqah.label = f"✨ {lbl_sadaqah}"
        self.chk_hadj.label = f"🕋 {lbl_hadj}"
        
        if self.btn_sauver.content:
            self.btn_sauver.content.value = str(m.get("btn_valider_journee", "Enregistrer la journée"))
        self.lbl_cadre_res.value = str(dic.get("audit", {}).get("titre_graphique_evolution", "Historique"))

        # 🎯 FIX TECHNIQUE SÉCURISÉ FLUIDE FLUTTER : On pousse l'état de rendu
        if self.page_flet:
            try:
                self.update()
            except Exception:
                pass

    # ============================================================
    # 🎯 PARTIE 2B : HYDRATATION ET SYNCHRONISATION DE LA MÉMOIRE VIVE
    # ============================================================

    def sauvegarder(self):
        """Calcule le score spirituel et persiste le payload sur le disque dur."""
        if not getattr(self.app, "est_mode_connecte", False): 
            return
        try:
            nb = sum([1 for p in self.prieres if self.chks_p[p].value])
            bonus_lunaire = sum([15 for v in self.vars_jeune_dynamique.values() if v.value])
            
            score = (nb * 15) + (12 if self.chk_nawafil.value else 0) + (13 if self.chk_sadaqah.value else 0) + bonus_lunaire
            if score > 100: 
                score = 100
            
            # Concaténation de la ligne d'historique (Simule l'insertion 1.0 Tkinter)
            nouvelle_ligne = f"📿 [{datetime.now().strftime('%d/%m/%Y %H:%M')}] - Score: {score}%\n"
            historique_existant = str(self.text_hist.value or "")
            self.text_hist.value = nouvelle_ligne + historique_existant
            
            if getattr(self.app, "sync_engine", None):
                donnees = {p: (1 if self.chks_p[p].value else 0) for p in self.prieres}
                donnees.update({
                    "score_spirituel": score, 
                    "nawafil": (1 if self.chk_nawafil.value else 0), 
                    "sadaqah": (1 if self.chk_sadaqah.value else 0), 
                    "deja_fait_hadj": (1 if self.chk_hadj.value else 0), 
                    "historique": str(self.text_hist.value)
                })
                for k, v in self.vars_jeune_dynamique.items(): 
                    donnees[k] = (1 if v.value else 0)
                
                self.app.sync_engine.executer_sauvegarde_module(self.app.user_id_connecte, "MOUHASABAH", donnees)
                
            self.actualiser_donnees_affichage()
        except Exception: 
            pass

    def injecter_donnees(self, data: dict | None):
        """Réinjecte la sauvegarde au sein de l'interface graphique Flet."""
        if not data: 
            return
        for p in self.prieres: 
            self.chks_p[p].value = (int(data.get(p, 0)) == 1)
        self.chk_nawafil.value = (int(data.get("nawafil", 0)) == 1)
        self.chk_sadaqah.value = (int(data.get("sadaqah", 0)) == 1)
        
        # 🎯 SÉCURITÉ PERSISTANCE : Maintien de l'état coché à vie pour le Hadj accompli
        self.chk_hadj.value = (int(data.get("deja_fait_hadj", 0)) == 1)
        
        for k, v in self.vars_jeune_dynamique.items(): 
            v.value = (int(data.get(k, 0)) == 1)
            
        self.text_hist.value = str(data.get("historique", ""))
        
        if self.page_flet:
            try: self.update()
            except Exception: pass

    def actualiser_donnees_affichage(self):
        """Cycle de vie : Recharge les dévotions et force l'affichage i18n différé."""
        self.lbl_status.value = ""
        self.c_notif.bgcolor = "#f3f4f6"
        self.lbl_status.color = "#4b5563"
        
        # 1. Extraction immédiate des données SQLite du SyncEngine (Synchrone)
        u_id = getattr(self.app, "user_id_connecte", "INVITE")
        if u_id != "INVITE" and hasattr(self.app, "sync_engine"):
            donnees_mouh = self.app.sync_engine.charger_donnees_module(u_id, "MOUHASABAH")
            self.injecter_donnees(donnees_mouh)
            
        # 2. 🎯 TÂCHE ASYNCHRONNE DIFFÉRÉE : On laisse 60ms à Flutter pour afficher la page
        # avant d'y injecter de force l'ensemble des labels i18n
        async def executer_traduction_differee(*args):
            import asyncio
            await asyncio.sleep(0.06)
            self.traduire_page(DICTIONNAIRE_LANGUES.actif)
            
        if self.page_flet:
            self.page_flet.run_task(executer_traduction_differee)

    def changer_langue(self, n_lang: str): 
        """Propagation descendante i18n."""
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def actualiser_contexte(self):
        """Routeur central."""
        self.actualiser_donnees_affichage()
