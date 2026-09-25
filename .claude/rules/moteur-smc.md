---
paths:
  - "**/engine/**"
  - "**/smc/**"
  - "tests/**"
---

# Règles du moteur SMC

Référence complète : `docs/CAHIER_DES_CHARGES.md` §1 et `exemples/README.md` (règles confirmées).

- Toute détection est **déterministe et testée**. Aucune IA ne décide d'un niveau.
- Strong High/Low = swing formé **après** une prise de liquidité ; sinon No Strong (piège).
- Prise de liquidité validée uniquement par la **clôture du corps** au-delà du niveau.
- Manipulation « flagrante » = accélération vers la liquidité anormalement grande par rapport au mouvement qui précède (ratio calibré sur les exemples).
- IPA/EPA : uniquement W, D1, H4, H1, M15 ; IPA précédé d'un FVG ; touché dès qu'une mèche l'atteint.
- Déclencheurs d'entrée : IFVG/BPR, CISD (clôture du corps de la bougie de manipulation), petit True BOS. Recherche M5 puis M3 puis M1.
- Jamais d'entrée sur retest : l'entrée se fait pendant le cycle, avant la prise de la prochaine liquidité.
- Breakeven : à la cassure du dernier point de structure interne formé avant la prise de liquidité. Le TP n'est jamais déplacé.
- Chaque nouvelle règle est validée sur les 10 trades de `exemples/` avant d'être considérée comme acquise.
