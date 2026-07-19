"""
LIVRE DE COMPTES SPIRITUEL (GUI/INTERFACE_MOUHASABAH.PY)
Version 6.3 - Initialisation, Planification Astro-Temporelle et RAZ.
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import sqlite3
from gui.langues import DICTIONNAIRE_LANGUES
from core.agenda_engine import AgendaEngine
from core.time_engine import gregorien_vers_hegiri

class EcranMouhasabah(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg="#ffffff")
        self.app = app_reference
        self.mode_mobile = None
        self.moteur_agenda = AgendaEngine()
        self.vars_jeune_dynamique = {} 
        self.mois_simulation_test = None
        
        DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_langue)
        self.prieres = ["fajr", "dhouhr", "asr", "maghrib", "isha"]
        self.construire_interface()
        
        # 🎯 PROGRAMMATION DE LA REMISE À ZÉRO AUTOMATIQUE QUOTIDIENNE (1h avant Fadjr)
        self.planifier_reinitialisation_mouhasabah()

    def planifier_reinitialisation_mouhasabah(self):
        """Calcule l'instant cible 1h avant Fadjr et l'arme dans Tkinter."""
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

        delai_ms = int((instant_raz_cible - maintenant).total_seconds() * 1000)
        self.after(delai_ms, self.executer_remise_a_zero_quotidienne)

    def executer_remise_a_zero_quotidienne(self):
        """Purge de l'IHM et de la base de données avec blindage exclusif du Hadj."""
        u_id = getattr(self.app, "user_id_connecte", None)

        # 1. Réinitialisation des cases à cocher à l'écran
        for p in self.prieres:
            if p in self.vars_p: self.vars_p[p].set(0)

        if hasattr(self, "var_nawafil"): self.var_nawafil.set(0)
        if hasattr(self, "var_sadaqah"): self.var_sadaqah.set(0)
        # 🎯 EXCEPTION DE LA SHARIA : self.var_hadj n'est pas modifiée, elle reste cochée à vie.

        for v_jeune in self.vars_jeune_dynamique.values(): v_jeune.set(0)

        # 2. Nettoyage de la table SQLite (hadj est volontairement omis de l'UPDATE)
        if u_id:
            try:
                conn = sqlite3.connect("core/hayaati_private.db")
                cur = conn.cursor()
                cur.execute("""
                    UPDATE suivi_mouhasabah 
                    SET fajr = 0, dhouhr = 0, asr = 0, maghrib = 0, isha = 0, 
                        nawafil = 0, sadaqah = 0, jeune_dynamique = 0
                    WHERE user_id = ?
                """, (str(u_id),))
                conn.commit()
                conn.close()
            except Exception: pass

        if hasattr(self, "actualiser_donnees_affichage"):
            try: self.actualiser_donnees_affichage()
            except Exception: pass

        # 🔄 Re-planification automatique en boucle pour le lendemain
        self.planifier_reinitialisation_mouhasabah()

    def construire_interface(self):
        # 📂 BLOC 1 : FORMULAIRE STANDARD (PRIÈRES & ACTIONS)
        self.cadre_form = tk.LabelFrame(self, font=("Helvetica", 9, "bold"), fg="#064e3b", bg="#ffffff", padx=5, pady=2)
        self.cadre_form.pack(fill="x", padx=10, pady=2)

        self.lbl_prieres = tk.Label(self.cadre_form, bg="#ffffff", font=("Helvetica", 8, "bold"))
        self.vars_p, self.chks_p = {}, {}
        for p in self.prieres:
            self.vars_p[p] = tk.IntVar()
            self.chks_p[p] = tk.Checkbutton(self.cadre_form, variable=self.vars_p[p], bg="#ffffff", activebackground="#ffffff")

        self.lbl_merite = tk.Label(self.cadre_form, bg="#ffffff", font=("Helvetica", 8, "bold"))
        self.var_nawafil, self.var_sadaqah, self.var_hadj = tk.IntVar(), tk.IntVar(), tk.IntVar()
        self.chk_nawafil = tk.Checkbutton(self.cadre_form, variable=self.var_nawafil, bg="#ffffff", activebackground="#ffffff")
        self.chk_sadaqah = tk.Checkbutton(self.cadre_form, variable=self.var_sadaqah, bg="#ffffff", activebackground="#ffffff")
        self.chk_hadj = tk.Checkbutton(self.cadre_form, variable=self.var_hadj, font=("Helvetica", 8, "bold"), fg="#0f766e", bg="#ffffff", activebackground="#ffffff")

        # 🎯 BLOC 2 : LE CADRE CONTEXTUEL LUNAIRE MAGIQUE (PRÊT À ACCUEILLIR L'ANIMATION)
        self.cadre_lunaire_dynamique = tk.LabelFrame(self, font=("Helvetica", 9, "bold"), fg="#d97706", bg="#fdfbf7", padx=10, pady=4)

        self.btn_sauver = tk.Button(self, font=("Helvetica", 9, "bold"), bg="#064e3b", fg="white", command=self.sauvegarder)
        self.btn_sauver.pack(fill="x", padx=10, pady=2)

        # 📂 BLOC 3 : CONFINEMENT DE L'HISTORIQUE
        self.cadre_res = tk.LabelFrame(self, font=("Helvetica", 9, "bold"), fg="#064e3b", bg="#ffffff", padx=5)
        self.cadre_res.pack(fill="x", expand=False, padx=10, pady=2)
        
        self.text_hist = tk.Text(self.cadre_res, wrap=tk.WORD, font=("Arial", 9), bg="#f9fafb", bd=1, height=2)
        self.text_hist.pack(fill="x", expand=False)

        # Bandeau de statut inférieur muni d'un double-clic secret pour tester les mois sacrés
        self.lbl_status = tk.Label(self, text="", font=("Helvetica", 9, "italic"), bg="#f3f4f6", fg="#4b5563", height=2, cursor="hand2")
        self.lbl_status.pack(fill="x", side="bottom")
        self.lbl_status.bind("<Button-1>", self.basculer_mode_simulation_demonstration)

        self.bind("<Configure>", lambda e: self.ordonner_layout(self.winfo_width() < 500))
        self.traduire_page(getattr(self.app, "langue_active", DICTIONNAIRE_LANGUES.actif))

    def basculer_mode_simulation_demonstration(self, event):
        """Permet de faire défiler manuellement les mois sacrés en cliquant sur le statut pour tester l'IHM."""
        if self.mois_simulation_test is None: self.mois_simulation_test = 9
        elif self.mois_simulation_test == 9: self.mois_simulation_test = 1
        elif self.mois_simulation_test == 1: self.mois_simulation_test = 12
        else: self.mois_simulation_test = None
        self.actualiser_donnees_affichage()

    def ordonner_layout(self, is_mobile):
        if is_mobile == self.mode_mobile: return
        self.mode_mobile = is_mobile
        for w in [self.lbl_prieres, self.lbl_merite, self.chk_nawafil, self.chk_sadaqah, self.chk_hadj] + list(self.chks_p.values()): w.grid_forget()

        if is_mobile:
            self.lbl_prieres.grid(row=0, column=0, sticky="w")
            for i, p in enumerate(self.prieres): self.chks_p[p].grid(row=i+1, column=0, sticky="w")
            self.lbl_merite.grid(row=6, column=0, sticky="w", pady=(4,0))
            self.chk_nawafil.grid(row=7, column=0, sticky="w")
            self.chk_sadaqah.grid(row=8, column=0, sticky="w")
            self.chk_hadj.grid(row=9, column=0, sticky="w", pady=2)
        else:
            self.lbl_prieres.grid(row=0, column=0, columnspan=5, sticky="w")
            for i, p in enumerate(self.prieres): self.chks_p[p].grid(row=1, column=i, sticky="w", padx=2)
            self.lbl_merite.grid(row=2, column=0, columnspan=5, sticky="w", pady=(4,0))
            self.chk_nawafil.grid(row=3, column=0, columnspan=2, sticky="w")
            self.chk_sadaqah.grid(row=3, column=2, columnspan=3, sticky="w")
            self.chk_hadj.grid(row=4, column=0, columnspan=5, sticky="w", pady=2)

    def animer_terrain_de_jeu_lunaire(self, mois_h, jour_h):
        """Anime et injecte des contrôles spécifiques selon le mois du calendrier islamique."""
        for w in self.cadre_lunaire_dynamique.winfo_children(): w.destroy()
        self.vars_jeune_dynamique.clear()
        self.cadre_lunaire_dynamique.pack_forget()
        
        langue_act = getattr(self.app, "langue_active", DICTIONNAIRE_LANGUES.actif)
        ev = langue_act.get("evenements_islamiques", {})
        onb = langue_act.get("onboarding", {})

        # 🌙 CAS 1 : MOIS DE RAMADAN (Mois 9)
        if mois_h == 9:
            nom_m = onb.get("mois_nom_9", "Ramadan")
            self.cadre_lunaire_dynamique.config(text=f"🌙 {nom_m} : {ev.get('evt_ramadan', '')[:40]}")
            self.cadre_lunaire_dynamique.pack(fill="x", padx=10, pady=3, after=self.cadre_form)
            self.vars_jeune_dynamique["ramadan_jeune"] = tk.IntVar()
            chk = tk.Checkbutton(self.cadre_lunaire_dynamique, text=f"{nom_m} ({jour_h})", variable=self.vars_jeune_dynamique["ramadan_jeune"], bg="#fdfbf7", activebackground="#fdfbf7", font=("Helvetica", 9, "bold"), fg="#064e3b")
            chk.pack(anchor="w", pady=4)

        # 🌙 CAS 2 : MOIS DE MUHARRAM (Mois 1)
        elif mois_h == 1:
            nom_m = onb.get("mois_nom_1", "Muharram")
            self.cadre_lunaire_dynamique.config(text=f"📿 {nom_m} : {ev.get('evt_achoura', '')[:40]}")
            self.cadre_lunaire_dynamique.pack(fill="x", padx=10, pady=3, after=self.cadre_form)
            self.vars_jeune_dynamique["achoura_9"] = tk.IntVar()
            self.vars_jeune_dynamique["achoura_10"] = tk.IntVar()
            tk.Checkbutton(self.cadre_lunaire_dynamique, text="9 (Tassou'a)", variable=self.vars_jeune_dynamique["achoura_9"], bg="#fdfbf7").pack(anchor="w")
            tk.Checkbutton(self.cadre_lunaire_dynamique, text="10 (Achoura)", variable=self.vars_jeune_dynamique["achoura_10"], bg="#fdfbf7", font=("Helvetica", 9, "bold"), fg="#0f766e").pack(anchor="w", pady=2)

        # 🌙 CAS 3 : MOIS DE DHU AL-HIJJAH (Mois 12) -> Suivi des 9 premiers jours & Arafat
        elif mois_h == 12:
            nom_m = onb.get("mois_nom_12", "Dhu al-Hijjah")
            self.cadre_lunaire_dynamique.config(text=f"🌟 {nom_m} : {ev.get('evt_arafa', '')[:40]}")
            self.cadre_lunaire_dynamique.pack(fill="x", padx=10, pady=3, after=self.cadre_form)
            self.vars_jeune_dynamique["neuf_jours"] = tk.IntVar()
            self.vars_jeune_dynamique["arafat"] = tk.IntVar()
            
            tk.Checkbutton(self.cadre_lunaire_dynamique, text=f"{nom_m} ({jour_h})", variable=self.vars_jeune_dynamique["neuf_jours"], bg="#fdfbf7").pack(anchor="w")
            if jour_h == 9 or self.mois_simulation_test is not None:
                chk_a = tk.Checkbutton(self.cadre_lunaire_dynamique, text=ev.get("evt_arafa", "Arafat"), variable=self.vars_jeune_dynamique["arafat"], bg="#fdfbf7", font=("Helvetica", 9, "bold"), fg="#b91c1c")
                chk_a.pack(anchor="w", pady=4)

    def action_langue(self, dic):
        if self.winfo_exists(): self.traduire_page(dic)

    def traduire_page(self, dic):
        """Met à jour les textes de l'écran en lisant uniquement les clés i18n dynamiques du JSON."""
        m = dic.get("mouhasabah", {})
        menu_json = dic.get("menu", {})
        
        # Configuration des titres de cadres de manière réactive
        self.cadre_form.config(text=menu_json.get("mouhasabah", "Mouhasabah"))
        self.lbl_prieres.config(text=m.get("cadre_obligations", "Prières :"))
        self.lbl_merite.config(text=menu_json.get("profil", "Actions :"))
        
        # 1. Traduction immédiate des intitulés individuels de coche des 5 prières
        prieres_json = m.get("prieres", {})
        for p in self.prieres:
            self.chks_p[p].config(text=prieres_json.get(p, p.capitalize()))

        # 2. 🎯 SÉCURITÉ I18N UNIVERSELLE : Lecture directe des clés courtes du dictionnaire actif
        lbl_nawafil = m.get("lbl_nawafil_court", "Nawafil")
        lbl_sadaqah = m.get("lbl_sadaqah_court", "Sadaqah")
        lbl_hadj = m.get("lbl_hadj_court", "Hadj")

        # Injection propre sans aucune manipulation de chaîne ou découpage risqué
        self.chk_nawafil.config(text=f"✅ {lbl_nawafil}")
        self.chk_sadaqah.config(text=f"✨ {lbl_sadaqah}")
        self.chk_hadj.config(text=f"🕋 {lbl_hadj}")
        
        self.btn_sauver.config(text=m.get("btn_valider_journee", "Enregistrer la journée"))
        self.cadre_res.config(text=dic.get("audit", {}).get("titre_graphique_evolution", "Historique"))

    def sauvegarder(self):
        if not getattr(self.app, "est_mode_connecte", False): return
        try:
            nb = sum(self.vars_p[p].get() for p in self.prieres)
            bonus_lunaire = sum(v.get() * 15 for v in self.vars_jeune_dynamique.values())
            score = (nb * 15) + (self.var_nawafil.get() * 12) + (self.var_sadaqah.get() * 13) + bonus_lunaire
            if score > 100: score = 100
            
            self.text_hist.insert("1.0", f"📿 [{datetime.now().strftime('%d/%m/%Y %H:%M')}] - Score: {score}%\n")
            if getattr(self.app, "sync_engine", None):
                donnees = {p: self.vars_p[p].get() for p in self.prieres}
                donnees.update({
                    "score_spirituel": score, 
                    "nawafil": self.var_nawafil.get(), 
                    "sadaqah": self.var_sadaqah.get(), 
                    "deja_fait_hadj": self.var_hadj.get(), 
                    "historique": self.text_hist.get("1.0", tk.END)
                })
                for k, v in self.vars_jeune_dynamique.items(): donnees[k] = v.get()
                self.app.sync_engine.executer_sauvegarde_module(self.app.user_id_connecte, "MOUHASABAH", donnees)
            self.actualiser_donnees_affichage()
        except Exception: pass

    def injecter_donnees(self, data):
        if not data: return
        for p in self.prieres: self.vars_p[p].set(data.get(p, 0))
        self.var_nawafil.set(data.get("nawafil", 0))
        self.var_sadaqah.set(data.get("sadaqah", 0))
        
        # 🎯 SÉCURITÉ PERSISTANCE : Restauration et maintien de l'état coché à vie pour le Hadj
        self.var_hadj.set(data.get("deja_fait_hadj", 0))
        
        for k, v in self.vars_jeune_dynamique.items(): v.set(data.get(k, 0))
        self.text_hist.delete("1.0", tk.END)
        self.text_hist.insert("1.0", data.get("historique", ""))

    def actualiser_donnees_affichage(self):
        u_id = getattr(self.app, "user_id_connecte", None)
        langue_act = getattr(self.app, "langue_active", DICTIONNAIRE_LANGUES.actif)
        if getattr(self.app, "est_mode_connecte", False) and getattr(self.app, "sync_engine", None):
            c_p = self.app.sync_engine.charger_donnees_module(u_id, "PREFERENCES")
            ajust_hegiri = int(c_p.get("ajustement_hegiri", 0))
            
            maintenant = datetime.now()
            h_date = gregorien_vers_hegiri(maintenant.year, maintenant.month, maintenant.day, ajustement_fiqh=ajust_hegiri)
            
            mois_final = self.mois_simulation_test if self.mois_simulation_test is not None else h_date["mois_num"]
            jour_final = 9 if self.mois_simulation_test is not None else h_date["jour"]
            
            self.animer_terrain_de_jeu_lunaire(mois_final, jour_final)
            self.injecter_donnees(self.app.sync_engine.charger_donnees_module(u_id, "MOUHASABAH"))
        
        o_txt = langue_act.get("onboarding", {})
        manquees = self.moteur_agenda.evaluer_prieres_manquees_en_direct({p: self.vars_p[p].get() for p in self.prieres}, madhhab_actif=getattr(self.app, "madhhab_actif", "Malikite"))
        
        if self.mois_simulation_test is not None:
            self.lbl_status.config(text=f"⚙️ [{mois_final}]", bg="#fffbeb", fg="#b45309")
        elif manquees: 
            trad_manquees = [langue_act.get("mouhasabah", {}).get("prieres", {}).get(p, p.capitalize()) for p in manquees]
            self.lbl_status.config(text=o_txt.get("prieres_manquees", "⚠️ {}").format(", ".join(trad_manquees)), bg="#fffbeb", fg="#b45309")
        else: 
            self.lbl_status.config(text=o_txt.get("prieres_ok", "✨ OK"), bg="#f0fdf4", fg="#166534")

    def changer_langue(self, n_lang): 
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)
