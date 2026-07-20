# The Evacuation Inform Index (EII)

### A Research Report on a Decision Support Tool for Weighing the Risk of Leaving Against the Risk of Staying

*Prepared as a plain language review of the EII research prototype*
*based on the software and documentation contained in this repository*

---

## Foreword

Every displacement crisis contains a question that is rarely asked out loud: is leaving actually safer than staying? Humanitarian practice tends to treat evacuation as the obvious good, the thing that rescues people from harm. In practice the journey itself carries risk. Roads are mined or blockaded. Checkpoints separate families. The elderly and the sick do not survive transit that a healthy adult would manage. A destination that looked open on Monday has closed by Thursday.

The Evacuation Inform Index, known as EII, is a research prototype that treats that question as the object of measurement. It does not tell anyone to move or to stay. It scores the two risks separately, side by side, so that the comparison between them becomes visible and can be argued with.

This report explains what the tool is, what it measures, where its numbers come from, and where its authors have marked the boundaries of what it can support. It is written for a policy, humanitarian, and legal readership rather than a technical one. Readers looking for the software itself will find it in the same repository as this document.

---

## 1. Executive Summary

1.1 The EII is an interactive web application that scores 104 active humanitarian crises on two dimensions: the risk of remaining in place, and the risk of attempting to leave. It expresses the relationship between them as a single ratio, while always displaying the two component scores that produced it.

1.2 The scores are not invented for the prototype. They are derived from the INFORM Severity Index, the monthly crisis severity model produced by ACAPS with the Joint Research Centre of the European Commission. The April 2026 release provides the live backbone, covering 104 crises.

1.3 A second analytical layer, adapted from the Civilian Evacuation Risk Anticipation Index (CERAI), keeps two ideas deliberately apart: how dangerous a situation is, and how practical it is to move people out of it. Collapsing those into one number would let operational difficulty quietly cancel out legal obligation. The tool refuses that collapse.

1.4 Live feeds supplement the monthly baseline. Conflict event data comes from ACLED, recent developments from news retrieval, and route weather from Open-Meteo. An optional satellite damage overlay can be connected if the user runs Microsoft HASTE themselves.

1.5 The prototype is explicit that its weights are researcher estimates awaiting expert validation, that its endangerment and feasibility measures are architectural proxies rather than validated instruments, and that no independent ground truth for evacuation decisions exists against which it could be calibrated. Section 9 sets out these limits in full.

1.6 The intended use is to direct attention, not to issue verdicts. A human decision maker retains the call.

---

## 2. The Problem the Index Addresses

2.1 Existing humanitarian indices measure how bad a situation is. They rank crises by severity so that funding and attention can be allocated. What they do not do is model the alternative. A crisis scored as extremely severe tells a planner that people are suffering; it does not tell them whether moving those people would reduce or increase the harm.

2.2 That gap matters because the two risks move independently. A siege can be catastrophic to endure and simultaneously impossible to escape. A drought can be survivable in place while the routes out remain open and safe. Treating severity as a proxy for "should evacuate" conflates conditions that need to be distinguished.

2.3 International humanitarian law makes the distinction consequential rather than merely analytical. Under Article 49 of the Fourth Geneva Convention, an Occupying Power may undertake total or partial evacuation of a given area where the security of the population or imperative military reasons so demand, must return those evacuated to their homes once hostilities in the area have ceased, and must ensure proper accommodation, satisfactory conditions of hygiene, health, safety and nutrition, and that members of the same family are not separated. Evacuation is therefore a regulated act with conditions attached, not a self evidently benign one.

2.4 The prototype's response is to score staying and leaving as two separate quantities and to publish both.

---

## 3. What the Index Is

3.1 The EII is a browser based application. It consists of a world map of active crises, a panel of live developments per crisis, a methodology section, a catalogue of data sources, and a reference list. It runs against a small local server when live data is wanted, and falls back to a stored set of captured responses when hosted as a static site.

3.2 It is a research prototype. It is not deployed in any operational setting, has no institutional mandate, and produces no output that any organisation is obliged to act upon.

3.3 The repository contains the full methodology, including the parts that are designed but not yet built. The distinction between what is implemented and what is planned is marked throughout the interface rather than left to the reader to infer.

---

## 4. How the Index Works

### 4.1 The central ratio

The index expresses its result as a ratio: the Risk Score for Evacuating divided by the Risk Score for Staying.

A value above 1.0 indicates that evacuation carries more risk than remaining. A value below 1.0 indicates the reverse. A value near 1.0 indicates that the two courses of action carry comparable risk, which is itself a meaningful finding rather than an absence of one.

Two safeguards apply. Ratios become unstable as the denominator approaches zero, so a floor of 0.5 on a five point scale is applied to the staying score. And the ratio is never shown alone: both component scores accompany it wherever it appears.

### 4.2 The live data backbone

The two component scores are drawn from the INFORM Severity Index rather than constructed independently.

INFORM assembles 31 core indicators into three weighted dimensions: the impact of the crisis at 20 per cent, the conditions of the affected people at 50 per cent, and the complexity of the situation at 30 per cent. ACAPS describes these weights as a current best estimate to be refined by expert analysis and statistical methods, which places the EII's own provisional weighting in familiar company.

The EII maps two of those dimensions onto its own question:

| INFORM dimension | Becomes | Represents |
|---|---|---|
| Conditions of affected people | Risk Score for Staying | How severe it is to remain in place |
| Complexity of the crisis (access constraints, society and safety, operating environment) | Risk Score for Evacuating | How difficult and dangerous it is to move |

Both are rescaled from the INFORM ten point scale to the five point scale the EII uses.

The choice is defensible on its face. Complexity in INFORM measures precisely the conditions that obstruct movement: humanitarian access, safety of operations, and the operating environment. It is nonetheless a substitution, and the prototype labels it as one.

### 4.3 The three layer architecture

The fuller design, of which the live build implements the first layer, divides the problem into three:

| Layer | Weight | Function | Precedent |
|---|---|---|---|
| Objective Risk Score | 50 per cent | Universal factors identical for everyone in the geography: active hostilities, likelihood of future hostility, life risk from natural hazards | INFORM Severity, ACLED, Global Conflict Risk Index |
| Infrastructure and Access | 35 per cent | Availability of routes, resources, and connectivity | ACAPS Humanitarian Access, IDMC |
| Personal Vulnerability Modifier | 15 per cent | Household and demographic factors applied as a multiplier rather than an addition | CDC Social Vulnerability Index, IOM RICD |

Within the first layer, active hostilities carry the heaviest weight at 20 per cent on the reasoning that they represent the most immediate and fastest changing threat to life. Forward looking hostility risk and non conflict life risk take 15 per cent each. Within the second, route availability leads at 12 per cent, followed by infrastructure availability at 10 per cent, security alerts at 8 per cent, and weather at 5 per cent.

The third layer is deliberately multiplicative. A personal characteristic does not add a fixed quantity of risk; it scales the risk already present in the environment. Being elderly in a stable region and being elderly under bombardment are not the same increment.

### 4.4 Why the parts are multiplied rather than averaged

Indicators combine by weighted geometric mean rather than arithmetic mean. The practical consequence is that a catastrophic score on one component cannot be averaged away by comfortable scores elsewhere. If every evacuation route is closed, no amount of favourable weather or food security compensates for it.

This is the same non compensatory logic used by the Human Development Index and by INFORM Risk. It reflects a judgement about the world rather than a mathematical preference: some failures are absolute.

---

## 5. The CERAI Lens: Keeping Danger and Feasibility Apart

5.1 The prototype adopts a structural argument from the CERAI framework, which holds that danger and feasibility must never be collapsed into one score.

5.2 The reasoning is legal as much as analytical. The obligation to protect civilians arises from the danger they face. Operational difficulty does not extinguish that obligation. A single blended number would allow low feasibility to drag down the composite, making a desperate situation appear less urgent precisely because it is hard to resolve. Keeping the two visible produces the opposite effect: high danger combined with low feasibility becomes a signal that the problem has moved beyond operational reach and requires political engagement.

5.3 The tool renders the split live for each crisis.

| Dimension | Question it answers | How the prototype computes it |
|---|---|---|
| Endangerment | How dangerous is it to stay? | INFORM Conditions expressed as a percentage, with a 75 per cent obligation threshold marked, and a trajectory drawn from recent ACLED fatality trends |
| Feasibility | Can civilians realistically move? | INFORM Complexity inverted and expressed as a percentage, reduced by live route weather from Open-Meteo |
| Protection gap flag | Where is escalation needed? | Raised when endangerment is at or above 75 per cent while feasibility is at or below 40 per cent |

5.4 Endangerment is banded for readability: manageable, elevated, severe, extreme, and critical, with critical reserved for scores at or above 90 per cent.

5.5 The trajectory indicator compares ACLED fatalities in the most recent three months against the preceding three months. It answers whether a situation is deteriorating or stabilising, which a static severity score cannot convey.

### 5.6 The vulnerability profile

A crisis score describes a population. It does not describe a person within it. The prototype therefore offers an interactive profile of twelve factors that a user can switch on to represent a particular group.

Each factor shifts a multiplier by 0.06, bounded between 0.7 and 1.3. The multiplier raises endangerment and lowers feasibility, on the reasoning that these are two causally distinct pathways rather than one effect measured twice.

The twelve factors extend well beyond mobility. Young children, the elderly, the disabled and medically dependent, the wounded and acutely sick, and pregnant women and new mothers all bear on the physical capacity to travel. Unaccompanied and separated minors, people facing gendered violence risk, members of targeted ethnic, religious or political groups, undocumented people with identity gaps, and linguistic minorities with low literacy face a different kind of exposure: they are endangered by targeting, detention, or exclusion rather than by the difficulty of walking. Two factors work in the opposite direction, reducing assessed risk: prior evacuation experience and available financial resources.

The distinction matters. A demographic list alone would treat vulnerability as a question of who moves slowly. The protection based additions treat it as a question of who is hunted, who is turned back, and who cannot read the sign telling them where to go.

---

## 6. What a User Sees

6.1 The map presents all 104 crises as markers scaled and coloured by whichever measure the user selects: the ratio itself, the risk of staying, or the risk of evacuating. Selecting a crisis opens a panel with the full breakdown.

6.2 The live panel provides, for each crisis, recent developments retrieved from news sources and a structured conflict timeline from ACLED, with every item linked to its primary source. The time window is adjustable from thirty days to twelve months.

6.3 The methodology section carries the material summarised in sections 4 and 5 of this report, together with the variable tables and their proposed weights.

6.4 The data sources section catalogues eighteen feeds with their update frequency and cost, distinguishing those in use from those on the roadmap and marking which require payment.

6.5 The references section lists the methodological precedents and the academic literature the design draws on.

6.6 The map also supports high resolution satellite imagery, daily NASA imagery layers, and an optional damage assessment overlay described in section 7.

---

## 7. Evidence, Provenance, and the Treatment of Uncertainty

7.1 The laboratory hosting this work has a lineage in supply chain traceability and forced labour mitigation, and several practices carry over from that domain into how this index treats evidence.

7.2 A two witness standard, adapted from the FLARE model developed by the Global Fund to End Modern Slavery, separates a fact corroborated by two or more independent reports from a single unverified claim. This sharpens source credibility into a graded ladder rather than a binary.

7.3 The score is deterministic rather than generated. Every number the tool produces comes from a fixed, auditable formula. Where a language model is involved, it supplies source grounded facts and never overrides the arithmetic. A reader can reconstruct any score by hand.

7.4 An evidence gap is treated as a risk signal rather than a neutral absence. An unverified corridor segment is penalised, not assumed safe. This inverts the common default in which missing information quietly reads as an acceptable situation.

7.5 Where the tool falls back to background knowledge rather than a live verified source, that fallback is labelled, capped below verified status, and flagged. Absence of verification never presents itself as verification.

7.6 The prototype states plainly which methods it has not implemented. It does not use the eleven forced labour indicators of the International Labour Organization, machine learning classifiers, or cryptographically signed credentials. Those belong to the models cited as design lineage and are not claimed as features here.

7.7 The satellite damage layer follows the same discipline. Microsoft HASTE, developed with Planet, converts satellite imagery into building and route damage maps. It has no public interface and must be self hosted, so the overlay stays empty until a user connects their own deployment. The interface reports the real state of that connection: it requests tiles, turns green only when tiles actually arrive, reports failure when none do, and distinguishes partial coverage from failure, since a damage layer legitimately returns nothing outside its project area. Nothing about the connection is asserted before it is observed.

---

## 8. Inheritance from Sibling Projects

8.1 The index draws structures from several related evacuation projects within the same organisation, and marks each as either incorporated or planned.

8.2 Incorporated: the protection based vulnerable group categories described in section 5.6, each carrying a basis in international humanitarian law; and the non compensatory geometric aggregation with its floor on the staying score.

8.3 Planned: destination readiness gatekeepers, under which a confirmed refusal by a host authority would cap feasibility outright rather than merely reducing it; a seven dimension decomposition that would replace the current single score inputs with scored sub dimensions; and corridor and checkpoint dynamics covering exit gates, ceasefire windows, congestion, siege conditions, and degradation of the information environment.

8.4 A calibration harness from a sibling project, fitted to sixteen historical cases, contributes something other than a number. Its documented failure modes, in which the model is declared out of scope for genocide, large enclave precision operations, and sieges beyond roughly ninety days, are cited as a practice worth copying. Declaring where a model stops working is presented as part of the model.

---

## 9. What the Index Does Not Do

9.1 The repository states nine limitations. They are reproduced here because they are the most important part of the document for any reader considering what weight to give the tool.

9.2 Proxy construct. Endangerment and feasibility derive from INFORM sub scores supplemented by conflict and weather data. They are not CERAI's full twenty two variable engine. They should be read as a faithful architectural proxy, not a validated instrument.

9.3 Researcher assigned weights. Every weight is a best estimate pending expert validation through structured elicitation. This places them at the same evidentiary level as INFORM's own initial weights, which is to say provisional and untested by consensus.

9.4 No ground truth calibration. Independent ground truth for evacuation decisions does not exist. There is no register of correct historical calls against which the index could be scored. Sibling calibration provides face validity, not statistical generalisation.

9.5 Population level vulnerability. The demographic profile is a scenario the user sets, not measured household data. It cannot capture individual circumstance.

9.6 Static snapshot. The endangerment and feasibility pair has no corridor dynamics, ceasefire windows, or modelling of misinformation. When hosted as a static site, news and conflict data are captured rather than live; weather remains live.

9.7 No modelling of political will. The index cannot represent actor behaviour, negotiation status, sudden shifts in belligerent intent, or the granting and withdrawal of consent. In many real evacuations these are the determining factors.

9.8 Variable evidence quality. Source credibility tiering is a stated design principle that is not yet weighted in the code. Live inputs differ in their verification standards.

9.9 Optional damage layer. Without a self hosted deployment, physical damage evidence is simply absent from the assessment.

9.10 Correlation, not causation. The index prioritises attention. It is decision support and must not be the sole basis for an evacuation decision.

---

## 10. Governance and Intended Use

10.1 The governance position is stated in a single sentence borrowed from the FLARE project: a decision support tool, not an executioner.

10.2 In practice this means the index is built to inform a judgement rather than to replace one. It surfaces which crises show a wide divergence between the risk of staying and the risk of leaving, which show a protection gap requiring political rather than operational escalation, and which are deteriorating on recent evidence.

10.3 It does not recommend evacuation. It does not rank populations for priority. It does not produce a threshold at which action becomes mandatory. The 75 per cent marker on the endangerment scale is a reference line drawn from the legal framework, not a trigger the software acts upon.

10.4 Two constraint layers sit outside the scoring entirely, on the view that they should filter a recommendation rather than dilute it. A financial feasibility check asks whether a recommended action is affordable once transport, accommodation, asset loss, and income disruption are counted. A legal and rights check, referencing the freedom of movement affirmed in Article 13 of the Universal Declaration of Human Rights, flags exit visa requirements, travel bans, and closure orders that restrict people from evacuating themselves.

---

## 11. From Prototype to Instrument

11.1 The repository sets out a three phase sequence for turning the current build into something defensible.

11.2 Phase one covers variable design, using structured expert elicitation across two rounds with a panel of eight to twelve specialists, to set initial weights at the layer and sub variable level.

11.3 Phase two covers weight validation using fuzzy analytic hierarchy process methods, chosen because they accommodate the ambiguity in expert judgement that ordinary pairwise comparison forces experts to suppress.

11.4 Phase three covers calibration against historical cases, including Sudan in 2023, Ukraine in 2022, Kabul in 2021, Lebanon in 2006, and Haiti in 2010, together with statistical analysis to identify and remove redundant variables.

11.5 Until phase two is complete, the weights on the map are the considered estimates of a single researcher. The tool says so on the page where those weights appear.

---

## 12. Conclusion

12.1 The contribution of this prototype is not a novel algorithm. It is a reframing. By insisting that the risk of leaving be scored separately from the risk of staying, and that danger be scored separately from feasibility, it makes visible a comparison that humanitarian assessment usually leaves implicit.

12.2 Its second contribution is its treatment of its own uncertainty. The weights are labelled as unvalidated. The proxies are labelled as proxies. The absent capabilities are listed rather than omitted. The satellite overlay reports honestly that it is not connected. For a tool that touches decisions about who moves and who remains, this reticence is not a weakness in the work; it is a substantial part of what the work is demonstrating.

12.3 The index does not know whether anyone should evacuate. It is built to make the question harder to answer carelessly.

---

## Attribution

This report describes a research prototype developed by Carolina Morón as masters research at the NYU Center for Global Affairs, published under Ethical Tech CoLab.

The live application is available at https://ethical-tech-colab.github.io/evacuation-inform-index-carolina/

---

## Sources

Primary data and frameworks referenced in this report:

- [INFORM Severity Index](https://www.acaps.org/en/thematics/all-topics/inform-severity-index), ACAPS with the Joint Research Centre of the European Commission, April 2026 release, 104 crises
- [Article 49, Geneva Convention (IV) on Civilians, 1949](https://ihl-databases.icrc.org/en/ihl-treaties/gciv-1949/article-49), International Committee of the Red Cross
- [ACLED](https://acleddata.com), conflict event and fatality data
- [Open-Meteo](https://open-meteo.com), route weather and daylight
- [Microsoft HASTE](https://aka.ms/HASTE), satellite damage assessment, self hosted
- [IOM Risk Index for Climate Displacement](https://environmentalmigration.iom.int/CMIL-AP/RICD), two tier macro and micro precedent
- [CDC Social Vulnerability Index](https://www.atsdr.cdc.gov/placeandhealth/svi/index.html), personal vulnerability layer
- [Fragile States Index](https://fragilestatesindex.org), Fund for Peace
- [Handbook on Constructing Composite Indicators](https://publications.jrc.ec.europa.eu/repository/handle/JRC31473), OECD and JRC, 2008
- Saaty, T.L. (1990). How to Make a Decision: The Analytic Hierarchy Process. European Journal of Operational Research, volume 48, issue 1, pages 9 to 26
- Beccari, B. (2016). A Comparative Analysis of Disaster Risk, Vulnerability and Resilience Composite Indicators. PLoS Currents Disasters
- Al Fozaie (2022). A Guide to Integrating Expert Opinion and Fuzzy AHP When Generating Weights for Composite Indices. Advances in Fuzzy Systems

---

> This document is a plain language description of a research prototype. The Evacuation Inform Index has not been validated, carries no institutional mandate, and must not be used as the sole basis for any decision affecting the movement or safety of civilians.
