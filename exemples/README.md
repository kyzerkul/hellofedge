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

## Premiers constats (lot 1)

1. **Tes entrées se font surtout entre 10:00 et 13:00 UTC** (11h–14h Bénin). C'est après la fenêtre de Londres de la formation (07:00–08:00 UTC) et avant ou pendant les stats US. L'outil doit mesurer **tes** fenêtres réelles, pas seulement celles de la formation.
2. **Ton schéma dominant : balayage d'equal lows ou du bas d'un range, puis reprise du niveau, puis achat avec un stop juste sous la mèche.** C'est très cohérent avec la formation (AMD + Sell to Buy).
3. **Les balayages sont petits** (0.2 à 1 pip) et les stops courts (2.5 à 6 pips). Un écart d'un pip entre les prix OANDA et ceux de FundedNext peut changer un signal. → Il faudra mesurer cet écart.
4. **Les stats US de 12:30 UTC** ont provoqué la manipulation d'Ex5 et, probablement, le stop d'Ex4. Cela confirme que la fenêtre de 12:30 UTC doit être traitée à part pour USD/JPY.
