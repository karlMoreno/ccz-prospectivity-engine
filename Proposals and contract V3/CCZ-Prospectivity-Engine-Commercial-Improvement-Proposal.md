# CCZ Prospectivity Engine
## Commercial Improvement Proposal — From Prospectivity Engine to CCZ Intelligence Platform

**Status:** Post-alpha improvement proposal  
**Purpose:** Extend the existing CCZ Prospectivity Engine into a commercially valuable decision-support and intelligence platform without disrupting the current alpha scope.  
**Intended reviewers:** Project team, Claude Code, technical advisors, geologists, prospective commercial partners.  
**Relationship to existing documents:** This proposal is additive. It does **not** replace the current *CCZ Prospectivity Engine Proposal v3* or *CCZ Prospectivity Engine Alpha Proposal v3*. The existing alpha should be completed as designed before these commercial extensions are introduced.

---

# 1. Executive Summary

The current CCZ Prospectivity Engine is technically credible because it focuses on a narrow, reproducible problem:

- assemble an open, evidence-typed CCZ abundance corpus,
- normalize heterogeneous data without conflating evidence classes,
- model polymetallic-nodule abundance,
- validate spatially,
- quantify uncertainty,
- benchmark against ISA Technical Study No. 6,
- add an economic overlay,
- publish outputs through a reproducible API/viewer.

That alpha should remain narrow.

The commercial opportunity begins **after** the alpha.

The current engine primarily answers:

> **Where does the available evidence suggest polymetallic nodules are abundant, and how uncertain is that prediction?**

A commercially mature platform should instead answer:

> **Where should an operator spend its next dollar of exploration or collection effort, what economic value could that decision create, and how confident are we?**

For financial users, the platform should answer:

> **How do geological, regulatory, operational, commodity-price, company, and financing developments change the expected value of CCZ projects and public companies?**

The proposed evolution is therefore:

```text
CCZ PROSPECTIVITY ENGINE
        │
        ▼
RESOURCE INTELLIGENCE
        │
        ▼
EXPLORATION OPTIMIZATION
        │
        ▼
ECONOMIC DECISION ENGINE
        │
        ├──────────────► OPERATIONS INTELLIGENCE
        │
        └──────────────► MARKET / INVESTMENT INTELLIGENCE
                               │
                               ▼
                    CCZ INTELLIGENCE PLATFORM
```

The objective is not to make the software "more complicated." The objective is to move it closer to decisions worth millions of dollars.

---

# 2. Commercial Thesis

A mining company is unlikely to pay millions of dollars merely for a geological heat map.

A mining company may pay substantial money for software that can demonstrate one or more of the following:

1. reduce expensive ship days,
2. reduce unnecessary sampling,
3. identify high-value survey targets,
4. prioritize exploration blocks,
5. improve resource-confidence estimates,
6. improve capital allocation,
7. optimize collection plans,
8. quantify project economics under changing commodity prices,
9. reduce uncertainty around regulatory or operational timelines,
10. combine proprietary company data with a global intelligence layer.

The key commercial transition is:

```text
FROM:
"Here is where nodules may be."

TO:
"Here is where your next survey dollar has the highest expected return."

THEN:
"Here is the optimal survey / collection plan under your budget,
risk tolerance, costs, prices, environmental constraints, and
existing proprietary observations."
```

The system becomes valuable when its recommendations can be tied to measurable economic outcomes.

---

# 3. Valuation Logic

A target strategic value of **$5 million** is plausible only if the product develops beyond a technically impressive alpha and begins demonstrating economic leverage.

A useful working framework is:

| Product State | Indicative Strategic Value |
|---|---:|
| Working Phase-3 prototype, no customers | $100K–$500K |
| Finished alpha with credible validation | $250K–$1M |
| Full CCZ intelligence platform | $1M–$3M |
| Proprietary data + demonstrated exploration savings | $3M–$10M+ |
| Recurring enterprise revenue + data moat | Potentially well above $5M |

These are strategic planning ranges, not formal appraisal values.

The core equation is simple:

\[
\text{Buyer Value} \approx \text{Expected Economic Benefit} - \text{Adoption Cost} - \text{Risk Discount}
\]

If the system can credibly save or create several million dollars per campaign, then a multimillion-dollar valuation becomes much easier to defend.

A more useful target than "make the code worth $5M" is:

> **Demonstrate that one recommendation from the platform can be worth at least $1M to a customer.**

---

# 4. Preserve the Existing Alpha

The existing alpha should remain unchanged in scope.

Do **not** pull these commercial features into the alpha before the following core outputs are working on real data:

```text
Phase-A corpus
    ↓
ingestion + normalization
    ↓
terrain features
    ↓
kriging + RF + baseline
    ↓
spatial cross-validation
    ↓
prediction + uncertainty
    ↓
TS-6 benchmark
    ↓
economic overlay
    ↓
provenance manifest
    ↓
viewer
```

The alpha's job is to prove scientific and engineering credibility.

The commercial platform should be layered on top of that stable core.

---

# 5. Proposed Product Architecture

## 5.1 High-Level Architecture

```text
+-----------------------------------------------------------------------+
|                    CCZ INTELLIGENCE PLATFORM                           |
+-----------------------------------------------------------------------+
|                           USER PRODUCTS                                |
|                                                                       |
|  +-------------------+ +-------------------+ +----------------------+  |
|  | Exploration       | | Operations        | | Markets / Investor   |  |
|  | Intelligence      | | Intelligence      | | Intelligence         |  |
|  +---------+---------+ +---------+---------+ +----------+-----------+  |
|            |                     |                      |              |
+------------+---------------------+----------------------+--------------+
             |                     |                      |
             v                     v                      v
+-----------------------------------------------------------------------+
|                        DECISION ENGINE                                 |
|                                                                       |
|  Value of Information | Monte Carlo Economics | Optimization          |
|  Scenario Engine       | NPV / P10/P50/P90     | Risk Ranking         |
+----------------------------------+------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                    PROSPECTIVITY ENGINE                                |
|                                                                       |
|  Abundance | Grade | Covariates | Uncertainty | Spatial Validation    |
|  TS-6 Benchmark | Economic Surface                                    |
+----------------------------------+------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                     CCZ KNOWLEDGE GRAPH                                |
|                                                                       |
| Company -> Area -> Resource -> Permit -> Vessel -> Technology          |
|         -> Partner -> Financing -> Event -> Economic Exposure          |
+----------------------------------+------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                  GEOSPATIAL / INTELLIGENCE DATA LAKE                   |
|                                                                       |
| Open Observations | Customer Data | Regulatory | Commodity Prices      |
| Vessel Data | Company Filings | Environmental | Derived Features       |
+-----------------------------------------------------------------------+
```

---

# 6. Improvement 1 — Active Exploration Planner

## 6.1 Why This Is the Highest-Priority Commercial Feature

The existing uncertainty surface should be turned into a decision tool.

Instead of merely asking:

\[
P(\text{abundance} \mid \text{available data})
\]

the platform should ask:

\[
\boxed{\text{Where should we sample next?}}
\]

Every candidate survey or sampling location should receive a **Value of Information** score.

A first formulation:

\[
VOI(x) =
\frac{
E[\Delta U_{\text{economic}} \mid \text{sample at } x]
}{
C_{\text{survey}}(x)
}
\]

Where:

- \(x\) = candidate sampling or survey location,
- \(\Delta U_{\text{economic}}\) = expected reduction in economically relevant uncertainty,
- \(C_{\text{survey}}(x)\) = expected marginal cost of reaching and sampling that location.

The initial implementation does not need to solve the full expedition-routing problem.

Version 1 can rank candidate locations by:

1. model uncertainty,
2. distance from existing observations,
3. predicted abundance,
4. expected effect on economic classification,
5. sampling cost proxy.

## 6.2 Example Output

```text
NEXT BEST SURVEY TARGETS

Rank  Location          Information Gain   Cost Proxy   VOI Score
-----------------------------------------------------------------
1     12.41,-128.22     Very High          Medium       9.2
2     12.51,-128.08     High               Low          7.8
3     12.17,-128.39     High               Low          6.9
4     11.92,-128.01     Medium             Very Low     5.1
```

## 6.3 Commercial Value

This feature provides a direct pathway to quantifiable savings:

```text
fewer unnecessary ship days
        +
fewer low-value box cores
        +
better AUV transect placement
        +
faster reduction of resource uncertainty
        =
MEASURABLE EXPLORATION SAVINGS
```

---

# 7. Improvement 2 — Full Economic Decision Engine

The alpha economic layer is intentionally simple.

The commercial system should evolve from a threshold-based "minable/not-minable" surface into a probabilistic economic model.

For each cell \(i\):

\[
EV_i =
P_i
\left[
R_i
\sum_m
\left(
M_{im}
\times G_{im}
\times Recovery_m
\times Price_m
\right)
-
C_i
\right]
\]

Where:

- \(P_i\) = probability/confidence adjustment,
- \(R_i\) = recoverable resource factor,
- \(M_{im}\) = estimated nodule or metal-bearing mass,
- \(G_{im}\) = grade of metal \(m\),
- \(Recovery_m\) = processing recovery for metal \(m\),
- \(Price_m\) = price scenario for metal \(m\),
- \(C_i\) = expected collection + logistics + processing cost.

The economic model should produce:

```text
Expected Value
P10
P50
P90
Break-even commodity price
Break-even recovery rate
Expected cost per recoverable tonne
Expected value per km²
Economic sensitivity by metal
```

## 7.1 Monte Carlo Scenarios

The engine should simulate uncertainty in:

- nodule abundance,
- grade,
- recovery,
- metal prices,
- collection efficiency,
- vessel costs,
- processing costs,
- project delays,
- permit timing.

Output:

```text
Project NPV
P10:  $...
P50:  $...
P90:  $...

Probability NPV > 0: ...
Probability IRR > target: ...
Most sensitive variables:
1. Nickel price
2. Collection efficiency
3. Permit date
4. Nodule abundance
```

---

# 8. Improvement 3 — Expedition Optimization

Once the Value-of-Information engine exists, optimize an entire exploration campaign.

## 8.1 Inputs

```text
Budget
Ship cost/day
Available mission days
Number of box cores
AUV hours
Transit speed
Weather allowance
Target commodity
Risk tolerance
Existing observations
Environmental exclusions
Required confidence threshold
```

## 8.2 Objective

A simplified objective:

\[
\max_{\pi}
\left[
E[\text{information gain from campaign } \pi]
-
\lambda C(\pi)
\right]
\]

subject to:

\[
\text{Mission Duration}(\pi) \leq D
\]

\[
\text{Campaign Cost}(\pi) \leq B
\]

\[
\text{Samples}(\pi) \leq N
\]

where:

- \(\pi\) = proposed expedition plan,
- \(D\) = available days,
- \(B\) = budget,
- \(N\) = available sampling actions.

## 8.3 Example User Experience

```text
OPTIMIZE EXPLORATION CAMPAIGN

Budget:              $8,000,000
Ship cost/day:       $150,000
Mission duration:    31 days
Box cores:           120
AUV hours:           350
Primary target:      Nickel
Risk tolerance:      Moderate
```

Output:

```text
RECOMMENDED EXPEDITION

Survey Zone 14 first.
Deploy 27 box cores.
Run AUV transect A -> F.
Skip Zones 19 and 21.

Expected information gain:      +38%
Expected resource uncertainty:  -31%

Probability target exceeds
economic cutoff:                72% -> 89%

Estimated avoidable survey cost:
$2.1M
```

This is potentially the strongest direct enterprise sales feature.

---

# 9. Improvement 4 — Collection / Mine-Plan Optimization

After exploration optimization comes production optimization.

The platform should model:

- collector speed,
- collection width,
- collection efficiency,
- nodule abundance,
- seafloor slope,
- exclusion zones,
- sediment / terrain constraints,
- riser constraints,
- vessel throughput,
- production targets,
- maintenance windows,
- weather downtime.

Objective:

\[
\max_{\pi}
\sum_{i \in \pi}
\left(
Revenue_i - Cost_i
\right)
\]

subject to operational constraints.

Example:

```text
YEAR 1 COLLECTION PLAN

Block A
    ↓
Block C
    ↓
Block F

Predicted recovered nodules:  3.12 Mt
Expected Ni:                 ...
Expected Cu:                 ...
Expected Co:                 ...

Expected revenue:            ...
Expected offshore cost:      ...
Expected margin:             ...

P10 NPV:                     ...
P50 NPV:                     ...
P90 NPV:                     ...
```

This feature moves the platform from exploration software toward operational planning software.

---

# 10. Improvement 5 — Private Customer Data Layer

The current open-data strategy is a major credibility advantage.

It should remain public-facing.

However, commercial users need a private data layer.

```text
PUBLIC DATA
     +
GLOBAL DERIVED FEATURES
     +
CUSTOMER PROPRIETARY DATA
     +
CUSTOMER-SPECIFIC ASSUMPTIONS
     ↓
PRIVATE CUSTOMER MODEL
```

Potential customer inputs:

- box-core data,
- grab samples,
- AUV imagery,
- OFOS observations,
- grade assays,
- bathymetry,
- collector-test results,
- vessel logs,
- processing assumptions,
- private economic cutoffs.

The system should guarantee:

```text
Customer A data -> Customer A model only
Customer B data -> Customer B model only
Public model     -> shared global layer
```

The commercial moat becomes:

```text
software
    +
historical derived features
    +
model calibration history
    +
customer integrations
    +
proprietary observations
```

not merely the codebase.

---

# 11. Improvement 6 — CCZ Knowledge Graph

The platform should represent important CCZ entities and relationships explicitly.

## 11.1 Core Entities

```text
Company
ContractArea
ExplorationLicense
ResourceEstimate
GovernmentSponsor
Permit
Application
Vessel
CollectorSystem
ProcessingPartner
TechnologyProvider
EnvironmentalStudy
FinancingRound
Commodity
CommodityPrice
Event
Publication
Dataset
```

## 11.2 Example Relationship Graph

```text
Company
  |
  +-- controls ------> Contract Area
  |
  +-- submitted -----> Permit Application
  |
  +-- partnered -----> Technology Provider
  |
  +-- financed by ---> Investor
  |
  +-- operates ------> Vessel
  |
  +-- depends on ----> Processing Partner
  |
  +-- exposed to ----> Commodity
  |
  +-- affected by ---> Regulatory Event
```

This graph should become the bridge between geology and markets.

---

# 12. Improvement 7 — Event Intelligence Engine

The platform should continuously ingest public events from sources such as:

```text
ISA
NOAA
SEC filings
Company announcements
Government notices
Academic publications
Environmental filings
Commodity markets
Patents
Vessel / AIS intelligence
Exploration announcements
Financing announcements
Technology partnerships
Processing partnerships
```

An event should not merely appear in a news feed.

It should flow into affected entities and models.

Example:

```text
REGULATORY EVENT
        |
        v
Permit probability changes
        |
        v
Expected production date changes
        |
        v
Project discounting changes
        |
        v
Risk-adjusted NPV changes
        |
        v
Investor alert generated
```

---

# 13. Improvement 8 — Investor / Quant Product

A separate product should be created for investors, commodity analysts, strategic capital, and possibly government users.

## 13.1 Core Model

\[
NPV =
f(
Ni,
Co,
Cu,
Mn,
Resource,
Grade,
Recovery,
CAPEX,
OPEX,
PermitProbability,
ProductionDate
)
\]

Users should be able to ask:

```text
What happens if nickel falls 20%?

Which company has the greatest cobalt exposure?

Which project gains the most value if manganese prices increase 30%?

What does a 12-month permit delay do to risk-adjusted NPV?

Which company is most exposed to collector-system failure?

Which projects are most sensitive to financing costs?
```

## 13.2 Historical Backtesting

Every model-changing event should be timestamped.

This permits backtesting:

```text
Event
  ↓
Model state before event
  ↓
Model state after event
  ↓
Public market reaction
  ↓
Was the signal useful?
```

This is essential if the platform is eventually marketed to quantitative or event-driven investors.

---

# 14. Improvement 9 — Remote and Operational Intelligence

Future versions can add:

- AIS vessel tracking,
- satellite imagery,
- port calls,
- expedition detection,
- vessel loiter analysis,
- survey-pattern recognition,
- reported vs observed activity,
- weather and sea-state data,
- bathymetric campaign changes,
- AUV deployment patterns.

This should be treated as an intelligence layer, not a replacement for actual geological sampling.

Potential output:

```text
Observed Activity
       +
Company Disclosures
       +
Known Contract Areas
       +
Vessel Behavior
       ↓
Operational Activity Estimate
```

---

# 15. Closed-Loop Product Vision

The strongest long-term version of the product is closed-loop.

```text
+------------------+
|     PREDICT      |
+--------+---------+
         |
         v
+------------------+
| OPTIMIZE SURVEY  |
+--------+---------+
         |
         v
+------------------+
|     COLLECT      |
+--------+---------+
         |
         v
+------------------+
|      INGEST      |
+--------+---------+
         |
         v
+------------------+
|   UPDATE MODEL   |
+--------+---------+
         |
         v
+------------------+
| UPDATE ECONOMICS |
+--------+---------+
         |
         v
+------------------+
| OPTIMIZE AGAIN   |
+--------+---------+
         |
         +--------------------+
                              |
                              +-------> back to PREDICT
```

The customer continuously improves its private model by using the platform.

This creates switching costs and data-network effects.

---

# 16. Proposed Post-Alpha Roadmap

| Phase | Build | Commercial Purpose |
|---|---|---|
| Alpha 0–5 | Finish current proposal | Scientific credibility |
| 6 | Path B/C + Option-B proxies | Better predictions |
| 7 | Grade surfaces + metal-price economics | Resource valuation |
| 8 | Monte Carlo economics / P10-P50-P90 | Investment decisions |
| 9 | Value-of-Information exploration optimizer | Save survey money |
| 10 | Private customer-data ingestion | Enterprise deployment |
| 11 | Campaign / expedition optimization | Save exploration money |
| 12 | Collection / mine-plan optimizer | Save operating money |
| 13 | CCZ knowledge graph | Integrate market intelligence |
| 14 | Event intelligence engine | Real-time decision updates |
| 15 | Company/project valuation models | Investor product |
| 16 | Alerts + API + backtesting | Financial terminal |
| 17 | AIS / satellite / operational feeds | Intelligence moat |
| 18 | Proprietary partner datasets | Data moat |

---

# 17. Recommended Priority Order

Do **not** build every feature simultaneously.

Recommended sequence:

```text
1. Finish alpha
      ↓
2. Improve geological signal
      ↓
3. Build real economics
      ↓
4. Build Value-of-Information ranking
      ↓
5. Build expedition optimizer
      ↓
6. Add private customer data
      ↓
7. Obtain first pilot customer
      ↓
8. Demonstrate real savings
      ↓
9. Expand to operational planning
      ↓
10. Add financial / intelligence terminal
```

The first major commercial objective should be:

> **Produce a pilot showing that the engine can change an exploration decision in a way that has measurable expected economic value.**

---

# 18. Product Packaging

## 18.1 Product A — Exploration Intelligence

Target users:

- seabed mining companies,
- exploration teams,
- resource geologists,
- strategic-mineral programs,
- government geological organizations.

Capabilities:

```text
Prospectivity
Uncertainty
Grade
Economic value
Sample targeting
Campaign optimization
Private-data integration
Scenario analysis
```

Possible pricing:

```text
Pilot:
$25K–$100K

Annual team license:
$100K–$300K+

Enterprise:
$250K–$1M+ depending on integration and private data

Bespoke campaign analysis:
$50K–$250K+
```

The important objective is not choosing exact pricing today. It is ensuring the product creates enough customer value to support enterprise pricing.

---

# 19. Product B — CCZ Markets Intelligence

Target users:

- hedge funds,
- commodity investors,
- mining analysts,
- strategic investors,
- consulting firms,
- governments,
- critical-mineral policy teams.

Capabilities:

```text
Company / project knowledge graph
Event tracking
Permit timelines
Resource / economics models
Commodity sensitivity
Risk-adjusted project NPV
Company exposure
Alerts
Historical backtesting
API
```

Possible pricing:

```text
Individual analyst:
$5K–$20K/year

Professional team:
$25K–$100K/year

Institutional API / enterprise:
$100K–$500K+/year
```

---

# 20. Data Moat Strategy

Open data should establish credibility.

Proprietary derived information should create defensibility.

A useful ladder is:

```text
LEVEL 1
Raw public data

LEVEL 2
Normalized evidence-typed corpus

LEVEL 3
Derived terrain / geological features

LEVEL 4
Validated prospectivity surfaces

LEVEL 5
Economic surfaces

LEVEL 6
Historical event graph

LEVEL 7
Model calibration history

LEVEL 8
Customer private observations

LEVEL 9
Observed outcome / prediction-performance history
```

The highest-value asset may eventually be the **history of predictions versus subsequent observations**, not any individual algorithm.

---

# 21. Commercial Proof Requirements

Before claiming a multi-million-dollar valuation, the project should demonstrate several of the following:

## 21.1 Scientific Proof

```text
[ ] Spatial CV beats baseline
[ ] Predictions remain calibrated out-of-sample
[ ] Uncertainty is empirically meaningful
[ ] Grade / abundance joins are defensible
[ ] TS-6 comparison is understood
[ ] Prediction errors are geologically interpretable
```

## 21.2 Operational Proof

```text
[ ] Optimizer produces stable recommendations
[ ] Recommendations respond correctly to budget constraints
[ ] Recommendations respond correctly to new observations
[ ] Route / campaign costs are modeled realistically
[ ] Environmental exclusions are enforced
```

## 21.3 Commercial Proof

```text
[ ] At least one industry expert validates the workflow
[ ] At least one operator provides real decision requirements
[ ] At least one pilot uses private or customer-provided data
[ ] A recommendation changes an actual or historical decision
[ ] Economic savings / value can be estimated
[ ] Customer expresses willingness to pay
```

## 21.4 Data-Moat Proof

```text
[ ] Derived corpus is difficult to recreate manually
[ ] New data can be integrated rapidly
[ ] Customer data can remain private
[ ] Model outputs improve as observations accumulate
[ ] Prediction history is versioned and auditable
```

---

# 22. Key Metrics

The commercial platform should track more than model RMSE.

## Model Metrics

```text
Spatial CV RMSE
Spatial CV MAE
Calibration
Coverage of prediction intervals
Baseline uplift
TS-6 agreement
```

## Exploration Metrics

```text
Expected uncertainty reduction per sample
Expected uncertainty reduction per dollar
Expected economic reclassification per sample
Number of avoided low-value samples
Estimated ship days avoided
```

## Customer Metrics

```text
Pilot conversion rate
Annual contract value
Retention
Number of private datasets integrated
Number of decisions informed
Estimated value created
```

## Intelligence Metrics

```text
Event detection latency
Entity-linking accuracy
Valuation update latency
Historical signal quality
Backtested event performance
```

---

# 23. Architectural Principles

Commercial expansion should preserve the strongest design qualities already present in the project.

## 23.1 Strategy Pattern

Existing strategy interfaces should expand rather than be replaced.

Potential additions:

```text
ExplorationOptimizer
EconomicScenarioModel
CostModel
CommodityPriceSource
ProjectValuationModel
EventImpactModel
CollectionOptimizer
CustomerDataSource
```

## 23.2 Adapter Pattern

Every new external source should continue to use adapters.

```text
ISAEventAdapter
NOAAEventAdapter
SECCompanyAdapter
CommodityPriceAdapter
AISAdapter
CustomerObservationAdapter
```

## 23.3 Event-Sourced Intelligence

For regulatory / company intelligence, preserve historical state transitions.

Example:

```text
CompanyState(t0)
      |
      +-- Event A
      |
      v
CompanyState(t1)
      |
      +-- Event B
      |
      v
CompanyState(t2)
```

This allows historical backtesting and model reproducibility.

## 23.4 Explicit Scenario Objects

Economic and financial assumptions must never be hidden globals.

```text
Scenario
├── commodity_prices
├── capex
├── opex
├── recovery_rates
├── permit_probability
├── discount_rate
├── production_start
├── collector_efficiency
└── risk_parameters
```

Every result should identify exactly which scenario produced it.

---

# 24. Suggested Domain Model Expansion

```text
Observation
TerrainLayer
ProxyLayer
PredictionResult
EconomicScenario
TS6Reference
ProvenanceManifest

        +
        |
        v

ExplorationTarget
SurveyAction
SurveyCampaign
SurveyCostModel
ValueOfInformationResult

ResourceBlock
GradeEstimate
EconomicCell
ProjectEconomicScenario
MonteCarloRun

Company
ContractArea
Permit
RegulatoryEvent
TechnologySystem
Vessel
ProcessingPartner
FinancingEvent

MarketScenario
CommodityPriceSeries
CompanyValuation
ProjectValuation

CustomerWorkspace
PrivateDataset
CustomerModelRun
```

---

# 25. Repository Direction

A possible future repository organization:

```text
ccz-intelligence-platform/
├── core/
│   ├── ingestion/
│   ├── prospectivity/
│   ├── validation/
│   ├── uncertainty/
│   ├── economics/
│   └── provenance/
│
├── exploration/
│   ├── voi/
│   ├── campaign_optimizer/
│   ├── cost_models/
│   └── routing/
│
├── operations/
│   ├── collection_optimizer/
│   ├── production_models/
│   └── logistics/
│
├── intelligence/
│   ├── knowledge_graph/
│   ├── events/
│   ├── regulatory/
│   ├── companies/
│   └── vessels/
│
├── markets/
│   ├── commodity_prices/
│   ├── project_valuation/
│   ├── company_valuation/
│   ├── backtesting/
│   └── alerts/
│
├── customer/
│   ├── workspaces/
│   ├── private_data/
│   ├── access_control/
│   └── model_isolation/
│
├── services/
│   ├── api/
│   ├── worker/
│   └── scheduler/
│
├── apps/
│   ├── exploration-terminal/
│   └── markets-terminal/
│
└── data/
    ├── public/
    ├── derived/
    ├── customer_private/
    ├── intelligence/
    └── manifests/
```

This is a **future target**, not a recommendation to restructure the alpha immediately.

---

# 26. "$5M Feature" Candidate

The highest-value near-term feature is likely:

> ## Optimize Exploration Campaign

Because it directly converts model outputs into cost-saving decisions.

Input:

```text
Budget
Ship-day cost
Mission duration
Sampling inventory
AUV availability
Existing observations
Target commodities
Risk tolerance
Environmental constraints
```

Output:

```text
Recommended sampling sequence
Recommended AUV transects
Recommended zones to skip
Expected uncertainty reduction
Expected probability of economic success
Expected campaign cost
Estimated cost avoided
Expected value of additional information
```

If the system can credibly show:

```text
"Following this recommendation would have avoided
approximately $1M–$3M of low-value exploration effort."
```

then the commercial proposition changes materially.

---

# 27. Main Risks

## Risk 1 — Open data is insufficient for commercial-grade prediction

Mitigation:

- preserve uncertainty,
- add Phase B/C,
- seek partnerships,
- support private-data ingestion,
- distinguish public benchmark quality from customer-private model quality.

## Risk 2 — Economic assumptions dominate geological predictions

Mitigation:

- scenario-based economics,
- sensitivity analysis,
- Monte Carlo modeling,
- visible assumptions,
- separate geological uncertainty from market uncertainty.

## Risk 3 — Optimizer creates false precision

Mitigation:

- expose objective function,
- expose cost assumptions,
- return confidence / sensitivity,
- allow multiple optimization strategies,
- compare against simple baselines.

## Risk 4 — Customers will not share proprietary data

Mitigation:

- isolated workspaces,
- customer-owned encryption keys where practical,
- no cross-customer training by default,
- explicit data-retention controls,
- ability to deploy in a customer-controlled environment later.

## Risk 5 — Mining market remains politically or commercially delayed

Mitigation:

- financial / government intelligence product,
- critical-mineral research customers,
- reusable geospatial decision engine,
- maintain portability to adjacent seabed and terrestrial resource problems.

## Risk 6 — Product becomes too broad

Mitigation:

```text
Finish alpha
    ↓
prove exploration value
    ↓
obtain pilot
    ↓
only then expand
```

---

# 28. Go-To-Market Sequence

Recommended initial sequence:

```text
1. Finish public alpha.
2. Publish methodology and benchmark.
3. Create a 10-minute operator demo.
4. Identify 5–10 domain experts / operators.
5. Interview them about their actual exploration workflow.
6. Build Value-of-Information prototype.
7. Reconstruct a historical campaign if possible.
8. Ask: "Would this recommendation have changed your plan?"
9. Quantify hypothetical savings.
10. Seek one paid or design-partner pilot.
```

The first customer does not need to buy the whole platform.

The first customer needs to validate one expensive decision.

---

# 29. Questions for Claude Code

Please review the existing alpha and this proposal as a senior software architect and challenge the plan.

Specifically answer:

## Architecture

1. Which commercial features can be added cleanly to the existing architecture without restructuring the alpha?
2. Which existing abstractions are too narrow for the proposed future product?
3. Should the prospectivity engine remain a modular package inside a larger monorepo, or eventually become a service?
4. Where should domain boundaries be drawn between:
   - prospectivity,
   - economics,
   - exploration optimization,
   - operations optimization,
   - market intelligence,
   - customer-private data?
5. Which modules should remain pure deterministic libraries versus services?

## Data Model

6. Does the proposed domain expansion create any problematic coupling?
7. How should versioned public observations and private customer observations coexist?
8. How should model-input provenance be represented so every recommendation remains reproducible?
9. Should the intelligence/event system use event sourcing?
10. Would a graph database materially help, or should relationships remain relational initially?

## Optimization

11. What is the simplest credible implementation of the Value-of-Information engine?
12. What baseline should be used to prove that the optimizer adds value?
13. How should campaign optimization be separated from geological prediction?
14. Should routing / scheduling use:
    - OR-Tools,
    - mixed-integer programming,
    - heuristic search,
    - reinforcement learning,
    - another method?
15. What should be postponed until actual customer constraints are known?

## Economics

16. How should uncertainty propagate from abundance -> grade -> recovery -> price -> NPV?
17. Should Monte Carlo simulation live in the engine or in a separate economics package?
18. How should scenario objects be versioned and validated?
19. What outputs are necessary to avoid false precision?

## Security / Enterprise

20. What architecture is appropriate for isolated customer workspaces?
21. What changes would be required for a customer-controlled / on-prem deployment?
22. Which data should never leave the customer's environment?
23. How should API authorization be structured before accepting private data?

## Commercial Scope

24. Which proposed feature is most likely to create measurable enterprise value fastest?
25. Which features look impressive but should **not** be built yet?
26. What would you cut from this roadmap?
27. What would you add?
28. What technical milestone would make you believe this project could reasonably justify a multi-million-dollar strategic valuation?

## Final Request

Please return:

```text
1. Major strengths
2. Major weaknesses
3. Architectural risks
4. Features to cut
5. Features to accelerate
6. Recommended post-alpha architecture
7. Recommended next 3 phases
8. Specific codebase refactors, if any
9. Missing technical contracts
10. Overall verdict
```

Do not assume the commercial thesis is correct. Challenge it aggressively.

---

# 30. Final Recommendation

The current alpha should remain a **scientifically honest, narrowly scoped prospectivity engine**.

The commercial extension should focus first on one transformation:

\[
\boxed{
\text{Prediction}
\rightarrow
\text{Decision}
\rightarrow
\text{Measured Economic Value}
}
\]

The most important post-alpha feature is therefore not another model.

It is:

\[
\boxed{
\text{Value-of-Information Exploration Optimization}
}
\]

because that directly connects:

```text
geological uncertainty
        +
survey cost
        +
economic potential
        ↓
recommended next action
```

Once that loop works, private customer data, campaign optimization, collection planning, market intelligence, event tracking, and investor analytics can all grow around the same core.

The long-term goal should not be to sell a map.

It should be to build the software layer through which CCZ participants decide:

> **where to explore, where to spend, where to collect, what a project is worth, and how new information changes those decisions.**
