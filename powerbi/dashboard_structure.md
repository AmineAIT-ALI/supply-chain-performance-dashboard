# Power BI — Structure du Dashboard

## Vue d'ensemble

**Nom du fichier :** `Supply_Chain_Performance_Dashboard.pbix`
**Thème couleur :** Professionnel — Bleu foncé (#1A2E4A), Gris clair (#F5F7FA), Accent bleu (#2E86C1), Vert (#27AE60), Orange (#E67E22), Rouge (#C0392B)
**Police :** Segoe UI (native Power BI)
**Format :** Paysage 16:9 — 1280 × 720 px

---

## Filtres globaux (Panel de filtres)

Disponibles sur toutes les pages via le volet de filtres ou des slicers partagés :

| Filtre | Type | Source |
|---|---|---|
| Période | Plage de dates | dim_date[date] |
| Année | Liste déroulante | dim_date[year] |
| Trimestre | Boutons | dim_date[year_quarter] |
| Région | Liste multi-sélection | fact_orders[region] |
| Pays | Liste multi-sélection | fact_orders[country] |
| Transporteur | Liste multi-sélection | dim_carrier[carrier_name] |
| Entrepôt | Liste multi-sélection | dim_warehouse[warehouse_name] |
| Statut commande | Boutons | fact_orders[order_status] |
| Priorité | Boutons | fact_orders[priority_level] |
| Type transporteur | Boutons | dim_carrier[carrier_type] |

---

## PAGE 1 — Vue Exécutive

**Titre :** `Supply Chain Executive Overview`
**Objectif :** Vision globale pour le management — décision rapide

### KPI Cards (ligne du haut)
| Card | Mesure | Format |
|---|---|---|
| Total Orders | `[Total Orders]` | Entier avec séparateurs |
| Total Revenue | `[Revenue Formatted]` | K€ / M€ |
| On-Time Rate | `[On-Time Delivery Rate %]` | 0.0% — couleur conditionnelle |
| Late Orders | `[Late Orders Count]` | Entier, fond rouge si > seuil |
| Avg Lead Time | `[Avg Lead Time Days]` | 0.0 jours |
| Shipping Cost Ratio | `[Shipping Cost Ratio %]` | 0.0% |

*Mise en forme conditionnelle :*
- On-Time Rate : vert ≥ 85%, orange 75–85%, rouge < 75%
- Late Orders : rouge si taux > 20%

### Visuels principaux

**1. Courbe d'évolution mensuelle (Area Chart)**
- Axe X : `dim_date[year_month]`
- Valeur : `[Total Orders]`, `[Late Orders Count]`
- Légende : 2 séries superposées
- Titre : "Monthly Order Volume & Late Orders"

**2. Carte géographique (Map)**
- Localisation : `fact_orders[country]`
- Taille des bulles : `[Total Orders]`
- Couleur : `[Late Rate %]` (dégradé vert → rouge)
- Titre : "Order Distribution by Country"

**3. Graphique en barres (Bar Chart) — Top transporteurs**
- Axe Y : `dim_carrier[carrier_name]`
- Valeur X : `[Late Rate %]`
- Tri décroissant
- Couleur : barre conditionnelle (rouge/orange/vert)
- Titre : "Carrier On-Time Performance"

**4. Graphique en anneau (Donut Chart)**
- Valeurs : `[Total Orders]`
- Légende : `fact_orders[order_status]`
- Titre : "Order Status Distribution"

**5. Graphique en barres empilées**
- Axe X : `fact_orders[region]`
- Valeurs : `[Total Orders]` (empilé par `priority_level`)
- Titre : "Orders by Region & Priority"

---

## PAGE 2 — Analyse Transporteurs

**Titre :** `Carrier Performance Analysis`
**Objectif :** Comparaison et audit des transporteurs

### Visuels

**1. Tableau comparatif (Table)**
Colonnes :
- Carrier Name
- Carrier Type
- Service Level
- Total Orders
- Late Rate %
- Avg Lead Time Days
- Avg Shipping Cost
- Revenue Share %
- Rank (calculé par DAX)

Mise en forme : barres de données sur "Late Rate %", couleur conditionnelle

**2. Scatter Plot — Coût vs. Performance**
- Axe X : `[Avg Shipping Cost]`
- Axe Y : `[Late Rate %]`
- Taille des bulles : `[Total Orders]`
- Légende : `dim_carrier[carrier_type]`
- Titre : "Cost vs. Reliability — Carrier Quadrant View"
- *Lignes de référence : médiane coût + médiane taux de retard (4 quadrants)*

**3. Barres groupées — Délai moyen par transporteur**
- Axe X : `dim_carrier[carrier_name]`
- Valeurs : `[Avg Lead Time Days]`, `[Avg Delay When Late]`
- Titre : "Lead Time & Delay by Carrier"

**4. Graphique en courbe — Taux de retard mensuel par transporteur**
- Axe X : `dim_date[year_month]`
- Valeurs : `[Late Rate %]`
- Légende : `dim_carrier[carrier_name]`
- Slicer : sélection de 1 à 3 transporteurs
- Titre : "Monthly Late Rate Trend by Carrier"

**5. Cards de synthèse**
- Best Carrier (taux de retard le plus bas)
- Worst Carrier (taux de retard le plus haut)
- Avg Carrier Late Rate

---

## PAGE 3 — Opérations & Entrepôts

**Titre :** `Warehouse Operations Overview`
**Objectif :** Pilotage des entrepôts, identification des anomalies

### Visuels

**1. Heatmap (Matrix)**
- Lignes : `dim_warehouse[warehouse_name]`
- Colonnes : `dim_date[month_abbr]`
- Valeurs : `[Late Rate %]`
- Mise en forme conditionnelle couleur : vert → rouge
- Titre : "Late Rate Heatmap by Warehouse × Month"

**2. Histogramme — Volume par entrepôt**
- Axe X : `dim_warehouse[warehouse_name]`
- Valeur Y : `[Total Orders]`
- Couleur : `dim_warehouse[country]`
- Titre : "Order Volume by Warehouse"

**3. Barres horizontales — Délai moyen par entrepôt**
- Axe Y : `dim_warehouse[warehouse_name]`
- Valeur X : `[Avg Lead Time Days]`
- Référence : ligne de moyenne globale
- Titre : "Average Lead Time by Warehouse"

**4. Carte KPI par entrepôt sélectionné**
- Slicer : `dim_warehouse[warehouse_name]`
- Cards : Total Orders, Late Rate, Avg Shipping Cost, Total Revenue

**5. Graphique en courbe — Évolution volumétrique**
- Axe X : `dim_date[year_month]`
- Valeurs : `[Total Orders]` par entrepôt sélectionné
- Titre : "Monthly Volume Trend — Selected Warehouse"

---

## PAGE 4 — Analyse des Retards

**Titre :** `Delay Analysis & Root Cause`
**Objectif :** Identifier les patterns de retard et prioriser les actions

### Visuels

**1. Graphique en barres — Distribution des retards**
- Axe X : `delay_bucket` (buckets de retard)
- Valeur Y : `[Total Orders]` (filtrées sur is_late = 1)
- Couleur : palette dégradée orange → rouge
- Titre : "Delay Distribution (Late Orders Only)"

**2. Courbe — Taux de retard mensuel avec moyenne mobile**
- Axe X : `dim_date[year_month]`
- Valeur 1 : `[Late Rate %]`
- Valeur 2 : `[Late Rate 3M Rolling %]`
- Titre : "Monthly Late Rate with 3-Month Rolling Average"

**3. Barres — Retards par catégorie de produit**
- Axe X : `main_category` (depuis supply_chain_analytics)
- Valeurs : `[Late Rate %]`, `[Late Orders Count]`
- Tri décroissant par taux de retard
- Titre : "Late Rate by Product Category"

**4. Barres groupées — Retards par priorité**
- Axe X : `fact_orders[priority_level]`
- Valeurs : `[Total Orders]`, `[Late Orders Count]`
- Titre : "Orders vs. Late Orders by Priority Level"

**5. Table détaillée filtrable**
Colonnes :
- Order ID
- Order Date
- Country / Region
- Carrier Name
- Warehouse Name
- Priority Level
- Delay Days
- Order Value
- Order Status

Filtres contextuels : cliquer sur un transporteur ou entrepôt pour filtrer

**6. Cards d'alerte**
- Critical Late Orders (commandes prioritaires en retard)
- Max Delay Days
- Avg Delay When Late
- Late Revenue at Risk

---

## Recommandations UX

### Navigation
- Utiliser des **boutons de navigation** entre pages (icônes dans l'en-tête)
- Ajouter un **breadcrumb** textuel dans chaque page
- Inclure un bouton **"Reset All Filters"** (action de signets)

### Mise en forme globale
- En-tête fixe avec logo (placeholder) + titre de page + dernière actualisation
- Pied de page avec mention "Données synthétiques — Usage portfolio"
- Couleur de fond des pages : #F5F7FA (gris très clair, professionnel)
- Couleur des cards : blanc (#FFFFFF) avec bordure légère

### Interactivité
- Tous les visuels sont **cross-filtrés** (comportement par défaut Power BI)
- Ajouter des **tooltips enrichis** sur les transporteurs et entrepôts
- Utiliser les **signets** pour sauvegarder des vues prédéfinies :
  - "Vue Europe uniquement"
  - "Commandes critiques en retard"
  - "Performance 2024"

### Accessibilité
- Titres de visuels explicites (pas d'acronymes sans explication)
- Alt text sur tous les visuels
- Contraste suffisant sur les couleurs conditionnelles

---

## Checklist de publication

- [ ] Toutes les mesures DAX testées et validées
- [ ] Relations vérifiées dans le modèle
- [ ] Filtres croisés configurés correctement
- [ ] Format date uniforme sur tous les axes
- [ ] Tooltips configurés sur les visuels clés
- [ ] Navigation entre pages fonctionnelle
- [ ] Mode mobile configuré (optionnel)
- [ ] Signets créés pour les vues importantes
