"""
INTERFACE DIAGNOSTIC ZAKAT TIERS (GUI/COMPONENTS/INTERFACE_ZAKAT_TIERS.PY)
Version Finale Intégrale Statique - Totalement compatible Flet 0.86.2, Python 3.14 & APK Android
"""
from __future__ import annotations
import flet as ft
from gui.langues import DICTIONNAIRE_LANGUES
from gui.components.zakat_affichage import (
    MODES_IRRIGATION, libelle_ovins, libelle_bovins, libelle_irrigation, suffixe_taux,
    creer_menu_irrigation, creer_cellule_irrigation, actualiser_cours_en_ligne,
    libelle_chameaux, notes_zakat,
)
from core.financial_engine import FinancialEngine
from core.certificate_engine import generer_certificat_pdf

class EcranZakatTiers(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self.mode_mobile = None
        self.moteur_zakat = FinancialEngine()
        self.intrants_mem: dict[str, str] = {}
        self.lignes_mem: list[list[str]] = []
        self.map_nisab_trad_vers_cle: dict[str, str] = {}
        self.map_nisab_cle_vers_trad: dict[str, str] = {}
        
        # Structure de stockage d'inventaire public
        self.fortune_calculee = {"liq": 0.0, "or": 0.0, "argent": 0.0, "due": 0.0, "creances": 0.0, "dettes": 0.0}
        self.agri_calcule = {"poids": 0.0, "due": 0.0}
        self.pastoral_calcule = {"o": "0", "b": "0", "ovins": 0, "bovins": 0}

        # 🎯 ALIGNEMENT TECHNIQUE : Le "stock" commercial est maintenu de manière étanche aux cotisations
        self.cles_champs = [
            "liq", "stock", "creances", "dettes", "dettes_long_terme",
            "or_refuge_poids", "or_parure_poids", "or_cours",
            "argent_refuge_poids", "argent_parure_poids", "argent_cours",
            "poids", "ovins", "bovins", "chameaux"
        ]
        self.labels: dict[str, ft.Text] = {}
        self.entries: dict[str, ft.TextField] = {}

        # --- 1. INSTANCIATION DES COMPOSANTS GRAPHIQUES MATERIAL 3 ---
        self.lbl_nom = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#d97706")
        self.en_nom_tiers = ft.TextField(
            value="Fatoumata ", width=140, height=38, text_size=12,
            border_radius=6, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
        )
        # 04/10/2026 : le choix du nisab se fait dans Réglages (accessible en mode Visiteur comme en mode Live).
        
        self.c_nom = ft.Row([self.lbl_nom, self.en_nom_tiers], spacing=10, alignment=ft.MainAxisAlignment.START, wrap=True)

        self.lbl_cadre_f = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#d97706")
        self.grille_f = ft.ResponsiveRow(spacing=8, run_spacing=8)
        self.c_f = ft.Container(
            content=ft.Column([self.lbl_cadre_f, self.grille_f], spacing=6),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#d97706")
        )

        self.lbl_cadre_m = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#d97706")
        self.grille_m = ft.ResponsiveRow(spacing=8, run_spacing=8)
        self.c_m = ft.Container(
            content=ft.Column([self.lbl_cadre_m, self.grille_m], spacing=6),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#d97706")
        )

        self.lbl_cadre_a = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#d97706")
        self.grille_a = ft.ResponsiveRow(spacing=8, run_spacing=8)
        self.c_a = ft.Container(
            content=ft.Column([self.lbl_cadre_a, self.grille_a], spacing=6),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#d97706")
        )

        for c in self.cles_champs:
            self.labels[c] = ft.Text(size=11, weight=ft.FontWeight.W_500, color="#4b5563")
            self.entries[c] = ft.TextField(
                value="0", height=38, text_size=12,
                border_radius=6, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
            )
            setattr(self, f"en_{c}", self.entries[c])

            cellule_formulaire = ft.Container(content=ft.Column([self.labels[c], self.entries[c]], spacing=4), col={"xs": 12, "sm": 6, "md": 3})
            
            if "or" in c or "argent" in c:
                self.grille_m.controls.append(cellule_formulaire)
            elif c in ["poids", "ovins", "bovins", "chameaux"]:
                self.grille_a.controls.append(cellule_formulaire)
            else:
                self.grille_f.controls.append(cellule_formulaire)

        # 🌙 Hawl : date a laquelle le nisab a ete atteint (annee lunaire ~ 354 jours). Vide = non precisee.
        self.lbl_date_hawl = ft.Text(size=11, weight=ft.FontWeight.W_500, color="#4b5563")
        self.en_date_hawl = ft.TextField(
            value="", hint_text="AAAA-MM-JJ", height=38, text_size=12,
            border_radius=6, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
        )
        self.grille_f.controls.append(ft.Container(
            content=ft.Column([self.lbl_date_hawl, self.en_date_hawl], spacing=4), col={"xs": 12, "sm": 6, "md": 3}))

        # 🌾 03/10/2026 : mode d'irrigation (pluie 10 %, artificielle 5 %, mixte 7,5 %)
        self.lbl_irrigation = ft.Text(size=11, weight=ft.FontWeight.W_500, color="#4b5563")
        self.cb_irrigation_tiers = creer_menu_irrigation(38, 12)
        (_cell_menu,) = creer_cellule_irrigation(
            self.lbl_irrigation, self.cb_irrigation_tiers, None, {"xs": 12, "sm": 6, "md": 3})
        self.grille_a.controls.insert(1, _cell_menu)

        # 🔄 Cours de l'or et de l'argent en ligne (la saisie manuelle reste toujours possible)
        self.btn_cours = ft.OutlinedButton(content=ft.Text("🔄", size=12), on_click=lambda _: self._lancer_actualisation_cours())
        self.lbl_cours_etat = ft.Text(size=10, italic=True, color="#6b7280")
        self.grille_m.controls.append(ft.Container(
            content=ft.Column([self.btn_cours, self.lbl_cours_etat], spacing=4), col={"xs": 12}))

        # Cours de repli indicatifs en XOF uniquement : ailleurs, a saisir ou a recuperer en ligne.
        _xof = getattr(self.app, "devise_active", "XOF") == "XOF"
        self.entries["or_cours"].value = "45000" if _xof else "0"
        self.entries["argent_cours"].value = "650" if _xof else "0"

        self.btn_calculer = ft.ElevatedButton(
            content=ft.Text("Calculer", size=13, weight=ft.FontWeight.BOLD),
            bgcolor="#064e3b", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.executer_calcul_tiers()
        )

        self.btn_pdf = ft.ElevatedButton(
            content=ft.Text("Générer PDF", size=13, weight=ft.FontWeight.BOLD),
            bgcolor="#0f766e", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.imprimer_pdf_tiers()
        )

        self.lbl_cadre_res = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.text_rapport = ft.TextField(
            multiline=True, min_lines=6, max_lines=10, text_size=14, read_only=True,
            text_style=ft.TextStyle(font_family="Courier New", weight=ft.FontWeight.BOLD, color="#064e3b"),
            border_color=ft.Colors.GREY_400, bgcolor="#f9fafb", expand=True 
        )
        
        self.c_res = ft.Container(
            content=ft.Column([self.lbl_cadre_res, self.text_rapport], spacing=6),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#064e3b"), expand=True 
        )

        self.layout_tiers = ft.Column([
            self.c_nom,
            self.c_f,
            self.c_m,
            self.c_a,
            ft.Row([self.btn_calculer, self.btn_pdf], spacing=15, alignment=ft.MainAxisAlignment.START, wrap=True),
            self.c_res
        ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

        super().__init__(
            content=self.layout_tiers, expand=True, bgcolor="#f8fafc",
            padding=ft.Padding(left=15, right=15, top=15, bottom=15)
        )

        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_langue)
        self.actualiser_donnees_affichage()

    def action_langue(self, dic: dict):
        self.traduire_page(dic)

    # PARTIE 2/3

    def traduire_page_suite(self, dic: dict, zk: dict, fin: dict):
        """Met à jour les labels des métaux et du secteur agro-pastoral depuis le dictionnaire JSON."""
        self.labels["or_refuge_poids"].value = str(fin.get("lbl_or_refuge", "Or Refuge (g) :"))
        self.labels["or_parure_poids"].value = str(fin.get("lbl_or_parures", "Or Parure (g) :"))
        self.labels["or_cours"].value = str(zk.get("lbl_cours_or", "Cours Or :"))
        self.labels["argent_refuge_poids"].value = str(fin.get("lbl_argent_refuge", "Argent Refuge (g) :"))
        self.labels["argent_parure_poids"].value = str(fin.get("lbl_argent_parures", "Argent Parure (g) :"))
        self.labels["argent_cours"].value = str(zk.get("lbl_cours_argent", "Cours Argent :"))
        self.labels["poids"].value = str(fin.get("lbl_grain", "Grains (kg) :"))
        self.labels["ovins"].value = str(fin.get("lbl_moutons", "Moutons :"))
        self.labels["bovins"].value = str(fin.get("lbl_bovins", "Bovins :"))
        self.labels["chameaux"].value = str(fin.get("lbl_chameaux", "Chameaux :"))
        self.labels["dettes_long_terme"].value = str(fin.get("lbl_dettes_long_terme", "Dont dettes à long terme (> 1 an) :"))
        self.lbl_date_hawl.value = str(fin.get("lbl_date_hawl", "Date où le nisab a été atteint (AAAA-MM-JJ) :"))

        # Mode d'irrigation : libelles traduits, selection conservee
        cle_irrigation = self.cb_irrigation_tiers.value if self.cb_irrigation_tiers.value in MODES_IRRIGATION else "pluie"
        self.lbl_irrigation.value = str(fin.get("lbl_irrigation", "Irrigation des cultures :"))
        self.cb_irrigation_tiers.options.clear()
        for m in MODES_IRRIGATION:
            self.cb_irrigation_tiers.options.append(ft.dropdown.Option(key=m, text=libelle_irrigation(m, fin)))
        self.cb_irrigation_tiers.value = cle_irrigation
        self._txt_fin_tiers = fin
        if self.btn_cours.content:
            self.btn_cours.content.value = str(fin.get("btn_cours_en_ligne", "🔄 Cours en ligne"))

        # Nisab : lu dans Réglages (voir _cle_nisab_reglages)

        if self.page_flet:
            try: self.update()
            except Exception: pass

    def _cle_nisab_reglages(self):
        """Nisab choisi dans Réglages (PLUS_BAS / OR / ARGENT), valable en mode Visiteur comme en mode Live."""
        cle = str(getattr(self.app, "cle_nisab_active_memoire", "") or "").upper()
        if cle not in ("PLUS_BAS", "OR", "ARGENT"):
            try:
                u = self.app.user_id_connecte if getattr(self.app, "est_mode_connecte", False) else "INVITE"
                cp = self.app.sync_engine.charger_donnees_module(u, "PREFERENCES") or {}
                cle = str(cp.get("arbitrage_nisab", "PLUS_BAS")).upper()
            except Exception:
                cle = "PLUS_BAS"
        return cle if cle in ("PLUS_BAS", "OR", "ARGENT") else "PLUS_BAS"

    def _libelle_nisab(self, cle):
        opt = DICTIONNAIRE_LANGUES.actif.get("zakat", {}).get("options_nisab", {})
        return str({"PLUS_BAS": opt.get("nisab_plus_bas", "Baromètre Prudent"),
                    "OR": opt.get("nisab_or", "Seuil de l'Or (85g)"),
                    "ARGENT": opt.get("nisab_argent", "Seuil de l'Argent (595g)")}.get(cle, ""))

    def _lancer_actualisation_cours(self):
        """Bouton « Cours en ligne » : remplit les champs or / argent (modifiables ensuite)."""
        if self.page_flet:
            self.page_flet.run_task(self._actualiser_cours)

    async def _actualiser_cours(self):
        dev = str(getattr(self.app, "devise_active", "XOF") or "XOF")
        await actualiser_cours_en_ligne(self, self.entries["or_cours"], self.entries["argent_cours"],
                                        self.lbl_cours_etat, getattr(self, "_txt_fin_tiers", {}), dev)

    def executer_calcul_tiers(self):
        """Déclenche l'évaluation budgétaire du tiers et met à jour l'IHM de simulation."""
        try:
            dev = getattr(self.app, "devise_active", "XOF")
            doc = getattr(self.app, "madhhab_actif", "Malikite")
            
            langue_active = DICTIONNAIRE_LANGUES.actif
            txt_zk = langue_active.get("zakat", {})
            txt_fin = langue_active.get("finances", {})

            # Extraction et conversion sécurisée depuis les boîtes de texte TextField
            intrants = {c: float(self.entries[c].value.strip() or 0) for c in self.cles_champs}
            intrants["ovins"] = int(intrants["ovins"])
            intrants["bovins"] = int(intrants["bovins"])
            intrants["chameaux"] = int(intrants["chameaux"])
            intrants["date_hawl"] = self.en_date_hawl.value.strip()
            
            intrants["arbitrage_nisab"] = self._cle_nisab_reglages()
            intrants["irrigation_mode"] = self.cb_irrigation_tiers.value if self.cb_irrigation_tiers.value in MODES_IRRIGATION else "pluie"

            # Soumission à l'Engine financier d'origine (Véhicule neutre car exclu de ass_brute)
            res = self.moteur_zakat.executer_audit_zakat_complet(
                mode_persistant=False, user_id=None, madhhab_actif=doc, cours_or_terrain=intrants["or_cours"], donnees_manuelles_tiers=intrants,
                cours_par_defaut_autorises=(dev == "XOF")
            )

            self.fortune_calculee = {
                "liq": res.get("assiette_financiere_nette", 0.0),
                "or": res.get("valeur_or_retenue_zakat", 0.0),
                "argent": res.get("valeur_argent_retenue_zakat", 0.0),
                "due": res.get("zakat_monetaire_due", 0.0),
                "creances": intrants["creances"],
                "dettes": intrants["dettes"]
            }
            self.agri_calcule = {
                "poids": intrants["poids"],
                "due": res.get("zakat_agricole_due_kg", 0.0),
                "taux": res.get("taux_agricole_pct", 0.0),
                "mode": res.get("mode_irrigation", "pluie")
            }
            self.pastoral_calcule = {
                # Le moteur renvoie des codes (code_obligation_*) : ils sont traduits ici. Avant, les
                # cles lues n'existaient pas et le cheptel s'affichait toujours "0".
                "o": libelle_ovins(res, txt_zk),
                "b": libelle_bovins(res, txt_zk),
                "ovins": res.get("brut_ovins", 0),
                "bovins": res.get("brut_bovins", 0)
            }

            # 🎯 ALIGNEMENT STRICT DES VARIABLES DE POIDS MÉTALLIQUES AVEC L'ENGINE 5.5
            p_or_poids = intrants["or_refuge_poids"] if doc != "Hanafite" else (intrants["or_refuge_poids"] + intrants["or_parure_poids"])
            p_ag_poids = intrants["argent_refuge_poids"] if doc != "Hanafite" else (intrants["argent_refuge_poids"] + intrants["argent_parure_poids"])
            
            self.intrants_mem = {
                "LIQUIDE": f"{intrants['liq']:.2f} {dev}",
                "STOCK": f"{intrants['stock']:.2f} {dev}",  # 🎯 RECONNAISSANCE DU STOCK COMMERCIAL EN SECTION 1
                "OR": f"{self.fortune_calculee['or']:.2f} {dev} ({p_or_poids:.1f}g)",
                "ARGENT": f"{self.fortune_calculee['argent']:.2f} {dev} ({p_ag_poids:.1f}g)",
                "DETTES": f"-{self.fortune_calculee['dettes']:.2f} {dev}",
                "CREANCES": f"{self.fortune_calculee['creances']:.2f} {dev}",
                "AGRO": f"{self.agri_calcule['poids']:.1f} kg · {libelle_irrigation(self.agri_calcule['mode'], txt_fin)}"
            }

            b_v = txt_zk.get("statut_eligible", "🟢 ÉLIGIBLE") if res["est_imposable_monetaire"] else txt_zk.get("statut_non_eligible", "🔴 EXEMPTÉ")
            titre_traduit = txt_zk.get("rapport_titre", "RAPPORT DE ZAKAT")
            
            lbl_m_ref = res.get('metal_seuil_reference', 'OR')
            if "OR" in str(lbl_m_ref).upper():
                lbl_m_ref = txt_zk.get("options_nisab", {}).get("nisab_or", "Or")
            elif "ARGENT" in str(lbl_m_ref).upper():
                lbl_m_ref = txt_zk.get("options_nisab", {}).get("nisab_argent", "Argent")

            b_outils = langue_active.get("barre_outils", {})
            ecole_traduite = b_outils.get("ecoles", {}).get(doc, doc)

    # PARTIE 3/3

            # Remplissage du tableau de verdict vert épuré
            self.lignes_mem = [
                [f"{txt_zk.get('assiette_imposable', 'Assiette')} : {self.fortune_calculee['liq']:.2f} {dev}"],
                [f"{txt_zk.get('montant_du', 'Zakat monétaire due')} (2.5%) : {self.fortune_calculee['due']:.2f} {dev}"],
                [f"{txt_zk.get('zakat_grain', 'Zakat Agricole')} : {self.agri_calcule['due']:.2f} kg{suffixe_taux(self.agri_calcule['taux'])}"],
                [f"{txt_zk.get('zakat_moutons', 'Zakat Ovins')} : {self.pastoral_calcule['o']}"],
                [f"{txt_zk.get('zakat_bovins', 'Zakat Bovins')} : {self.pastoral_calcule['b']}"]
            ]
            
            # Format d'affichage visuel pour la zone de texte de l'écran principal
            lignes_visuelles_ecran = [
                f" 🕋 {titre_traduit} ({ecole_traduite.upper()}) :",
                f" ==================================================",
                f"   • {txt_zk.get('cadre_analyse', 'VERDICT').strip()} : {b_v}",
                f"   • {txt_zk.get('nisab_applique', 'NISAB')}   : {lbl_m_ref} ({res['nissab_monetaire_calcule']:.2f} {dev})",
                f"   • {self.lignes_mem[0][0]}",
                f"   • {self.lignes_mem[1][0]}",
                f"   • {self.lignes_mem[2][0]}",
                f"   • {self.lignes_mem[3][0]}",
                f"   • {self.lignes_mem[4][0]}",
            ]
            
            if int(res.get("brut_chameaux", 0) or 0) > 0:
                self.lignes_mem.append([f"{txt_zk.get('zakat_chameaux', 'Zakat Chameaux')} : {libelle_chameaux(res, txt_zk)}"])
                lignes_visuelles_ecran.append(f"   • {self.lignes_mem[-1][0]}")
            for _note in notes_zakat(res, txt_zk, dev):
                lignes_visuelles_ecran.append(f"   {_note}")
            if res.get("cours_manquants"):
                lignes_visuelles_ecran.insert(2, "   " + str(txt_zk.get("cours_manquants", "⚠️ Cours de l'or ou de l'argent non renseigné.")))
            elif res.get("cours_par_defaut_utilises"):
                lignes_visuelles_ecran.insert(2, "   " + str(txt_zk.get("cours_indicatifs", "ℹ️ Cours non renseignés : valeurs indicatives utilisées.")))
            self.text_rapport.value = "\n".join(lignes_visuelles_ecran)
            
        except Exception as e:
            self.text_rapport.value = f"❌ : {str(e)}"
            
        if self.page_flet:
            try: self.update()
            except Exception: pass

    def imprimer_pdf_tiers(self):
        """Génère le certificat de purification pour le tiers simulé."""
        if not self.lignes_mem: 
            return
        
        id_t = {
            "nom": self.en_nom_tiers.value.strip() or "Tiers", 
            "prenom": "", 
            "ville": "Saisie Manuelle", 
            "pays": "Diagnostic", 
            "telephone": "-"
        }
        
        nisab_choisi_texte = self._libelle_nisab(self._cle_nisab_reglages())
        
        generer_certificat_pdf(
            id_t, 
            "ZAKAT", 
            getattr(self.app, "madhhab_actif", "Malikite"), 
            getattr(self.app, "devise_active", "XOF"), 
            self.intrants_mem, 
            self.lignes_mem,
            nisab_label=nisab_choisi_texte
        )

    def traduire_page(self, dic: dict):
        """Met à jour dynamiquement tous les labels du formulaire depuis le JSON (FIX TECHNICAL SUCCESS)."""
        if not dic:
            return
        
        # 🌟 FIX CRITIQUE PYLANCE : Déclaration explicite et locale de txt_zk requis par le dictionnaire de stocks
        txt_zk = dic.get("zakat", {}) or {}
        p = dic.get("pdf", {}) or {}
        fin = dic.get("finances", {}) or {}
        
        self.lbl_cadre_f.value = str(fin.get("cadre_liquide", "Finances"))
        self.lbl_cadre_m.value = str(fin.get("cadre_metaux", "Métaux"))
        self.lbl_cadre_a.value = str(fin.get("cadre_agropastoral", "Agro-Pastoral"))
        self.lbl_nom.value = str(p.get("tableau_part", "Bénéficiaire :"))
        self.lbl_cadre_res.value = str(txt_zk.get("cadre_analyse", "Verdict"))
        
        if self.btn_calculer.content:
            self.btn_calculer.content.value = str(txt_zk.get("btn_calculer", "Calculer"))
        if self.btn_pdf.content:
            self.btn_pdf.content.value = str(txt_zk.get("btn_imprimer", "Générer PDF"))

        # 🎯 ALIGNEMENT SHARIA-COMPLIANT : Dissociation totale des véhicules personnels du calcul Zakat
        dict_labels_tiers = {
            "liq": fin.get("liq_lbl", "Disponibilités Cash / Comptes :"),
            "stock": dic.get("finances", {}).get("stock_lbl", "Stocks & Marchandises Commerciales :") if txt_zk.get("options_nisab") else "Stocks / Marchandises :",
            "creances": fin.get("creances_lbl", "Créances Actives Recouvrables :"),
            "dettes": fin.get("dettes_lbl", "Passif Exigible / Dettes :")
        }
        
        for k in ["liq", "stock", "creances", "dettes"]:
            if k in self.labels: 
                self.labels[k].value = str(dict_labels_tiers[k])

        # Renvoi vers le sous-bloc des métaux et du bétail pour finaliser le dictionnaire
        self.traduire_page_suite(dic, txt_zk, fin)

    def changer_langue(self, n_lang: str): 
        """Propagation descendante linguistique."""
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)
        
    def actualiser_donnees_affichage(self): 
        """Cycle de vie : Remet à zéro les simulations."""
        self.en_nom_tiers.value = "Fatoumata "
        for c in self.cles_champs:
            _xof = getattr(self.app, "devise_active", "XOF") == "XOF"
            self.entries[c].value = ("45000" if _xof else "0") if c == "or_cours" else ("650" if _xof else "0") if c == "argent_cours" else "0"
        self.text_rapport.value = ""
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)
        
    def actualiser_contexte(self): 
        self.actualiser_donnees_affichage()
