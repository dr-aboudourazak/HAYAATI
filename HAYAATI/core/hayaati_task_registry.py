"""
GARDE-FOU GÉNÉRIQUE CONTRE LES FUITES DE TÂCHES DE FOND
(CORE/HAYAATI_TASK_REGISTRY.PY)

Contexte : le bug corrigé le 23/09/2026 sur gui/pages/page_onboarding.py
(explosion des tâches asyncio visible en logcat : 15 → 796 → 5106 sur
l'écran ONBOARDING, à l'origine des gels/plantages après usage prolongé)
venait d'un patron répété à la main, à chaque écran, pour lancer une
boucle de fond puis l'arrêter au bon moment : un booléen partagé, jamais
garanti d'être remis à False, avec pour seul filet de sécurité que la
boucle elle-même remarque le changement d'écran à son prochain réveil —
ce qui laisse une fenêtre de course si l'utilisateur revient sur l'écran
avant ce réveil.

Ce module centralise ce patron une fois pour toutes, pour qu'aucune
future boucle d'animation/rafraîchissement/sondage n'ait à le
réinventer — et ne puisse donc pas réintroduire la même fuite par simple
oubli.

CONTRAT : toute coroutine de fond RÉCURRENTE (boucle while, pas un
traitement ponctuel) lancée via page.run_task() DOIT passer par
HayaatiTaskRegistry.lancer(), jamais directement par
page_flet.run_task(). La coroutine doit accepter un paramètre
`generation` et vérifier à CHAQUE itération, via
HayaatiTaskRegistry.generation_active(canal, generation), qu'elle est
toujours la version en cours avant de continuer.

Exemple minimal :

    async def _ma_boucle(self, generation):
        while HayaatiTaskRegistry.generation_active("mon_ecran.ma_boucle", generation):
            ... travail ...
            await asyncio.sleep(30)

    def demarrer(self):
        HayaatiTaskRegistry.lancer(self.page_flet, "mon_ecran.ma_boucle", self._ma_boucle)

    def arreter(self):
        HayaatiTaskRegistry.arreter("mon_ecran.ma_boucle")

Pourquoi un compteur de génération plutôt qu'un simple booléen : au
réveil d'un `await asyncio.sleep(...)`, la tâche annulée par
`Task.cancel()` reçoit une CancelledError au prochain point d'attente —
ce qui suffit dans l'immense majorité des cas. Le compteur de
génération est une deuxième vérification, active à chaque tour de
boucle plutôt qu'une seule fois à l'annulation : si jamais une boucle
future contient du travail synchrone long entre deux `await`, ou si un
appelant oublie d'annuler explicitement, la vérification de génération
rattrape le cas — double protection plutôt qu'un unique mécanisme dont
la défaillance ne serait détectée qu'en production.

Convention de nommage des canaux : "<ecran>.<nom_boucle>", en minuscules
(ex: "onboarding.badge_kaaba", "priere.horloge") — pour pouvoir arrêter
toutes les boucles d'un écran d'un coup avec arreter_prefixe().
"""
from __future__ import annotations
from typing import Dict, Optional


class HayaatiTaskRegistry:
    """Registre partagé au niveau classe — un seul registre pour toute
    l'application, quel que soit le module qui l'utilise."""

    _taches: Dict[str, object] = {}
    _generations: Dict[str, int] = {}

    @classmethod
    def lancer(cls, page_flet, canal: str, fonction_coroutine, *args, **kwargs):
        """Annule toute tâche déjà enregistrée sous ce canal, incrémente
        sa génération, puis relance `fonction_coroutine(generation, *args,
        **kwargs)` via page_flet.run_task(). Retourne la nouvelle Task
        (ou None si page_flet est indisponible — ex: tests hors Flet)."""
        cls.arreter(canal)
        generation = cls._generations.get(canal, 0) + 1
        cls._generations[canal] = generation

        if not page_flet:
            print(f"[HayaatiTaskRegistry] page_flet indisponible — canal '{canal}' non lancé.")
            return None

        tache = page_flet.run_task(fonction_coroutine, generation, *args, **kwargs)
        cls._taches[canal] = tache
        return tache

    @classmethod
    def arreter(cls, canal: str) -> None:
        """Annule la tâche du canal si elle existe et n'est pas déjà
        terminée, et invalide sa génération dans tous les cas — même si
        aucune tâche n'était enregistrée, pour qu'une boucle qui vérifie
        encore une ancienne génération après coup s'arrête bien."""
        tache = cls._taches.get(canal)
        if tache is not None and not tache.done():
            try:
                tache.cancel()
            except Exception as exc:
                print(f"[HayaatiTaskRegistry] Annulation du canal '{canal}' a échoué : {exc}")
        cls._generations[canal] = cls._generations.get(canal, 0) + 1

    @classmethod
    def arreter_prefixe(cls, prefixe: str) -> None:
        """Arrête tous les canaux dont le nom commence par `prefixe` —
        typiquement toutes les boucles d'un écran donné, ex:
        arreter_prefixe("onboarding.")."""
        for canal in list(cls._taches.keys()):
            if canal.startswith(prefixe):
                cls.arreter(canal)

    @classmethod
    def generation_active(cls, canal: str, generation: int) -> bool:
        """À appeler à chaque itération d'une boucle enregistrée : False
        dès que ce canal a été relancé ou arrêté après le lancement de
        cette instance précise de la boucle."""
        return cls._generations.get(canal) == generation

    @classmethod
    def canaux_actifs(cls) -> Dict[str, bool]:
        """Diagnostic — utile pour un futur écran [DIAG-RESSOURCES] qui
        voudrait afficher le nombre de boucles de fond réellement
        vivantes plutôt que le seul compteur global de tâches asyncio."""
        return {
            canal: (tache is not None and not tache.done())
            for canal, tache in cls._taches.items()
        }
