import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../config.dart';
import '../controleur.dart';
import '../modeles.dart';
import '../proposition.dart';
import '../theme/palette.dart';
import '../theme/theme_hayaati.dart';
import 'outils.dart';

/// Proposer une nouvelle mosquée (mosquee == null) ou corriger la position
/// d'une mosquée existante. La position est relevée sur place par le GPS :
/// la précision s'affiche en direct et s'améliore pendant quelques dizaines
/// de secondes ; l'utilisateur arrête quand elle lui convient.
class EcranProposition extends StatefulWidget {
  const EcranProposition({super.key, required this.c, this.mosquee});

  final ControleurAlAnsar c;
  final Fiche? mosquee;

  @override
  State<EcranProposition> createState() => _EcranPropositionState();
}

class _EcranPropositionState extends State<EcranProposition> {
  final TextEditingController _nom = TextEditingController();
  final TextEditingController _commentaire = TextEditingController();
  StreamSubscription<ResultatPosition>? _abonnement;
  PositionPrecise? _position;
  ErreurPosition? _erreur;
  bool _releve = false;

  bool get _correction => widget.mosquee != null;
  bool get _pret => _position != null && _nom.text.trim().length >= 2;

  @override
  void initState() {
    super.initState();
    _nom.text = widget.mosquee?.nom ?? '';
    _nom.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _abonnement?.cancel();
    _nom.dispose();
    _commentaire.dispose();
    super.dispose();
  }

  void _demarrerReleve() {
    final fournisseur = widget.c.config.fournisseurPosition;
    if (fournisseur == null) {
      setState(() => _erreur = ErreurPosition.indisponible);
      return;
    }
    _abonnement?.cancel();
    setState(() {
      _releve = true;
      _erreur = null;
    });
    _abonnement = fournisseur(precis: true).listen(
      (r) {
        if (!mounted) return;
        setState(() {
          final p = r.position;
          if (p != null) {
            _position = p;
            _erreur = null;
            final precision = p.precisionM;
            if (precision != null && precision <= 15) {
              _releve = false;
              _abonnement?.cancel();
            }
          } else {
            if (_position == null) _erreur = r.erreur;
            _releve = false;
          }
        });
      },
      onDone: () {
        if (mounted) setState(() => _releve = false);
      },
    );
  }

  void _arreterReleve() {
    _abonnement?.cancel();
    setState(() => _releve = false);
  }

  Future<void> _envoyer() async {
    _abonnement?.cancel();
    final c = widget.c;
    final t = c.t;
    final pos = _position;
    if (pos == null) return;
    final proposition = Proposition(
      type: _correction ? TypeProposition.correctionPosition : TypeProposition.nouvelleMosquee,
      pays: c.config.pays,
      villeId: widget.mosquee?.villeId ?? c.config.villeId,
      ficheId: widget.mosquee?.id,
      nom: _nom.text.trim(),
      position: pos,
      commentaire: _commentaire.text.trim(),
    );
    final message = proposition.versMessage(t);
    final numero = c.numeroModeration;
    if (numero != null) {
      final ok = await ouvrirWhatsApp(numero, message);
      if (ok) return;
    }
    await Clipboard.setData(ClipboardData(text: message));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(t('message_copie'))));
  }

  @override
  Widget build(BuildContext context) {
    final c = widget.c;
    final t = c.t;
    final theme = Theme.of(context);
    final p = _position;
    final precision = p?.precisionM;
    final faible = precision != null && precision > 50;
    final precisionTxt = precision == null ? '' : '  (${t('precision')} ±${precision.round()} m)';
    return Scaffold(
      appBar: barreHayaati(
        t(_correction ? 'type_correction' : 'type_nouvelle'),
        integre: c.config.integre,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(t(_correction ? 'proposition_intro_correction' : 'proposition_intro_nouvelle')),
          const SizedBox(height: 16),
          TextField(
            controller: _nom,
            readOnly: _correction,
            decoration: InputDecoration(
              labelText: t('nom_mosquee'),
              border: const OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          CarteHayaati(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (_releve)
                    Row(
                      children: [
                        const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                        const SizedBox(width: 10),
                        Expanded(child: Text(t('releve_en_cours'), style: theme.textTheme.titleSmall)),
                      ],
                    )
                  else if (p != null)
                    Text(t('position_relevee'), style: theme.textTheme.titleSmall),
                  if (p != null) ...[
                    const SizedBox(height: 4),
                    Text('${p.coord.lat.toStringAsFixed(6)}, ${p.coord.lon.toStringAsFixed(6)}$precisionTxt'),
                    if (faible)
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Text(
                          t('precision_faible'),
                          style: const TextStyle(color: PaletteHayaati.ambreAttente),
                        ),
                      ),
                  ],
                  const SizedBox(height: 8),
                  if (_releve)
                    FilledButton.tonal(
                      onPressed: p != null ? _arreterReleve : null,
                      child: Text(t('arreter_utiliser')),
                    )
                  else
                    FilledButton.tonalIcon(
                      onPressed: _demarrerReleve,
                      icon: const Icon(Icons.my_location),
                      label: Text(t(p == null ? 'ma_position' : 'relancer')),
                    ),
                  if (_erreur != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Text(
                        messageErreurPosition(t, _erreur!),
                        style: const TextStyle(color: PaletteHayaati.rougeErreur),
                      ),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _commentaire,
            maxLines: 3,
            decoration: InputDecoration(
              labelText: t('commentaire'),
              border: const OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          Text(t('vie_privee_proposition'), style: theme.textTheme.bodySmall),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: _pret ? _envoyer : null,
            icon: const Icon(Icons.send),
            label: Text(c.numeroModeration != null ? t('envoyer_whatsapp') : t('copier_message')),
          ),
        ],
      ),
    );
  }
}
