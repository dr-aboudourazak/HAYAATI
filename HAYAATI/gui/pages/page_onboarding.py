"""
PANNEAU D'ACCUEIL INTERACTIF CONNECTÉ (GUI/PAGES/PAGE_ONBOARDING.PY)
Version 4.6 — Minuteur de secours à 0.3s retiré. Il compensait un vrai bug
              d'ordonnancement dans app_layout.py (basculer_vers_ecran()
              appelait actualiser_donnees_affichage() avant self.update(),
              donc avant que self.page ne soit défini). Ce bug est corrigé
              à la source dans app_layout.py — actualiser_donnees_affichage()
              y est maintenant appelé après le montage réel de l'écran.
              Le minuteur ne servait plus qu'à retarder inutilement le
              premier affichage, avec en plus un risque de double-rendu si
              son tir à 0.3s arrivait après l'appel désormais correct de
              basculer_vers_ecran().
"""
from __future__ import annotations
import asyncio
import flet as ft
from datetime import datetime, timedelta
from gui.langues import DICTIONNAIRE_LANGUES
from gui.pages.page_onboarding_alerts import compiler_alertes_espace_prive
from gui.pages.page_onboarding_calendrier import construire_grille_calendrier
from gui.pages.page_onboarding_vivant import construire_badge_kaaba, construire_bandeau_versets


class PageOnboarding(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self.mode_smartphone_interne = None

        self.lbl_bienvenue = ft.Text(size=20, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.lbl_sous_titre = ft.Text(size=12, italic=True, color="#4b5563")

        # 🆕 12/09/2026 : badge Kaaba vivant (compte à rebours) + bandeau
        # de versets/hadiths qui alterne — les deux éléments "vivants"
        # validés par maquette avant intégration.
        self.badge_kaaba, self._rafraichir_badge_kaaba = construire_badge_kaaba(app_reference)
        self.bandeau_versets, self._basculer_verset = construire_bandeau_versets()
        self._boucles_vivantes_actives = True
        self.lbl_titre_prieres = ft.Text(value="🕋 Prières Échues", size=12, weight=ft.FontWeight.BOLD, color="#b91c1c")

        self.grille_metrics = ft.ResponsiveRow(spacing=15, run_spacing=12)

        self.c_prieres = ft.Column(spacing=5, tight=True)
        self.cadre_prieres = ft.Container(
            content=ft.Column([
                self.lbl_titre_prieres,
                self.c_prieres
            ], spacing=6),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#b91c1c"),
            visible=False, expand=True
        )

        # Layout initial vide — actualiser_contexte() décide du contenu,
        # appelé par app_layout.py juste après le montage réel de l'écran.
        self.layout_principal = ft.Column(
            [],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH
        )

        super().__init__(
            content=self.layout_principal,
            expand=True,
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(left=20, right=20, top=15, bottom=15)
        )

        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_changement_langue)

        # 🆕 04/09/2026 : filet de sécurité robuste, pas un pari sur un
        # délai fixe. app_layout.py appelle désormais
        # actualiser_donnees_affichage() juste après le montage, ce qui
        # suffit sur PC (Python et le client sont dans le même souffle).
        # Sur Android, serious_python et le moteur Flutter communiquent
        # par un vrai canal de message : self.update() peut rendre la main
        # avant que le montage ne soit réellement confirmé côté client.
        # Ce filet vérifie donc activement, par petits intervalles, plutôt
        # que de deviner une durée unique, et se désactive dès que le
        # premier rendu (par n'importe quel chemin) a réussi.
        self._premier_rendu_effectue = False

        async def assurer_montage_puis_rendre(*args):
            import asyncio
            for _ in range(40):  # jusqu'à ~2s, par pas de 50ms
                if self._premier_rendu_effectue:
                    return  # le chemin principal (app_layout.py) a déjà réussi
                try:
                    if self.page:
                        self.actualiser_donnees_affichage()
                        return
                except RuntimeError:
                    pass
                await asyncio.sleep(0.05)
            if not self._premier_rendu_effectue:
                print("[ONBOARDING] Montage non confirmé après 2s — rendu forcé quand même")
                try:
                    self.actualiser_donnees_affichage()
                except Exception as exc:
                    print(f"[ONBOARDING] Échec rendu forcé : {exc}")

        if self.page_flet:
            self.page_flet.run_task(assurer_montage_puis_rendre)
            self.page_flet.run_task(self._boucle_badge_kaaba)
            self.page_flet.run_task(self._boucle_bandeau_versets)

    async def _boucle_badge_kaaba(self):
        """Rafraîchit le compte à rebours toutes les 30s — pas besoin
        d'une cadence plus fine, la précision à la minute suffit ici."""
        while self._boucles_vivantes_actives:
            if getattr(self.app, "ecran_courant", None) != "ONBOARDING":
                break
            try:
                self._rafraichir_badge_kaaba()
            except Exception:
                break
            await asyncio.sleep(30)

    async def _boucle_bandeau_versets(self):
        """Fondu sortant, changement de texte, fondu entrant — toutes les
        9 secondes. S'arrête d'elle-même en quittant l'onboarding, comme
        l'horloge de page_priere.py (même raison : ce routeur n'a pas de
        crochet de démontage explicite)."""
        while self._boucles_vivantes_actives:
            if getattr(self.app, "ecran_courant", None) != "ONBOARDING":
                break
            await asyncio.sleep(9)
            if getattr(self.app, "ecran_courant", None) != "ONBOARDING":
                break
            try:
                self.bandeau_versets.opacity = 0
                self.bandeau_versets.update()
                await asyncio.sleep(0.4)
                self._basculer_verset()
                self.bandeau_versets.opacity = 1
                self.bandeau_versets.update()
            except Exception:
                break

    def action_changement_langue(self, nuevo_dic: dict):
        # 🔧 17/09/2026 : le bandeau verset/hadith et le badge Kaaba ne se
        # reconstruisent pas eux-mêmes dans actualiser_contexte() (ce sont
        # des widgets créés une seule fois dans __init__, pas reconstruits
        # à chaque rendu comme le reste du tableau de bord) — sans ces deux
        # appels, ils restaient dans l'ancienne langue jusqu'au prochain
        # basculement périodique de la boucle async.
        try:
            self._basculer_verset()
            self.bandeau_versets.update()
        except Exception:
            pass
        try:
            self._rafraichir_badge_kaaba()
        except Exception:
            pass
        self.actualiser_contexte()

    # ═══════════════════════════════════════════════════════════════════════
    # UNIQUE méthode actualiser_contexte — protégée + secours
    # ═══════════════════════════════════════════════════════════════════════
    def actualiser_contexte(self):
        try:
            if getattr(self.app, "est_mode_connecte", False):
                self.rendre_tableau_de_bord_connecte()
            else:
                self.rendre_page_vitrine_visiteur()
        except Exception as exc:
            print(f"[ONBOARDING] Erreur actualiser_contexte : {exc}")
            self._rendre_vitrine_minimale_secours()

    def _rendre_vitrine_minimale_secours(self):
        """Affiche une vitrine minimale si le rendu principal échoue."""
        self.layout_principal.controls.clear()
        self.layout_principal.controls.append(
            ft.Text("HAYAATI", size=24, weight=ft.FontWeight.BOLD, color="#064e3b", text_align=ft.TextAlign.CENTER)
        )
        self.layout_principal.controls.append(
            ft.Text("Chargement...", size=12, color="#4b5563", text_align=ft.TextAlign.CENTER)
        )
        try:
            self.update()
        except Exception:
            pass

    def rendre_tableau_de_bord_connecte(self):
        from datetime import timedelta
        u_id = self.app.user_id_connecte
        dev = getattr(self.app, "devise_active", "XOF")
        fiqh = getattr(self.app, "madhhab_actif", "Malikite")

        txt_onb = DICTIONNAIRE_LANGUES.actif.get("onboarding", {})
        txt_zk = DICTIONNAIRE_LANGUES.actif.get("zakat", {})

        c_fin = self.app.sync_engine.charger_donnees_module(u_id, "FINANCES") or {}
        c_arb = self.app.sync_engine.charger_donnees_module(u_id, "PROFIL") or {}
        c_pref = self.app.sync_engine.charger_donnees_module(u_id, "PREFERENCES") or {}

        maintenant = datetime.now()
        heure_fadjr_str = "05:00"
        if hasattr(self.app, "horaires_prieres_aujourdhui") and self.app.horaires_prieres_aujourdhui:
            heure_fadjr_str = self.app.horaires_prieres_aujourdhui.get("Fajr", "05:00")

        try:
            h_f, m_f = map(int, heure_fadjr_str.split(":"))
            limite_bascule_sharia = h_f - 1
        except Exception:
            limite_bascule_sharia = 4

        if maintenant.hour < limite_bascule_sharia:
            date_veille = (maintenant - timedelta(days=1)).strftime("%Y-%m-%d")
            if hasattr(self.app.sync_engine, "charger_donnees_module_par_date"):
                c_sp = self.app.sync_engine.charger_donnees_module_par_date(u_id, "MOUHASABAH", date_veille) or {}
            else:
                c_sp = self.app.sync_engine.charger_donnees_module(u_id, "MOUHASABAH") or {}
        else:
            c_sp = self.app.sync_engine.charger_donnees_module(u_id, "MOUHASABAH") or {}

        ajust_hegiri = int(c_pref.get("ajustement_hegiri", 0))
        net = float(c_fin.get("net", 0.0))
        score = c_sp.get("score_spirituel", 0)

        nom_c = f"{c_arb.get('prenom', '')} {c_arb.get('nom', '')}".strip()
        if not nom_c or nom_c == "- -":
            nom_c = self.app.nom_utilisateur_connecte

        self.lbl_bienvenue.value = str(txt_onb.get("bienvenue", "Assalâmou Alaykoum, {} 🌟")).format(nom_c.upper())
        fiqh_traduit = DICTIONNAIRE_LANGUES.actif.get("barre_outils", {}).get("ecoles", {}).get(fiqh, fiqh)
        self.lbl_sous_titre.value = str(txt_onb.get("sous_titre", "Rapport de vigilance doctrinale — École {}")).format(str(fiqh_traduit).upper())

        txt_mouh_local = DICTIONNAIRE_LANGUES.actif.get("mouhasabah", {})
        libelle_traduit_net = str(txt_mouh_local.get("cadre_obligations", "Prières Échues")).replace(":", "").strip()
        self.lbl_titre_prieres.value = f"🕋 {libelle_traduit_net}"

        # EXTRACTS DES COURS ET DE L'ARBITRAGE DYNAMIQUE DU NISAB HAYAATI
        cours_or_db = float(c_fin.get("or_cours", 45000.0))
        cours_argent_db = float(c_fin.get("argent_cours", 650.0))

        nisab_or_calcul_sec = 85.0 * cours_or_db
        nisab_argent_calcul_sec = 595.0 * cours_argent_db

        cache_pref = getattr(self.app, "sync_engine").charger_donnees_module(u_id, "PREFERENCES") or {} if getattr(self.app, "sync_engine", None) and u_id else {}
        arbitrage_pref = str(cache_pref.get("arbitrage_nisab", "PLUS_BAS")).upper()

        if arbitrage_pref == "OR":
            nisab_reference_dynamique = nisab_or_calcul_sec
        elif arbitrage_pref == "ARGENT":
            nisab_reference_dynamique = nisab_argent_calcul_sec
        else:
            nisab_reference_dynamique = min(nisab_or_calcul_sec, nisab_argent_calcul_sec)

        if net >= nisab_reference_dynamique:
            statut_zakat_traduit = txt_zk.get('statut_eligible', '🔴 IMPOSABLE')
            couleur_statut_zakat = "#b91c1c"
        else:
            statut_zakat_traduit = txt_zk.get('statut_non_eligible', '🟢 EXEMPTÉ')
            couleur_statut_zakat = "#166534"

        # 🆕 12/09/2026 : formatter(v) reçoit soit la valeur numérique en
        # cours d'incrémentation (pendant l'animation), soit None pour les
        # métriques non numériques (Statut Zakat), qui ne font qu'un fondu
        # d'entrée sans compter quoi que ce soit.
        metrics_data = [
            (txt_onb.get("titre_fortune", "Fortune Nette"), "#f0fdf4", "#166534",
             net, lambda v, d=dev: f"{v:.2f} {d}"),
            (txt_onb.get("titre_zakat", "Statut Zakat"), "#fffbeb", couleur_statut_zakat,
             None, lambda v, s=statut_zakat_traduit: s),
            (txt_onb.get("titre_mouhasabah", "Indice Spirituel"), "#f0f9ff", "#0369a1",
             score, lambda v: f"{round(v)}%"),
        ]

        self.grille_metrics.controls.clear()
        for idx, (titre, bg_c, fg_c, valeur_cible, formatter) in enumerate(metrics_data):
            lbl_valeur = ft.Text(value="", size=14, color=fg_c, weight=ft.FontWeight.BOLD)
            carte = ft.Container(
                content=ft.Column([
                    ft.Text(value=str(titre).strip(), size=11, color="#4b5563", weight=ft.FontWeight.W_500),
                    lbl_valeur,
                ], spacing=4, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=bg_c,
                padding=ft.Padding(10, 12, 10, 12),
                border_radius=8,
                alignment=ft.Alignment(0, 0),
                col={"xs": 12, "md": 4},
                # Entrée en fondu + léger glissement vers le haut, décalée
                # par carte (voir _animer_entree_carte) plutôt qu'un
                # affichage brut instantané.
                opacity=0,
                offset=ft.Offset(0, 0.15),
                animate_opacity=300,
                animate_offset=300,
            )
            self.grille_metrics.controls.append(carte)
            if self.page_flet:
                self.page_flet.run_task(
                    self._animer_entree_carte, carte, lbl_valeur, valeur_cible, formatter, idx * 0.12
                )
            else:
                lbl_valeur.value = formatter(valeur_cible if valeur_cible is not None else 0)
                carte.opacity = 1
                carte.offset = ft.Offset(0, 0)

        # Reconstruction atomique du layout connecté
        self.layout_principal.controls.clear()
        self.layout_principal.controls.extend([
            self.lbl_bienvenue,
            self.lbl_sous_titre,
            ft.Container(height=8),
            self.bandeau_versets,
            ft.Container(height=8),
            self.grille_metrics,
            ft.Container(height=8),
            ft.Container(content=self.badge_kaaba, alignment=ft.Alignment.CENTER),
            ft.Container(height=5),
            self.cadre_prieres,
        ])
        self.layout_principal.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        try:
            self._rafraichir_badge_kaaba()
        except Exception:
            pass

        self.poursuivre_construction_alertes(c_fin, c_sp, net, dev, fiqh, u_id, ajust_hegiri, txt_onb)

    async def _animer_entree_carte(self, carte: ft.Container, lbl_valeur: ft.Text, valeur_cible, formatter, delai: float):
        """Fondu + glissement d'entrée, puis incrémentation du chiffre de
        0 jusqu'à la valeur cible si celle-ci est numérique (None = juste
        le fondu, pour les métriques textuelles comme le Statut Zakat)."""
        await asyncio.sleep(delai)
        try:
            carte.opacity = 1
            carte.offset = ft.Offset(0, 0)
            carte.update()
        except Exception:
            return

        if valeur_cible is None:
            try:
                lbl_valeur.value = formatter(None)
                lbl_valeur.update()
            except Exception:
                pass
            return

        etapes = 14
        for i in range(1, etapes + 1):
            try:
                lbl_valeur.value = formatter(valeur_cible * i / etapes)
                lbl_valeur.update()
            except Exception:
                return
            await asyncio.sleep(0.035)

    def poursuivre_construction_alertes(self, c_fin: dict, c_sp: dict, net: float, dev: str, fiqh: str, u_id: str, ajust_hegiri: int, txt_onb: dict):
        from gui.pages.page_onboarding_alerts import compiler_alertes_espace_prive, compiler_et_dessiner_les_3_carrousels

        # ⚠️ 08/09/2026 : compiler_alertes_espace_prive() renvoie désormais
        # un 5ᵉ élément, etat_alerte ("manquee" / "imminente" / "ok"),
        # explicite. L'ancienne condition cherchait les mots "⚠️" ou
        # "VIGILANCE" dans le texte lui-même : fragile, et surtout cassée
        # dès l'ajout du nouvel état "imminente", dont le texte par défaut
        # ne contient aucun des deux mots-clés — le bandeau serait resté
        # invisible même en cas d'alerte réelle.
        txt_pr, txt_cal_complet, bg_c, fg_c, etat_alerte = compiler_alertes_espace_prive(
            c_fin, c_sp, net, dev, fiqh,
            user_id=u_id,
            ajustement_lune=ajust_hegiri,
            page_flet=self.page_flet,
            scheduler=getattr(self.app, "notification_scheduler", None),
        )

        self.c_prieres.controls.clear()
        if etat_alerte in ("manquee", "imminente"):
            self.cadre_prieres.visible = True
            # 🆕 08/09/2026 : bg_c était calculé par compiler_alertes_espace_prive
            # mais jamais appliqué ici — le cadre restait blanc à bordure
            # rouge fixe quel que soit l'état. Désormais le fond et la
            # bordure suivent la couleur de l'état (rouge = manquée,
            # ambre = imminente), pour que la distinction se voie vraiment.
            self.cadre_prieres.bgcolor = bg_c
            self.cadre_prieres.border = ft.Border.all(1, fg_c)
            self.c_prieres.controls.append(
                ft.Text(value=str(txt_pr).strip(), size=12, weight=ft.FontWeight.W_500, color=fg_c)
            )
        else:
            self.cadre_prieres.visible = False

        # 🆕 11/09/2026 : la grille calendrier Hégirien/Grégorien est
        # reconstruite à chaque rafraîchissement (comme les 3 carrousels
        # juste après), pas supprimée. L'ancien code retirait purement et
        # simplement cadre_calendrier s'il existait — c'était le bon
        # réflexe tant que rien ne le reconstruisait, mais maintenant
        # qu'on a un vrai contenu à afficher, il faut le regénérer et le
        # replacer, pas juste le nettoyer.
        ajust_hegiri_int = int(ajust_hegiri) if ajust_hegiri is not None else 0
        nouvelle_grille = construire_grille_calendrier(ajustement_lune=ajust_hegiri_int)
        conteneur_calendrier = ft.Container(content=nouvelle_grille, alignment=ft.Alignment.CENTER, padding=ft.Padding(0, 5, 0, 5))
        print(f"[ONBOARDING][DIAG] Grille calendrier construite : {nouvelle_grille is not None}")

        if hasattr(self, "cadre_calendrier") and self.cadre_calendrier in self.layout_principal.controls:
            idx = self.layout_principal.controls.index(self.cadre_calendrier)
            self.layout_principal.controls[idx] = conteneur_calendrier
            print(f"[ONBOARDING][DIAG] Calendrier remplacé à l'index {idx}")
        else:
            self.layout_principal.controls.append(conteneur_calendrier)
            print(f"[ONBOARDING][DIAG] Calendrier ajouté, layout_principal.controls compte maintenant {len(self.layout_principal.controls)} éléments")
        self.cadre_calendrier = conteneur_calendrier

        compiler_et_dessiner_les_3_carrousels(self, txt_cal_complet, txt_onb)

        try:
            _ = self.page
            self.update()
            print("[ONBOARDING][DIAG] self.update() exécuté sans exception")
        except RuntimeError as exc:
            print(f"[ONBOARDING][DIAG] self.update() a échoué (page pas encore montée ?) : {exc}")

    def rendre_page_vitrine_visiteur(self):
        txt_auth = DICTIONNAIRE_LANGUES.actif.get("auth", {})
        txt_onb = DICTIONNAIRE_LANGUES.actif.get("onboarding", {})

        self.grille_metrics.controls.clear()
        self.cadre_prieres.visible = False
        if hasattr(self, "cadre_calendrier"):
            self.cadre_calendrier.visible = False

        btn_login = ft.ElevatedButton(
            content=ft.Text(str(txt_auth.get("deja_compte", "Se connecter")), size=12, weight=ft.FontWeight.BOLD),
            bgcolor="#064e3b", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.app.basculer_ecran("CONNEXION")
        )

        btn_register = ft.ElevatedButton(
            content=ft.Text(str(txt_auth.get("pas_compte", "S'inscrire")), size=12, weight=ft.FontWeight.BOLD),
            bgcolor="#0f766e", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.app.basculer_ecran("INSCRIPTION")
        )

        logo_vitrine_hayaati = ft.Image(
            src="images/Logo-Hayaati.svg",
            width=220,
            height=220,
            fit="contain"
        )

        boite_vitrine = ft.Container(
            content=ft.Column([
                logo_vitrine_hayaati,
                ft.Container(height=4),
                ft.Text(value=str(txt_onb.get("guide_visiteur_humain", "Mode Simulation Tiers actif.")), size=12, color="#374151", text_align=ft.TextAlign.CENTER),
                ft.Container(height=10),
                ft.Row([btn_login, btn_register], spacing=12, alignment=ft.MainAxisAlignment.CENTER, wrap=True)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8, tight=True),
            bgcolor=ft.Colors.WHITE,
            padding=30,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.GREY_200),
            width=440
        )

        # Reconstruction atomique du layout visiteur
        self.layout_principal.controls.clear()
        self.layout_principal.controls.append(
            ft.Container(content=boite_vitrine, expand=True, alignment=ft.Alignment(0, 0))
        )

        try:
            _ = self.page
            self.update()
        except RuntimeError:
            pass

    def actualiser_donnees_affichage(self):
        """
        Point d'entrée unique pour le rafraîchissement.
        Délegue entièrement à actualiser_contexte().
        Appelé par app_layout.py juste après le montage réel de l'écran
        (chemin principal), ou par le filet de sécurité interne si ce
        premier appel n'a pas pu s'exécuter (self.page pas encore
        confirmé sur Android). Marque _premier_rendu_effectue à True dans
        tous les cas, y compris en cas d'échec, pour ne jamais bloquer le
        filet de sécurité indéfiniment sur un problème qui se reproduirait
        à chaque tentative.
        """
        self._premier_rendu_effectue = True
        try:
            self.actualiser_contexte()
        except Exception as exc:
            print(f"[ONBOARDING] actualiser_contexte a échoué : {exc}")
            self._rendre_vitrine_minimale_secours()
