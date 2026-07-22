# Peer Review: The Evacuation Inform Index (EII)

**Reviewed as:** a masters research report / methods-and-tool paper written for a policy, humanitarian, and legal readership (NYU CGA masters research, published under Ethical Tech CoLab).

**Overall assessment:** A conceptually strong and unusually honest report whose core reframing — scoring the risk of leaving separately from the risk of staying, and danger separately from feasibility — is a genuine contribution that humanitarian assessment usually leaves implicit. The single most important thing standing between it and a publishable methods paper is empirical grounding: the report describes the instrument thoroughly but never *demonstrates* it on a real crisis, and it does not directly reckon with whether its central proxy (INFORM "Complexity" standing in for the danger/difficulty of civilian evacuation) actually measures what it claims. My read: **major revisions** — strong bones, needs one worked example and a direct proxy-validation section before the claims fully land.

## Summary of the paper

The EII is a research prototype: a browser-based tool that scores 104 active humanitarian crises on two separate dimensions — the risk of remaining in place and the risk of attempting to leave — and expresses their relationship as a ratio while always displaying both component scores. The component scores are derived from the INFORM Severity Index (mapping INFORM's "Conditions of affected people" onto the risk of staying and its "Complexity" onto the risk of evacuating), supplemented by live ACLED conflict data, news retrieval, Open-Meteo route weather, and an optional self-hosted satellite damage overlay (Microsoft HASTE). A second analytical layer, adapted from the CERAI framework, deliberately keeps danger and feasibility apart so that operational difficulty cannot quietly cancel legal obligation. The report is emphatic about the tool's limits — nine stated limitations, unvalidated researcher-assigned weights, proxy constructs, and no ground-truth calibration — and frames the contribution not as a novel algorithm but as a reframing that "makes the question harder to answer carelessly."

## Strengths

- **The central conceptual move is real and well-argued.** Separating risk-of-leaving from risk-of-staying (§2.1–2.4), and danger from feasibility (§5.1–5.3), is the paper's genuine intellectual contribution, and it is motivated both analytically (the two risks move independently — a siege catastrophic to endure yet impossible to escape) and legally (Article 49 GC IV; the protection-gap logic in §5.2). This is the part to protect and build the paper around.
- **The epistemic honesty is exemplary and rare.** §9's nine limitations, the labeling of proxies as proxies (§9.2), unvalidated weights as unvalidated (§9.3, §11.5), and the satellite layer that "reports honestly that it is not connected" (§7.7, §12.2) together model good uncertainty disclosure. For a tool touching decisions about who moves and who stays, this reticence is itself a substantive part of the work, as §12.2 rightly claims.
- **The aggregation choice is principled, not arbitrary.** The weighted geometric mean (§4.4) — so that a catastrophic score on one component cannot be averaged away by comfortable scores elsewhere — is correctly justified as non-compensatory logic with real precedent (HDI, INFORM Risk).
- **The evidence discipline is coherent** (§7): deterministic, reconstructable-by-hand scoring; the two-witness standard; treating an evidence gap as a risk signal rather than a neutral absence (§7.4); and capping unverified fallbacks below verified status (§7.5).

## Major issues

1. **The central proxy is asserted, not validated, and may measure a neighboring construct.** §4.2 maps INFORM "Complexity" onto "Risk Score for Evacuating." But INFORM Complexity measures humanitarian *access and operating environment for responders delivering aid* — not the danger and difficulty faced by *civilians self-evacuating* along a specific corridor. These are correlated but genuinely distinct: a besieged city can score terribly on humanitarian access while the question of whether families can walk out a particular exit gate is a different one. The report concedes it is "a substitution" (§4.2) but never examines where the two diverge, in which direction the proxy would bias the score, or by how much. This is the load-bearing validity question for the whole instrument. *Fix:* add a subsection that names 1–2 real crises where humanitarian-access complexity and civilian-evacuation difficulty pull apart, states the expected direction of bias, and explains why the mapping is still defensible despite it.

2. **The headline ratio is arithmetically fragile in ways the single safeguard does not fully cover.** §4.1 defines the ratio as evacuation risk over staying risk, with only a 0.5 floor on the denominator. Three concerns compound: (a) dividing two rescaled 5-point scores treats them as ratio-scale quantities, which INFORM-derived ordinal severity bands are not obviously entitled to; (b) the 0.5 floor is arbitrary and its effect is not characterized — a staying score floored from, say, 0.2 to 0.5 changes the displayed ratio by 2.5×, a large swing driven by a safeguard rather than by the data; (c) equal ratios can hide very different absolute stakes (evac 1 / stay 1 and evac 5 / stay 5 both read 1.0). The paper mitigates (c) by always showing both components, but the ratio remains the "single ratio" headline of §1.1. *Fix:* justify (or drop) the ratio-scale treatment, report a short sensitivity check on the floor, and consider demoting the ratio relative to the two-component display, which is more consistent with the paper's own anti-collapse philosophy (§5).

3. **The elaborate design and the actually-built tool are interleaved in a way that invites over-reading.** §4.3 presents a three-layer architecture with specific weights (50/35/15, sub-weights 20/15/15 and 12/10/8/5) and §5.6 a twelve-factor vulnerability profile — but §8.3 and §11.5 reveal that the live build implements essentially only layer one (the INFORM mapping) and that most of this is "designed but not yet built." The report marks this honestly, yet the sheer specificity of the weight tables can lead a reader to treat the planned design as operative. *Fix:* add a single implemented-vs-planned table near the top (§3 or §4) mapping each component to its status, so the reader never has to reconstruct the boundary from scattered cues.

4. **No demonstration.** For a tool whose entire pitch is "make a comparison visible," the report never walks one named crisis end to end. This is the biggest single gap between "described" and "shown." (See *What's missing*; I rank it first among fixes below.)

## Minor issues

1. **Data currency.** The report repeatedly leans on the "April 2026 release … 104 crises" (§1.1–1.2). As of mid-2026 a newer INFORM release likely exists; state the snapshot date and update cadence explicitly wherever the 104 figure appears, so the number reads as a snapshot rather than a fixed fact.
2. **Source-list inconsistency.** The Sources section mixes fully-formed academic citations (Saaty 1990; Beccari 2016; Al Fozaie 2022) with URL-plus-description entries. Normalize to one style (MLA or the house convention) and give the internal frameworks (CERAI, FLARE) a followable reference or an explicit "internal project" label.
3. **Two prose-heavy weight passages** (§4.3) would read far more cleanly as the implemented-vs-planned table recommended above.

## What's missing

- **A worked example.** One named crisis (e.g., Sudan 2023 or another from the §11.4 calibration set) carried all the way through — staying score, evacuating score, the ratio, the endangerment/feasibility split, and one vulnerability profile applied — with the actual numbers. This would teach more than the entire descriptive apparatus and would surface any hidden arithmetic surprises.
- **A sensitivity analysis, even informal.** How much does the output move with the arbitrary choices — the 0.5 floor (§4.1), the 10-to-5-point rescaling (§4.2), the 0.06 multiplier step (§5.6)? A reader currently cannot tell whether the tool's rankings are robust or knife-edge.
- **A misuse/adversarial section.** The governance discussion (§10) lists what the tool does not do, but not how it guards against motivated misreading — an actor citing a sub-1.0 ratio to justify forced transfer, or a supra-1.0 ratio to justify denying evacuation. Given that Article 49 sits at the center of the framing, one paragraph on political misuse is warranted.
- **A comparison against the fuller CERAI outputs.** Since the EII adapts CERAI's structure but implements only a proxy of it, showing where the simplified proxy agrees and disagrees with the fuller CERAI engine on a few crises would be the most natural available form of validation.

## Internal inconsistencies

1. **"We resist a single number" vs. "we express it as a single ratio."** §5's entire argument is that danger and feasibility must never be collapsed into one score, yet §1.1 and §4.1 foreground the ratio as the headline metric and §1.1 calls it "a single ratio." The paper is aware of the tension (it always shows both components) and §12.1 reframes the contribution as a reframing rather than an algorithm — but the framing still wobbles between these two commitments. Reconcile it explicitly in one sentence: the ratio is a pointer that directs attention, not a verdict, and it is never the object of the anti-collapse critique because both components remain visible.
2. **Multiplier saturation is undisclosed.** §5.6 states each vulnerability factor "shifts a multiplier by 0.06, bounded between 0.7 and 1.3." That is ±0.30 around 1.0, i.e. only five 0.06 steps in each direction — yet ten of the twelve factors raise risk. A user profiling a highly vulnerable group (say, a wounded, elderly, undocumented, linguistic-minority unaccompanied minor) toggles more than five risk-raising factors, at which point the multiplier saturates at 1.3 and additional factors have no effect. This silently contradicts the section's premise that these factors are cumulative, and it should be disclosed and, ideally, justified.
3. **"Risk of Evacuating" vs. "Feasibility" — same quantity, two names, never reconciled.** §4.2 maps Complexity to the *Risk of Evacuating* (more complexity → higher evac risk); §5.3 computes *Feasibility* as "INFORM Complexity inverted" (more complexity → lower feasibility). These are consistent — evac risk and feasibility are inverses of the same input — but the report uses the two labels across different sections without ever stating that evacuation-risk ≈ (1 − feasibility). A careful reader tracking both dimensions will suspect a double-count. State the identity explicitly.

## Prioritized next steps

If the author has time for only three things:

1. **Add one end-to-end worked example** of a named crisis with real numbers (staying, evacuating, ratio, endangerment/feasibility, one vulnerability profile). Highest value, lowest cost; also the most effective way to catch hidden issues like the saturation above.
2. **Confront the INFORM-Complexity-as-evacuation proxy directly** (Major issue 1): divergence examples, expected bias direction, and why the substitution is still defensible.
3. **Add an implemented-vs-planned table near the top** so the three-layer/twelve-factor design is not mistaken for the live build, and disclose the ratio floor's sensitivity and the multiplier saturation alongside it.

## What to take forward

- **Pair every "this is a proxy" with "and here is where it would mislead."** The report's honesty is a real asset, but honesty that only disclaims is weaker than honesty that diagnoses. The habit to build: whenever you flag a limitation, add the one sentence about *which direction* it bends the result — that turns a caveat into something a reader can actually reason with.
- **Show, don't only describe.** A tool paper needs at least one worked instance; the reframing you are proud of only becomes legible when a reader watches it operate on a real case.
- **Interrogate whether an off-the-shelf indicator measures *your* construct or a neighboring one.** The INFORM→EII mapping is the paper's recurring soft spot, and the same question — "does this measure what I need, or something adjacent that correlates?" — is the discipline to carry into every future use of a borrowed index.

## References

1. INFORM Severity Index, ACAPS with the Joint Research Centre of the European Commission, April 2026 release. https://www.acaps.org/en/thematics/all-topics/inform-severity-index
2. Article 49, Geneva Convention (IV) relative to the Protection of Civilian Persons in Time of War, 1949, International Committee of the Red Cross. https://ihl-databases.icrc.org/en/ihl-treaties/gciv-1949/article-49
3. Saaty, Thomas L. "How to Make a Decision: The Analytic Hierarchy Process." *European Journal of Operational Research*, vol. 48, no. 1, 1990, pp. 9–26.
4. Al Fozaie, M. "A Guide to Integrating Expert Opinion and Fuzzy AHP When Generating Weights for Composite Indices." *Advances in Fuzzy Systems*, 2022.
5. OECD and JRC. *Handbook on Constructing Composite Indicators: Methodology and User Guide*, 2008.

**[Verification Required]** The report attributes a "two witness standard" to "the FLARE model developed by the Global Fund to End Modern Slavery" (§7.2). I could not independently confirm that GFEMS's FLARE uses a formally-named two-witness corroboration standard as described; the author should supply a followable citation or mark FLARE and CERAI explicitly as internal sibling projects.
