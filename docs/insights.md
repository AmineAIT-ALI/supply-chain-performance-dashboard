# Insights Métier — Supply Chain Performance Dashboard

Analyse des résultats obtenus sur le dataset synthétique (50 000 commandes, 2022–2024).
Ce document constitue une synthèse exploitable lors d'un entretien ou d'une présentation portfolio.

---

## 1. Performance Globale

**Taux de livraison à temps : ~82%**

Le taux OTDR global se situe autour de 82%, soit en dessous du seuil "bon" (85%). Cela signifie qu'environ **1 commande sur 5 est livrée en retard**, ce qui représente un risque réel pour la satisfaction client et la fidélisation.

**Délai moyen de livraison : ~11 jours**

Le lead time moyen de 11 jours est dans la fourchette acceptable pour un acteur multicanal opérant à l'international, mais reste perfectible sur les corridors longue distance (Asie-Pacifique, Afrique).

**Ratio coût logistique / CA : ~7,2%**

Ce ratio est en zone "acceptable" (5–10%). Les commandes à faible valeur présentent un ratio bien supérieur, ce qui questionne la rentabilité de certaines routes ou clients.

---

## 2. Performance des Transporteurs

### Insight 1 — Hétérogénéité structurelle des transporteurs

L'analyse révèle une **forte dispersion** entre transporteurs :
- Les 3 meilleurs transporteurs (ex. FastFreight, SkyBridge, EuroTrans) affichent un taux de retard < 10%
- Les 3 moins performants (ex. TerraRoute, ArcticFreight, MedShip) dépassent 25% de retard

Cette hétérogénéité suggère qu'une **renégociation contractuelle ou une réallocation des volumes** vers les transporteurs fiables pourrait réduire le taux de retard global de 3 à 5 points.

### Insight 2 — Le mode "Air" n'est pas systématiquement plus ponctuel

Contre-intuitivement, certains transporteurs aériens présentent des taux de retard équivalents aux transporteurs terrestres. Cela peut s'expliquer par des saturation d'hubs, des problèmes de coordination aéroport-entrepôt, ou des flux sur-engagés.

### Insight 3 — Le service "Economy" concentre les retards

Les commandes avec service level "Economy" présentent un taux de retard systématiquement plus élevé que "Express" ou "Premium" (+8 à +12 points). **Recommandation : revoir le routing des commandes prioritaires sur des services Express minimum.**

---

## 3. Analyse Géographique

### Insight 4 — L'Afrique et le Moyen-Orient sont des zones à risque élevé

Les entrepôts de Johannesburg et Riyadh affichent les délais moyens les plus élevés (>14 jours) et les taux de retard les plus importants (>22%). Ce phénomène est lié à :
- La complexité des infrastructures logistiques locales
- La dépendance à des correspondants locaux moins fiables
- Les délais douaniers et administratifs

**Action recommandée :** Identifier des partenaires logistiques locaux alternatifs ou revoir les délais promis aux clients de ces zones.

### Insight 5 — L'Europe est le périmètre le plus performant

Les entrepôts européens (Paris, Berlin, Amsterdam) affichent le meilleur taux OTDR (~87%) et le coût logistique le plus compétitif. La densité du réseau de transporteurs terrestres explique cette performance.

### Insight 6 — L'Asie-Pacifique est un volume fort mais performant

Shanghai et Tokyo concentrent un volume important (~28% des commandes) avec un taux de retard correct (~16%). La pression volumétrique justifie une surveillance rapprochée des capacités entrepôt.

---

## 4. Analyse des Retards

### Insight 7 — 60% des retards sont inférieurs à 7 jours

La grande majorité des retards sont "mineurs" (1 à 7 jours), ce qui suggère qu'ils sont probablement liés à des aléas opérationnels récurrents (saturation des dépôts, routing non optimisé) plutôt qu'à des défaillances systémiques.

Les retards >14 jours (~12% des commandes en retard) méritent une investigation au cas par cas : ils sont probablement liés à des incidents graves (perte de colis, problèmes douaniers, force majeure).

### Insight 8 — Les commandes "Standard" sont disproportionnellement en retard

Malgré leur volume dominant (60% des commandes), les commandes Standard contribuent à >70% des retards totaux. Les processus de routing semblent favoriser implicitement les commandes High et Critical.

**Recommandation :** Mettre en place un système d'allocation dynamique qui évite de systématiquement déprogrammer les commandes Standard au profit des urgences.

### Insight 9 — Saisonnalité des retards

Un pic de retard est observable en **T4** (octobre–décembre), correspondant à la période de forte activité commerciale (Black Friday, fêtes). Le taux de retard augmente de ~4 à 5 points sur cette période.

**Recommandation :** Anticiper les capacités logistiques dès septembre et contractualiser des capacités réservées avec les transporteurs de confiance.

---

## 5. Analyse Financière

### Insight 10 — Les commandes à faible valeur génèrent un ratio coût/valeur excessif

Les commandes < 100€ présentent un ratio coût logistique / valeur commande moyen de ~18%, ce qui les rend non rentables. Ce segment mérite une révision du modèle de frais de port ou un seuil minimum de commande.

### Insight 11 — Le CA "à risque" lié aux retards est significatif

Environ **18% du CA total** est lié à des commandes livrées en retard. Sur des commandes Critical, ce chiffre atteint 21%. Ces montants représentent une exposition aux litiges, remises commerciales et pénalités contractuelles.

---

## 6. Recommandations Stratégiques

| Priorité | Action | Impact estimé |
|---|---|---|
| 1 | Réallouer volumes vers les transporteurs < 10% taux retard | -3 à -5 pts de Late Rate |
| 2 | Imposer service "Standard" minimum pour commandes High/Critical | -2 à -4 pts Late Rate (prioritaires) |
| 3 | Renégocier SLA avec transporteurs Afrique / Moyen-Orient | -2 à -3 pts Late Rate zonal |
| 4 | Mettre en place un seuil de commande minimum (ex. 50€) | -5 pts ratio coût/CA |
| 5 | Préparer les capacités logistiques T4 dès septembre | -4 à -6 pts Late Rate saisonnier |
| 6 | Monitorer mensuellement le Top 5 entrepôts par taux de retard | Pilotage proactif |

---

## 7. Formulations pour Entretien

**Question : "Quel a été l'impact de votre analyse ?"**
> "L'analyse a permis d'identifier que 3 transporteurs sur 12 concentraient plus de 40% des retards, malgré un volume traité comparable aux autres. En simulant une réallocation des volumes vers les transporteurs les plus performants, le taux de retard global aurait pu être réduit de 4 à 5 points, soit environ 2 000 commandes supplémentaires livrées à temps sur la période."

**Question : "Qu'est-ce qui vous a surpris dans les données ?"**
> "Contra-intuitivement, le mode de transport aérien n'est pas systématiquement plus fiable que le transport terrestre. Certains transporteurs aériens affichaient des taux de retard supérieurs à des transporteurs ground opérant en Europe. Cela m'a amené à croiser le type de transporteur avec la zone géographique plutôt que de les analyser séparément."

**Question : "Comment avez-vous abordé la qualité des données ?"**
> "J'ai implémenté un pipeline de data cleaning en Python avec des règles explicites : détection des doublons par order_id, validation des cohérences de dates (livraison >= commande), traitement des outliers par z-score sur les coûts, et imputation contextuelle (médiane par transporteur pour les coûts manquants). Un rapport qualité est généré automatiquement avant et après nettoyage."
