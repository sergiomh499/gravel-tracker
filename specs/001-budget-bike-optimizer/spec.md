# Feature Specification: Budget Bike Optimizer

**Feature Branch**: `001-budget-bike-optimizer`

**Created**: 2026-10-09

**Status**: Draft

**Input**: User description: "profesionaliza el proyecto de cara a que sea realmente usable y utilizable, y util al fin y al cabo, quiero maxima eficiencia y resultados a la hora de conseguir una bici para mi presupuesto por el mejor precio real para mi"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Budget-Targeted Real Deal Recommendation (Priority: P1)

As a cyclist searching for a gravel bike with a specific budget, I want to query the system with my maximum spending limit (and optional rider height/size) so that I immediately receive an executive, noise-free recommendation of the top 3 best complete gravel bikes I can buy right now, with verified availability and direct links.

**Why this priority**: Solves the core user problem directly. Instead of browsing through hundreds of unfiltered database rows, the user gets an instant, trustworthy decision on how to maximize their money right now.

**Independent Test**: Provide a budget ceiling (e.g., 1000 €). The system returns an executive summary with the #1 best value-for-money bike within budget, the #2 steepest discount/outlet bargain, and direct purchase links for both.

**Acceptance Scenarios**:

1. **Given** a catalogue with various bikes across different price tiers, **When** the user requests recommendations for a budget ceiling of 1.000 € and height 1,69 m, **Then** the system outputs only complete, compatible gravel bikes priced at or below 1.000 €, ranked by objective component quality.
2. **Given** a search with zero valid options strictly below budget, **When** the recommendation engine runs, **Then** the system clearly states that no complete bikes meet all criteria below that limit and offers the nearest viable candidate just above the threshold.

---

### User Story 2 - Strict Noise Exclusion & Reality Filter (Priority: P2)

As a prospective buyer, I want the system to rigorously exclude invalid listings (loose bike frames, e-bikes/motorized bikes, out-of-stock listings, closed or liquidated vendors, and non-gravel disciplines) so that I never waste time researching phantom deals or irrelevant products.

**Why this priority**: Usability and credibility depend on data accuracy. Presenting liquidated stores (like Tuvalum) or frames without components (like bare framesets) as "Tier S+ bargains" destroys utility.

**Independent Test**: Query the ranking or deal system; verify that no listings labeled as frames, ebikes, or from liquidated merchants appear in any recommendation list.

**Acceptance Scenarios**:

1. **Given** database records containing bare framesets (e.g., "Cuadro Gravel"), e-bikes, or shops marked as closed/liquidated, **When** any ranking, budget search, or alert runs, **Then** those records are completely filtered out from active recommendations.
2. **Given** listings with explicit sizes, **When** a user specifies a target rider height or size, **Then** listings marked as "incompatible size" or missing compatible sizes are excluded from the primary recommendation podio.

---

### User Story 3 - Smart Stretch & Compromise Analysis (Priority: P3)

As a cost-conscious buyer, I want to know if spending a small incremental amount (e.g., 50 € to 150 € over budget) unlocks a major component leap (such as switching from mechanical brakes to full hydraulic Shimano GRX, or gaining a carbon fork), or conversely if a cheaper model offers 95% of the same performance.

**Why this priority**: Real-world bike purchasing involves critical component boundaries. A 950 € bike with mechanical brakes is often a worse investment than a 1.050 € bike with full hydraulic brakes. Surfacing this "smart stretch" saves the buyer from expensive post-purchase regret.

**Independent Test**: Request recommendations for 950 €. The system shows the best option $\le$ 950 €, but also highlights a "Smart Stretch" recommendation at 1.050 € explicitly pointing out the hydraulic brake upgrade.

**Acceptance Scenarios**:

1. **Given** a user budget ceiling $B$, **When** a bike priced between $B$ and $B \times 1.15$ possesses a component tier upgrade (e.g., mechanical to hydraulic, or alloy fork to carbon), **Then** the system displays a "Smart Stretch" advisory note with the exact spec delta.
2. **Given** a user budget ceiling $B$, **When** a bike priced at $B \times 0.85$ matches the primary spec within 5% quality score, **Then** the system displays a "Budget Saver" alternative showing potential savings.

---

### User Story 4 - Multi-Channel Purchasing Clarity (Priority: P4)

As a buyer evaluating real total cost, I want clear distinction between brand-new stock in online shops, immediate local pickup in physical bike shops (in the user's region), and certified second-hand/refurbished options with buyer protection, including shipping/warranty considerations.

**Why this priority**: A 900 € bike on a peer-to-peer platform without inspection is not the same real risk/cost as a 950 € bike with a 2-year warranty in a local shop. The user needs transparency on purchasing channels.

**Independent Test**: Review a recommendation card; verify that channel type (Local Shop, Online Retailer, Certified Refurbished, Private Second-Hand) is explicitly labeled with relevant warranty or pickup context.

**Acceptance Scenarios**:

1. **Given** a recommended bike, **When** the user views the product card, **Then** the purchase channel is categorized (Tienda Local, Tienda Online, Ocasión Certificada, Particular) along with physical proximity or warranty status.
2. **Given** a user preference for local physical inspection only, **When** filtered by local stores, **Then** only bikes with verifiable physical store presence in the user's declared zone are shown.

---

### Edge Cases

- **No inventory within budget**: When no complete bike exists below the declared budget, the system gracefully informs the user, indicates the minimum budget required to purchase an entry-level gravel bike with acceptable components, and lists the top 2 closest models.
- **Ambiguous sizing in listing**: When a listing does not state a concrete frame size or lists "Talla Única", it must be flagged as "Talla por verificar" and demoted behind verified-size listings.
- **Stale or dead product links**: When a scraped product page returns HTTP 404/410 or indicates "Agotado / Sin stock", the system flags the listing as inactive and excludes it from the immediate recommendation podio.
- **Budget ceiling unrealistically high**: When a user inputs an unusually high budget (e.g., 10.000 €), the system caps recommendations at diminishing returns thresholds and explains that gravel value-for-money plateaus around 2.500 € – 3.500 €.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a single-command budget recommendation workflow accessible via both CLI and Telegram bot interfaces.
- **FR-002**: The system MUST accept a maximum budget limit (in Euros) and optional rider parameters (height in cm or nominal frame size) as query inputs.
- **FR-003**: The recommendation engine MUST strictly filter out bare frames, motorized/e-bikes, non-gravel disciplines, and closed/liquidated merchants from recommendation results.
- **FR-004**: The system MUST calculate an objective Value-for-Money (VfM) index for every candidate bike, combining component quality metrics (braking type, gearing range, frame and fork material) normalized by the real asking price.
- **FR-005**: The recommendation output MUST present a concise Executive Podio containing at most 3 top candidate bikes: the Best Value within Budget, the Top Discounted Bargain, and (if applicable) a Smart Stretch candidate.
- **FR-006**: Each recommended bike in the output MUST display: Brand and Model, Verified Real Price, Nominal PVP and Discount %, Target Size Compatibility, Key Specs (Drivetrain, Brakes, Frame/Fork Material), Shop Name & Channel Type, and a direct purchase URL.
- **FR-007**: The system MUST identify and flag "Smart Stretch" candidates when an expenditure increase $\le 15\%$ over the user's budget yields a critical component upgrade (e.g., transition from mechanical to hydraulic disc brakes).
- **FR-008**: The system MUST allow the user to filter or prioritize recommendations by purchase channel: All channels, Physical stores only (local zone), or Certified refurbished/second-hand.
- **FR-009**: The system MUST persist the user's budget and sizing preferences to prevent repetitive data entry during recurring sessions.
- **FR-010**: The system MUST verify listing availability and purge or deactivate out-of-stock listings from active recommendation queues.

### Key Entities

- **Bike Offer**: Represents a complete bicycle listing available for purchase.
  - Attributes: identifier, brand, model, discipline, asking price, original PVP, discount percentage, frame material, fork material, drivetrain group and configuration, brake type, available size list, store identifier, channel type (online, physical, certified refurbished, peer-to-peer), product URL, active stock status.
- **Rider Profile**: Represents the user's personal purchasing parameters and physical constraints.
  - Attributes: user identifier, height in centimeters, target nominal frame size, admissible sizes, geographical zone, target budget, maximum stretch budget, preferred purchase channels.
- **Recommendation Result**: Represents the synthesized decision output for a specific budget inquiry.
  - Attributes: query timestamp, budget ceiling, matched rider size, top value bike, top bargain bike, smart stretch candidate (optional), justification notes per candidate.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Decision latency: The system generates the complete top-3 recommendation podio in less than 3 seconds from query submission.
- **SC-002**: Zero false-positive listings: 0% of recommendations in the executive podio correspond to bare frames, motorized e-bikes, or liquidated/closed merchants.
- **SC-003**: Sizing fidelity: 100% of recommended offers match the user's declared size or compatible height range whenever size criteria are provided.
- **SC-004**: Actionable purchase links: 100% of recommended bikes include a direct, accessible URL pointing to the merchant's product page.
- **SC-005**: Budget compliance: 100% of candidates nominated for the primary "Best Value within Budget" position have an asking price $\le$ the user's specified budget.
- **SC-006**: Noise reduction: The executive recommendation format reduces user reading effort from over 50 rows of raw tabular data to an actionable 3-card decision summary.

## Assumptions

- The primary cycling discipline target is Gravel (drop-bar or all-road geometry for mixed asphalt and gravel terrain).
- Default rider profile defaults to height 169 cm (Size S / 50-52 cm) and territory Madrid / Spain when not explicitly provided by the user.
- Component quality hierarchy prioritizes hydraulic disc brakes and wide gear ranges (2x10/2x11/2x12 or modern 1x11/1x12 with $\ge 400\%$ gear range) as essential gravel criteria over aesthetic or brand prestige factors.
- Out-of-stock or liquidated stores (such as Tuvalum liquidation listings) must be treated as inactive stock and omitted from recommendation rankings.
- The user operates in Euros (€) in the Spanish cycling market (including domestic physical stores and European online retailers shipping to Spain).