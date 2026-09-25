# Exemples de référence

Captures USD/JPY fournies par le trader, annotées. Elles servent de **cas de test du moteur** : à terme, le moteur doit retrouver sur chaque exemple les mêmes niveaux, la même manipulation et la même entrée.

Convention : les graphiques TradingView sont en **UTC** (heure du Bénin = UTC+1, heure de Paris en été = UTC+2). Sessions de l'indicateur LuxAlgo, en UTC : Tokyo 00-09, Londres 07-16, New York 12-21.

Statut d'une lecture : `à valider` tant que le trader ne l'a pas confirmée.

---

## Lot 1

### Ex1 · 24/08/2026 · M1 · achat (`lot-1/ex1.png`)
| Élément | Lecture |
|---|---|
| Contexte | Londres fait son plus haut à 159.283 (~08:30 UTC), puis redescend et range sous 159.23 |
| Liquidité | Deux niveaux de lows tracés : **159.150** et **159.128** (lows de 07:45–07:50 UTC, retestés plusieurs fois) |
| Manipulation | 10:15–10:40 UTC : passage sous 159.150 puis mèche à ~159.120, **balayage de 159.128** d'environ 0.8 pip |
| Entrée | ~159.145 vers 10:40 UTC, après la reprise de 159.150 |
| SL / TP | SL ~159.120 (≈2.5 pips) · TP ~159.237 (≈3.7R) |
| Heure | 10:40 UTC = 11:40 Bénin = 12:40 Paris : **hors des fenêtres de la formation** (fin de Londres / NY Trap) |
| Résultat | Le plus haut suivant est ~159.235 (vers 11:05 UTC), **le TP est manqué d'environ 0.2 pip**. Voir Ex2 |
| Statut | à valider |

### Ex2 · 24/08/2026 · M1 · suite d'Ex1 (`lot-1/ex2.png`)
| Élément | Lecture |
|---|---|
| Position | Même entrée ~159.145, SL ~159.120, mais la zone verte ne monte qu'à ~159.162 |
| Question | TP réduit, sortie partielle ou fermeture manuelle ? Résultat final ? |
| Statut | à valider |

### Ex3 · 25/08/2026 · M3 · achat (`lot-1/ex3.png`)
| Élément | Lecture |
|---|---|
| Contexte | Tokyo range entre 159.22 et 159.40. Londres prend le plus haut de Tokyo et fait **159.493** (~08:10 UTC), puis chute |
| Accumulation | Range de Londres **159.235–159.350** de 09:00 à 12:00 UTC (rectangle tracé) |
| Liquidité | Bas du range et ligne grise **~159.222** (low de Tokyo vers 04:50 UTC) |
| Manipulation | ~12:00 UTC (ouverture de NY selon l'indicateur) : passage sous le bas du range, vers 159.22 |
| Entrée | ~159.255 vers 12:10 UTC |
| SL / TP | SL ~159.195 · TP **159.493** (le plus haut de Londres), ≈4R |
| Heure | 12:10 UTC = 14:10 Paris : fin du NY Trap, **avant les stats US de 12:30 UTC** |
| Statut | à valider |

### Ex4 · 25/08/2026 · M1 · suite d'Ex3 (`lot-1/ex4.png`)
| Élément | Lecture |
|---|---|
| Déroulé | Montée à ~159.30, puis chute vers 13:05 UTC jusqu'à **159.180**, sous le SL (~159.195) |
| Résultat probable | **−1R**. La chute arrive entre 12:30 et 13:10 UTC, pendant la séquence des stats US et l'ouverture de NY |
| Question | SL touché ? La flèche en pointillés indique-t-elle que tu attendais ce mouvement ? |
| Statut | à valider |

### Ex5 · 26/08/2026 · M5 · vente (`lot-1/ex5.png`)
| Élément | Lecture |
|---|---|
| Contexte | « BOS M15 (shift haussier) » annoté. Tokyo fait un plus bas à **158.881** (« Zone achat, liquidité sweep 158.881 ») |
| Manipulation | **12:30 UTC pile (stats US)** : chute jusqu'à ~158.93, sous le low de Londres (~158.935), puis rallye très fort jusqu'à **159.327**. C'est un Sell to Buy flagrant |
| Liquidité prise en haut | 159.185 puis le plus haut antérieur **~159.33** (ligne rouge du haut) |
| Entrée | Vente ~159.268, dans la « Zone vente / résistance » 159.26, après la prise de 159.327 |
| SL / TP | SL ~159.335 · TP ~159.105 (≈2.4R) |
| Question | Contre-tendance après un Sell to Buy net sur news : y a-t-il eu un Buy to Sell en M1 au plus haut ? Résultat ? |
| Statut | à valider |

---

## Lot 2

### Ex6 · 04/09/2026 · M5 · vente (`lot-2/ex6.png`)
| Élément | Lecture |
|---|---|
| Contexte HTF | Le 03/09, forte chute de ~157.0 à **155.29** (plus bas de NY). Remontée pendant la nuit |
| Zone | Bande rouge **156.45–156.48** (origine de la chute du 03/09) et ligne bleue **156.53** (point de structure du 03/09) |
| Accumulation | Tokyo range **156.10–156.46** de 03:30 à 09:00 UTC (rectangle violet) |
| Manipulation | ~09:30 UTC, début de Londres : pointe à **~156.58**, au-dessus de 156.53 et du plus haut de Tokyo, puis rejet. **Buy to Sell** |
| Entrée | Vente ~156.39 vers 10:10 UTC, sous la zone rouge |
| SL / TP | SL ~156.60 · TP **155.29** (plus bas de la veille), ≈5R |
| Événement | Drapeau US à 12:30 UTC : **NFP** (vendredi 04/09) |
| Statut | à valider |

### Ex7 · 04/09/2026 · M5 · suite d'Ex6 (`lot-2/ex7.png`)
| Élément | Lecture |
|---|---|
| Déroulé | Baisse jusqu'à ~156.17 vers 12:05 UTC (flèche en pointillés), puis **pointe NFP à 156.762** à 12:30 UTC, puis chute à ~155.40 |
| Position affichée | Entrée ~156.39, zone verte jusqu'à ~156.15 : le TP semble avoir été **ramené à ~156.15 (≈1.1R)** et touché avant les NFP |
| Leçon possible | Avec le TP initial (155.29), la pointe des NFP (156.76) aurait touché le SL (156.60) avant la chute. Sortir avant la news a sauvé le trade |
| Statut | à valider |

### Ex8 · 08/09/2026 · M1 · vente (`lot-2/ex8.png`)
| Élément | Lecture |
|---|---|
| Contexte HTF | Tokyo monte de **152.888** à ~153.90. Ligne **« IPA H1 » tracée à ~154.05**, au-dessus du prix |
| Accumulation | Londres range **153.72–153.97** de 07:00 à 08:00 UTC (rectangle rouge) |
| Manipulation | 08:00 UTC : pointe à ~153.98 au-dessus du range, puis rejet |
| Entrée | Vente ~153.87 vers 08:05 UTC |
| SL / TP | SL ~154.10, juste au-dessus de la ligne IPA H1 · TP **152.89** (plus bas de Tokyo), ≈4.3R |
| Statut | à valider |

### Ex9 · 08/09/2026 · M1 · suite d'Ex8 (`lot-2/ex9.png`)
| Élément | Lecture |
|---|---|
| Déroulé | Le prix remonte, passe **à travers l'IPA H1 (154.05)** et fait **154.135** à 08:44 UTC |
| Résultat probable | **SL touché (−1R)** |
| Lien avec les règles | Selon la formation (1.5 et 1.10 du cahier des charges), une zone située **juste sous un IPA non comblé** est un piège : le prix va d'abord combler l'IPA. Ici, la vente était placée sous l'IPA H1 encore ouvert. **C'est exactement le cas que le moteur doit signaler en TRAP** |
| Statut | à valider |

### Ex10 · 16/09/2026 · M5 · vente (`lot-2/ex10.png`)
| Élément | Lecture |
|---|---|
| Contexte | Londres fait son plus bas à **154.882** vers 07:20 UTC. Ligne bleue **~155.23** (niveau de 05:45–06:00 UTC) |
| Manipulation | De 11:30 à 13:00 UTC, rallye de 154.94 à ~155.27, qui **prend la ligne 155.23**. Rejet vers 13:05 UTC |
| Entrée | Vente ~155.20 vers 13:05 UTC |
| SL / TP | SL ~155.28 · TP ~154.83, sous le plus bas de Londres (ligne rouge), ≈4.6R |
| Heure | 13:05 UTC = 15:05 Paris, **entre les deux fenêtres NY** de la formation (12:30–13:00 et 13:30–14:00 UTC) |
| Événement | Drapeau US à **18:00 UTC** : probablement la **décision du FOMC** (16/09). Trade ouvert avant une annonce majeure |
| Question | Le repère « PA » près de l'entrée, et la ligne jaune 155.114 : que représentent-ils ? Résultat ? |
| Statut | à valider |

---

## Lot 3

### Ex11 · 16/09/2026 · M5 · suite d'Ex10 (`lot-3/ex11.png`)
| Élément | Lecture |
|---|---|
| Déroulé | À 13:20 UTC, le rallye continue jusqu'à **155.296**, au-dessus du SL (~155.28) |
| Résultat probable | **−1R**, avant même le FOMC de 18:00 UTC |
| Contexte a posteriori | Les jours suivants sont très haussiers (156.41 le soir même, 157.33 le 18/09). La vente d'Ex10 allait **contre le biais HTF** |
| Statut | à valider |

### Ex12 · 17/09/2026 · M3 · achat (`lot-3/ex12.png`)
| Élément | Lecture |
|---|---|
| Contexte HTF | La veille, NY monte jusqu'à **156.414** après le FOMC |
| Accumulation | Tokyo range 155.53–156.28, puis Londres range **155.55–155.91** |
| Liquidité | Ligne « **$** » à **~155.54** (plus bas de Tokyo et de Londres, equal lows) et ligne bleue **~155.51** (IPA M15, voir Ex13) |
| Manipulation | 12:10–12:30 UTC, début de NY : chute nette de 155.91 à **155.338**, qui balaie « $ » et l'IPA M15. **Sell to Buy flagrant** |
| Entrée | Achat ~155.54 vers 12:35 UTC, après la reprise de la ligne « $ » |
| SL / TP | SL ~155.30 · TP initial vers le plus haut de la veille (156.41) |
| Statut | à valider |

### Ex13 · 18/09/2026 · M5 · suite d'Ex12 (`lot-3/ex13.png`)
| Élément | Lecture |
|---|---|
| Repères | Ligne jaune **155.541** = prix d'entrée. Lignes bleues annotées « **IPA 15** » (155.51 et 155.23) |
| Déroulé | Montée régulière pendant NY, pause la nuit, puis **pointe à 157.33 pendant Tokyo** le 18/09 vers 03:00–05:00 UTC |
| Résultat probable | TP vers **~157.10**, soit **environ +6.5R**, après **~15 h de position, nuit comprise** |
| Leçon | Le trade type de la formation : biais HTF haussier, balayage d'equal lows + IPA M15, Sell to Buy net à l'ouverture de NY, entrée à la reprise du niveau |
| Statut | à valider |

### Ex14 · 22/09/2026 · M1 · vente (`lot-3/ex14.png`)
| Élément | Lecture |
|---|---|
| Contexte | Tokyo et le début de Londres tiennent vers **157.70–157.78**. À 08:37–08:45 UTC, **chute brutale** jusqu'à 156.87 : cassure de 157.565, puis de 157.265 |
| Niveaux | 157.565 (support de Tokyo cassé) · **157.265** (niveau cassé pendant la chute) · 156.97 |
| Retracement | 08:55–09:15 UTC : remontée jusqu'à **~157.27**, qui revient sur 157.265, dans le déséquilibre laissé par la chute |
| Entrée | Vente ~157.21 vers 09:15 UTC |
| SL / TP | SL ~157.30 · TP ~156.85 (plus bas de la chute), ≈4R |
| Question | Selon la formation, pas d'entrée sur retest. Ici, qu'est-ce qui rend ce retour valide pour toi : le comblement du déséquilibre (IPA en petite UT), une prise de liquidité sur 157.265, ou un Buy to Sell en M1 ? |
| Statut | à valider |

### Ex15 · 22/09/2026 · M1 · suite d'Ex14 (`lot-3/ex15.png`)
| Élément | Lecture |
|---|---|
| Déroulé | Descente régulière (flèche en pointillés) jusqu'à **156.850** à 10:00 UTC |
| Résultat probable | **TP touché, environ +4R**, en ~45 minutes |
| Statut | à valider |

---

## Lot 4

### Ex16 · 24/09/2026 · M1 · achat (`lot-4/ex16.png`)
| Élément | Lecture |
|---|---|
| Contexte | Tokyo monte de 157.80 à **158.489** (~06:45 UTC). Equal highs vers **158.455** (ligne blanche) |
| Liquidité | Ligne rouge **~158.165** (low de 06:00 UTC) · ligne bleue **~158.10** (plus haut de Tokyo vers 03:40 UTC, ancien point de structure) |
| Manipulation | 07:35–07:50 UTC, **dans la fenêtre de Londres de la formation** (9h–10h Paris) : chute jusqu'à ~158.07, qui balaie 158.165 et 158.10. **Sell to Buy** |
| Entrée | Achat ~158.19 vers 07:55 UTC, à la reprise de 158.165 |
| SL / TP | SL ~158.05 · TP initial **158.966** (ligne jaune), ≈5.5R |
| Statut | à valider |

### Ex17 · 24/09/2026 · M1 · suite d'Ex16 (`lot-4/ex17.png`)
| Élément | Lecture |
|---|---|
| Déroulé | Montée à travers 158.455 et 158.495 jusqu'à **158.802** vers 10:05 UTC, puis range sous des equal highs (rectangles jaunes 158.73–158.80) et baisse vers 11:15 UTC |
| Position affichée | La zone verte s'arrête vers **~158.70** : TP apparemment ramené de 158.966 à ~158.70 |
| Résultat probable | **TP touché, environ +3.6R** |
| Statut | à valider |

### Ex18 · 25/09/2026 · M1 · vente (`lot-4/ex18.png`)
| Élément | Lecture |
|---|---|
| Contexte | Tokyo chute de ~158.47 à **157.949** (~06:20 UTC). Londres range au-dessus de ce plus bas |
| Liquidité | Au-dessus : rouge **158.165** (plus haut de 06:30) · bleue **~158.19** · rouge **~158.28** (plus haut de 06:00) · bleue **~158.29** (low de 04:10, ancien point de structure) |
| Manipulation | 07:45–08:27 UTC : montée qui prend tous ces niveaux jusqu'à ~158.30, puis rejet. **Buy to Sell** |
| Entrée | Vente ~158.255 vers 08:28 UTC |
| SL / TP | SL ~158.32 · TP **~157.95** (plus bas de Tokyo et de Londres), ≈4.7R. Ligne blanche plus bas à **157.794** |
| Statut | à valider |

### Ex19 · 25/09/2026 · M1 · suite d'Ex18 (`lot-4/ex19.png`)
| Élément | Lecture |
|---|---|
| Déroulé | Descente régulière (flèche en pointillés) jusqu'à **157.926** à 09:08 UTC |
| Résultat probable | **TP touché, environ +4.7R**, en ~40 minutes |
| Statut | à valider |

---

## Premiers constats (lot 1)

1. **Tes entrées se font surtout entre 10:00 et 13:00 UTC** (11h–14h Bénin). C'est après la fenêtre de Londres de la formation (07:00–08:00 UTC) et avant ou pendant les stats US. L'outil doit mesurer **tes** fenêtres réelles, pas seulement celles de la formation.
2. **Ton schéma dominant : balayage d'equal lows ou du bas d'un range, puis reprise du niveau, puis achat avec un stop juste sous la mèche.** C'est très cohérent avec la formation (AMD + Sell to Buy).
3. **Les balayages sont petits** (0.2 à 1 pip) et les stops courts (2.5 à 6 pips). Un écart d'un pip entre les prix OANDA et ceux de FundedNext peut changer un signal. → Il faudra mesurer cet écart.
4. **Les stats US de 12:30 UTC** ont provoqué la manipulation d'Ex5 et, probablement, le stop d'Ex4. Cela confirme que la fenêtre de 12:30 UTC doit être traitée à part pour USD/JPY.

## Constats du lot 2

5. **Tes ventes suivent le même schéma que tes achats**, inversé : prise d'un plus haut (range de Tokyo, point de structure de la veille, plus haut d'accumulation), rejet, vente, et TP sur l'extrême opposé de la session (plus bas de Tokyo, de Londres ou de la veille). Les RR visés sont plus grands que dans le lot 1 (4 à 5R).
6. **Ex8 → Ex9 montre la valeur du filtre IPA** : une vente placée sous un IPA H1 non comblé a été stoppée quand le prix est allé combler l'IPA. Le moteur doit afficher « TRAP : IPA H1 ouvert au-dessus ».
7. **Les grosses annonces ont décidé de deux trades sur cinq** : les NFP (Ex7) et, probablement, le FOMC (Ex10). Le compagnon de position doit prévenir avant chaque annonce majeure, avec le R en cours et la distance au SL.
8. **Tu déplaces parfois ton TP en cours de route** (Ex2, Ex7). Le journal doit enregistrer le TP initial, le TP final et la raison du changement, pour mesurer si ces ajustements te rapportent.

## Constats du lot 3

9. **Tes meilleurs trades cochent toutes les cases de la formation** (Ex12→13 : biais HTF + equal lows + IPA M15 + Sell to Buy flagrant à l'ouverture de NY + entrée à la reprise). **Tes pertes ont chacune un défaut identifiable** : vente contre le biais HTF (Ex10→11), vente sous un IPA H1 ouvert (Ex8→9), achat juste avant les stats US (Ex3→4). Sur si peu de trades, c'est une piste et non une preuve. C'est exactement ce que le score de setup et les statistiques devront confirmer.
10. **Tu tiens parfois une position la nuit** (Ex13 : ~15 h, gain réalisé pendant Tokyo). Le compagnon de position doit couvrir la nuit : annonces japonaises, fixing de Tokyo, swap.
11. **Tu prends aussi des continuations après un mouvement violent** (Ex14→15) : retour dans le déséquilibre, puis reprise du mouvement. Ce modèle n'est pas décrit tel quel dans la formation. Il faut le définir avec toi pour le coder (voir la question d'Ex14).

## Synthèse des 19 captures (10 trades)

Les captures vont **par paires : l'entrée, puis le résultat** (précision du trader). Seule Ex5 n'a pas de capture de résultat.

### Bilan provisoire
| Trade | Captures | Entrée (UTC) | Résultat probable | Défaut identifié |
|---|---|---|---|---|
| Achat 24/08 | Ex1–2 | 10:40 | ≈ +0.7R (TP ramené à ~159.162) | — |
| Achat 25/08 | Ex3–4 | 12:10 | −1R | Entrée juste avant les stats US |
| Vente 26/08 | Ex5 | ~13:30 | ? (pas de capture de résultat) | Contre un Sell to Buy très fort sur news |
| Vente 04/09 | Ex6–7 | 10:10 | ≈ +1.1R (TP ramené avant les NFP) | — |
| Vente 08/09 | Ex8–9 | 08:05 | −1R | Sous un IPA H1 ouvert |
| Vente 16/09 | Ex10–11 | 13:05 | −1R | Contre le biais HTF, avant le FOMC |
| Achat 17/09 | Ex12–13 | 12:35 | ≈ +6.5R | — |
| Vente 22/09 | Ex14–15 | 09:15 | ≈ +4R | — |
| Achat 24/09 | Ex16–17 | 07:55 | ≈ +3.6R (TP ramené à ~158.70) | — |
| Vente 25/09 | Ex18–19 | 08:28 | ≈ +4.7R | — |

Sur les 9 trades au résultat connu : **6 gagnants, 3 perdants, environ +17.6R**. Chaque perte a un défaut que la formation interdit. L'échantillon est beaucoup trop petit pour conclure, mais la direction est claire.

### Tes deux modèles
**Modèle A · Balayage et reprise** (9 trades sur 10)
1. Un niveau de liquidité évident : extrême du range de la session, equal highs ou lows, ancien point de structure, extrême d'une session précédente.
2. Le prix le prend avec une accélération nette : **Sell to Buy ou Buy to Sell**.
3. **Entrée à la reprise du niveau**, le plus souvent en M1 (parfois M3 ou M5).
4. SL juste derrière la mèche de manipulation.
5. TP sur l'extrême opposé : plus bas ou plus haut de Tokyo, de Londres ou de la veille. RR visé : 3 à 6R, souvent ramené en cours de route.

**Modèle B · Continuation après déplacement** (Ex14)
Mouvement violent, retour dans le déséquilibre laissé, entrée dans le sens du mouvement. À définir avec le trader.

### Tes horaires réels
- **07:55 – 10:40 UTC** (Londres, 8h55–11h40 au Bénin) : 6 trades, **5 gagnants, 1 perdant** ;
- **12:10 – 13:30 UTC** (ouverture de NY, 13h10–14h30 au Bénin) : 4 trades, 1 gagnant, 2 perdants, 1 inconnu.

Piste à vérifier sur beaucoup plus de données : **Londres te réussit mieux que New York**, ce qui va dans le sens d'un passage à Asie + Londres.

### Ton code couleur (à confirmer)
| Couleur | Ce que j'en déduis |
|---|---|
| Rouge | Liquidité : equal highs ou lows, extrêmes locaux |
| Bleu | Point de structure ou IPA (parfois annoté « IPA H1 », « IPA 15 ») |
| Blanc | Plus haut ou plus bas d'une session précédente |
| Jaune | Niveau clé : prix d'entrée ou objectif |
| Rectangle | Range d'accumulation de la session |
