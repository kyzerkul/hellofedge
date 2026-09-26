# Verify: Source de prix · spec 0002 · updated 2026-09-26
_Étapes tirées des critères d'acceptation de la spec 0002. `/check verify` les rejoue ; `/test` fixe celles qui durent. Cette première série couvre ce qui est construit : le fichier de référence (étape 1 du plan) et le code pur des bougies (étape 2), plus le garde « lecture seule ». Les étapes des adaptateurs, de la base et du direct viendront avec leur construction._

## À la main (le trader)
- [ ] Ouvrir `exemples/reference_oanda.csv` à côté de chaque capture et relire chaque ligne : le prix est celui de l'en-tête ou de l'étiquette High/Low, l'heure `ts_open_utc` est la bonne bougie → toutes les lignes sont justes, ou corrigées dans un commit qui dit pourquoi → AC-1
- [ ] Pour une capture M3 (ex3) : heure de la capture 12:16 + compte à rebours 01:08 → la bougie finit à 12:18 → `ts_open_utc` = 12:15, qui tombe bien sur :00, :03, :06… → AC-1 (règle de datation)
- [ ] Pour une capture M5 (ex5) : 13:33 + 01:36 → fin à 13:35 → `ts_open_utc` = 13:30 → AC-1 (règle de datation)
- [ ] Vérifier les points dont l'heure est incertaine (note « autre sommet presque égal » : ex3, ex4, ex17, ex18) → l'heure choisie est celle de la bougie qui porte vraiment l'extrême → AC-1, AC-12 (comparaison aux bougies voisines)

## Commandes (depuis `backend/`)
- [ ] `uv run pytest tests/test_reference.py` → le fichier se lit sans erreur, couvre les 19 captures, avec au moins 5 points M3 et 5 points M5, sans doublon → AC-1
- [ ] Changer une heure M3 du fichier en 12:16, relancer le test → échec qui cite la ligne et « ne tombe pas sur une bougie M3 » → AC-1 (contrôle de datation)
- [ ] `uv run pytest tests/test_timeframes.py` → le M3 est calé sur :00, :03, :06, le M5 sur :00, :05, et une minute absente n'est pas inventée (la bougie garde l'heure de début de sa tranche) → AC-7
- [ ] `uv run pytest tests/test_candle.py` → une bougie refuse un nombre à virgule flottante, plus de 3 décimales, une heure non UTC ou pas une minute pleine → AC-3 (minute pleine en UTC), invariant « prix en NUMERIC(10,3) »
- [ ] `uv run pytest tests/test_readonly_guard.py` → passe ; ajouter `def place_order` dans un fichier de `src/hellofedge/data/` → le test échoue en nommant le fichier et la ligne → AC-9

## Sources des valeurs (tableau *Value sourcing*)
- [ ] Prix OANDA de référence → viennent uniquement de `exemples/reference_oanda.csv`, validé par le trader → AC-1, AC-2
- [ ] Prix de la source pour un point M3 ou M5 → agrégation du M1 par `aggregate(…, 3)` ou `aggregate(…, 5)`, jamais une bougie M3 ou M5 demandée au fournisseur → AC-7
- [ ] Les autres lignes du tableau (seuil de 0,3 pip, minute attendue, marché ouvert, rollover, source active, état du flux) → à vérifier quand la mesure, le direct et `GET /api/feed/status` seront construits → AC-2, AC-4, AC-5, AC-8, AC-11

## Acceptance-criteria coverage
- AC-1 : fichier écrit (77 points), validation du trader en attente · AC-7 : agrégation construite et testée sur des bougies connues ; le contrôle sur les vrais points M3 et M5 attend la mesure · AC-9 : garde en place avant le premier adaptateur · AC-2, AC-3, AC-4, AC-5, AC-6, AC-8, AC-10, AC-11, AC-12 : pas encore construits
