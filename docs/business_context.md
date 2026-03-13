# Contexte Métier — Supply Chain Performance Dashboard

## Problématique

Dans un environnement logistique mondial de plus en plus complexe, les directions supply chain font face à plusieurs défis structurels :

- **Visibilité insuffisante** sur la performance réelle des transporteurs
- **Délais de livraison non maîtrisés**, impactant la satisfaction client
- **Coûts logistiques opaques** et difficiles à comparer entre partenaires
- **Retards concentrés** sur certaines zones géographiques ou catégories de produits
- **Absence d'indicateurs consolidés** permettant une décision rapide en comité de direction

Ce projet simule le contexte d'une entreprise **distributeur multicanal** opérant dans plusieurs régions du monde (Europe, Amérique du Nord, Asie-Pacifique, Moyen-Orient, Afrique), gérant :

- **50 000+ commandes** sur 3 ans (2022–2024)
- **12 transporteurs** de types variés (Air, Ground, Sea, Rail)
- **18 entrepôts** répartis sur 4 continents
- **250 produits** dans 7 grandes catégories
- **2 000 clients** B2B, B2C et Enterprise

---

## Objectifs Métier

### Niveau Opérationnel
- Identifier les commandes en retard en temps réel
- Comparer la ponctualité des transporteurs
- Détecter les entrepôts avec des anomalies de performance

### Niveau Tactique
- Optimiser les choix de transporteurs par route et par priorité
- Piloter les volumes et coûts logistiques par entrepôt
- Anticiper les pics de retard selon les tendances mensuelles

### Niveau Stratégique
- Mesurer le ratio coût logistique / valeur commande
- Évaluer la performance par région pour guider l'expansion
- Identifier les catégories produit à risque logistique élevé

---

## Utilisateurs Cibles

| Profil | Usage principal | Pages utilisées |
|---|---|---|
| Directeur Supply Chain | Suivi KPI globaux, alertes | Page 1 |
| Responsable Transport | Évaluation transporteurs | Page 2 |
| Responsable Logistique | Pilotage entrepôts | Page 3 |
| Analyste Supply Chain | Analyse approfondie des retards | Page 4 |
| Contrôle de Gestion | Analyse financière coûts logistiques | Pages 1, 4 |

---

## Périmètre du Projet

### Ce que ce projet couvre
- Pipeline ETL complet : extraction → nettoyage → transformation → chargement
- Modèle dimensionnel en étoile (schéma Power BI-ready)
- Calcul de KPI supply chain standards et avancés
- Dashboard Power BI multi-pages orienté décision
- Base de données SQLite avec vues analytiques

### Hors périmètre (extensions possibles)
- Prévision de la demande (ML/forecasting)
- Intégration temps réel (API, streaming)
- Alertes automatiques (Power Automate)
- Module de simulation de scenarios

---

## Valeur Métier Générée

**Avant ce dashboard :**
- Rapports Excel hebdomadaires manuels
- Visibilité limitée aux données du mois précédent
- Impossible de croiser transporteur × entrepôt × région en un clic

**Après ce dashboard :**
- Visibilité instantanée sur la performance logistique
- Identification en 30 secondes des transporteurs problématiques
- Drill-down en 2 clics de la région → pays → entrepôt
- Comparaison YoY / MoM automatisée pour les revues de performance

---

## Glossaire Métier

| Terme | Définition |
|---|---|
| Lead Time | Délai total entre la date de commande et la date de livraison réelle |
| Delay Days | Nombre de jours entre la livraison promise et la livraison réelle (>0 = retard) |
| On-Time Delivery Rate | % de commandes livrées avant ou à la date promise |
| Late Rate | % de commandes livrées après la date promise |
| Shipping Cost Ratio | Coût logistique / Valeur de la commande (indicateur d'efficience) |
| Priority Level | Niveau de priorité assigné à la commande : Standard, High, Critical |
| Carrier | Transporteur chargé d'acheminer la commande |
| Warehouse | Entrepôt d'origine de l'expédition |
| Service Level | Type de service choisi : Economy, Standard, Express, Premium |
