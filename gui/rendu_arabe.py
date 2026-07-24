"""
UTILITAIRE DE RENDU MIXTE ARABE/FRANÇAIS (GUI/RENDU_ARABE.PY)
Version 1.0 - Un texte explicatif mélange souvent des mots ou expressions
arabes au milieu de phrases françaises (ex: "le مبتدأ est toujours...").
Un Label Tkinter ne peut pas mélanger deux tailles de police dans une même
étendue de texte ; ce module construit un widget Text avec des tags pour
que les segments arabes détectés ressortent nettement plus grands, sans
toucher au français environnant.
"""
import re
import tkinter as tk

# Couvre l'arabe de base, les présentations arabes, et les diacritiques (harakat),
# pour qu'un mot vocalisé (ex: "الْحَمْدُ") soit reconnu comme un seul segment.
_PATTERN_ARABE = re.compile(
    r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]'
    r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF\s]*'
    r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]|'
    r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]'
)


def construire_texte_mixte(parent, contenu, bg, couleur_texte, taille_normale=11,
                            taille_arabe=17, hauteur_min=1, hauteur_max=40, wraplength=None,
                            padx=0, pady=(0, 10)):
    """Construit et empaquette (fill='x') un widget Text en lecture seule où les
    segments arabes détectés dans `contenu` s'affichent nettement plus grands que
    le reste. Retourne le widget ; sa hauteur s'auto-ajuste après le premier rendu."""
    widget = tk.Text(
        parent, wrap=tk.WORD, bg=bg, fg=couleur_texte, bd=0, highlightthickness=0,
        height=hauteur_min, padx=0, pady=0, spacing3=4, cursor="arrow"
    )
    widget.tag_configure("normal", font=("Helvetica", taille_normale), foreground=couleur_texte)
    widget.tag_configure("arabe", font=("Helvetica", taille_arabe, "bold"), foreground=couleur_texte)

    position = 0
    for match in _PATTERN_ARABE.finditer(contenu):
        debut, fin = match.span()
        if debut > position:
            widget.insert("end", contenu[position:debut], "normal")
        widget.insert("end", match.group(), "arabe")
        position = fin
    if position < len(contenu):
        widget.insert("end", contenu[position:], "normal")

    widget.config(state=tk.DISABLED)
    widget.pack(fill="x", expand=True, padx=padx, pady=pady)

    def ajuster():
        if not widget.winfo_exists():
            return
        widget.update_idletasks()
        try:
            nb_lignes = int(widget.index("end-1c").split(".")[0])
            widget.config(height=min(max(nb_lignes, hauteur_min), hauteur_max))
        except tk.TclError:
            pass

    widget.after(1, ajuster)
    return widget
