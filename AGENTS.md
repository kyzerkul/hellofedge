# Hellofedge

Compagnon de trading **USD/JPY uniquement** pour un trader SMC (méthode RedPillFX). Il analyse, surveille, alerte et journalise. **Il ne passe jamais d'ordre.**

## Langue
Tout ce qui est destiné au trader (messages, docs, scope, specs, interface) est **en français**, simple et clair. Le code et ses identifiants peuvent rester en anglais.

## Sources de vérité
- Stratégie et règles de détection : `docs/CAHIER_DES_CHARGES.md` (section 1, notamment 1.12 le modèle d'entrée).
- Cas de test réels du trader : `exemples/README.md` (10 trades annotés, règles confirmées en fin de fichier).
- Plan et phases : `docs/PLAN_DE_DEVELOPPEMENT.md`.

## Règles non négociables
- Aucun ordre de trading, jamais. L'accès courtier est en lecture seule.
- Aucun secret dans le code, les commits ou le chat. Les secrets vivent dans des variables d'environnement ; `.env.example` ne contient que les noms.
- Heures stockées et calculées en **UTC**. Affichage à l'heure du Bénin (`Africa/Porto-Novo`, UTC+1). Les sessions sont ancrées sur le fuseau de leur place (Europe/London, America/New_York, Asia/Tokyo).
- Prise de liquidité = **clôture du corps** au-delà du niveau (M1, M3, M5). IPA touché = une **mèche** suffit.
- Le M3 est reconstruit à partir du M1 (OANDA ne fournit pas de M3).

## Stack
À décider par `/architect` (voir `docs/specs/` quand il existera). Rien n'est installé avant cette décision.

## Workflow
Skills du projet dans `.claude/skills/` : `/scope` → `/architect` → `/develop` → `/check verify` → `/test` → `/check review` → `/sync`. Décision coûteuse = plan présenté et validé par le trader avant tout code.

## Git
integration: off
Le trader valide les étapes sensibles. Branche de travail imposée par la session ; pas de push sans accord.
