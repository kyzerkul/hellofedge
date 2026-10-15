# 0003. Design system du cockpit : raisonnement

## Context

Le cockpit n'a aujourd'hui qu'un squelette (l'état du serveur) et des styles provisoires. Toutes les fonctions qui suivent ont un écran : la connexion (n°6), le fil minimal et son graphique (n°7), les zones (n°9), le setup (n°11), le téléphone (n°14). Sans langage commun décidé avant, chaque écran inventerait ses couleurs et ses composants, et le cockpit deviendrait incohérent dès la troisième fonction.

Le prototype (`docs/prototype/hellofedge-cockpit.html`) a posé une ambiance qui plaît : fond encre indigo, trois polices (une japonaise pour les titres, une pour le texte, une à chasse fixe pour les chiffres), cartes, puces, ruban des sessions. Mais il entre en conflit avec le code couleur du trader, confirmé dans `exemples/README.md` : **rouge = liquidité, bleu = IPA, blanc = extrêmes, jaune = objectif**. Dans le prototype, les bougies baissières sont rouges, l'accent est un bleu indigo et l'alerte est orange, proche du jaune. Sur les captures TradingView du trader, les bougies sont vert sarcelle et rouge, du même rouge que ses lignes de liquidité.

Contraintes : le cockpit doit marcher au clavier sur ordinateur et au doigt sur téléphone (critère « Done when » de la n°5), l'interface est en français, les heures s'affichent à l'heure du Bénin, et la spec 0001 fixe déjà React, Tailwind « branché sur les variables du design system » et Lightweight Charts pour le graphique. Le cockpit sera installable (PWA) et doit pouvoir s'ouvrir hors ligne une fois installé. Une seule personne s'en sert, sans équipe de design.

## Options considered

### Option 1 : CSS du prototype, composants faits main

On reprend les classes CSS du prototype telles quelles dans un fichier global, et on écrit nous mêmes chaque composant interactif en React.

**Pros**:
- Aucune dépendance nouvelle, le rendu du prototype est obtenu tout de suite.

**Cons**:
- Contredit la spec 0001 (Tailwind branché sur les jetons).
- Le clavier, le focus, les rôles ARIA et le toucher (appui unique, annulation en glissant) sont à réécrire et tester composant par composant ; c'est là que les bugs d'accessibilité naissent.

### Option 2 : jetons dans le thème Tailwind v4, composants React Aria stylés par le projet (retenue)

Les valeurs vivent dans le bloc `@theme` de Tailwind v4 (des variables CSS), la palette par défaut est retirée, et les composants interactifs s'appuient sur React Aria Components, une bibliothèque sans style d'Adobe, habillée avec nos classes.

**Pros**:
- Une source unique de valeurs, lisible par Tailwind, par le CSS et par le graphique à l'exécution.
- Clavier, lecteur d'écran et toucher éprouvés sur de vrais appareils, ce qui sert directement le critère « au clavier comme au doigt ».

**Cons**:
- Une dépendance de taille moyenne, et une façon de styler propre à React Aria (attributs `data-*`).

### Option 3 : Tailwind et Radix Primitives (ou une collection prête comme shadcn/ui)

Même thème, mais des composants Radix, souvent fournis tout faits par shadcn/ui.

**Pros**:
- Très répandu, beaucoup d'exemples, démarrage rapide avec shadcn/ui.

**Cons**:
- La gestion du toucher est moins travaillée que celle de React Aria (appui, annulation, focus après un toucher).
- shadcn/ui apporte son propre style et ses propres jetons, à défaire pour retrouver le prototype.

### Option 4 : jetons dans un fichier JSON qui génère le CSS et le TypeScript

Un `tokens.json` produit les variables CSS, des constantes TypeScript pour le graphique et une palette Python pour les images d'alerte.

**Pros**:
- Une source unique pour trois consommateurs, sans lecture à l'exécution.

**Cons**:
- Un outil de génération de plus à maintenir, pour un seul développeur et un seul thème ; la lecture des variables CSS à l'exécution et un test de comparaison côté Python donnent la même garantie.

## Rationale

Le critère qui décide est « au clavier comme au doigt » sur le téléphone du trader : c'est exactement ce que React Aria a été construit pour garantir, alors qu'avec l'option 1 ce serait notre code à nous, testé seulement dans jsdom. Radix (option 3) le fait bien au clavier mais moins bien au toucher, et shadcn/ui imposerait un style qu'il faudrait défaire pour retrouver le prototype. L'option 2 respecte aussi la spec 0001 sans rien ajouter de neuf côté stack, Tailwind étant déjà prévu.

Le choix de couleurs suit le trader : son code couleur est déjà dans ses yeux depuis TradingView, donc on le garde à l'identique (valeurs lues dans les pixels de ses captures) et on le protège. Tout ce qui pourrait lui faire concurrence change de teinte : bougies grises, accent violet, vente magenta, erreur orange. Les gardes automatiques (couleurs réservées, couleurs en dur, miroir de `design.md`, contrastes) existent parce qu'une seule personne développe : sans eux, une couleur glissée « pour essayer » finirait par casser le code sans que personne ne le voie. L'option 4 a été écartée parce qu'elle ajoute un générateur pour un gain que le test de comparaison apporte déjà.

Deux corrections au prototype viennent des contrastes : son texte discret (`#5B6782`, 3,3:1) ne se lit pas assez bien, et une fois relevé au seuil il ne se distinguait plus du gris secondaire, d'où un seul gris de texte ; le bleu IPA (3,9:1) suffit pour un trait mais pas pour du texte, d'où la règle « une couleur de niveau ne colore jamais un mot ». La liquidité prise à 50 % (environ 2:1) est une exception voulue par le trader : elle doit s'effacer, et le mot « pris » porte l'information.

La relecture croisée par un autre modèle a trouvé 25 décisions que la première version laissait à inventer (formats exacts, états de chaque composant, état « marché fermé », règles du renvoi vers `index.html`, motifs des gardes, façon de lire les fichiers dans les tests). Le trader a accepté les corrections en bloc ; elles sont intégrées à `index.md`. Les polices sont livrées avec l'appli pour l'usage hors ligne de la PWA et pour ne dépendre d'aucun service tiers à chaque ouverture.
