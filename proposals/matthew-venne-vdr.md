# Matthew Venne: VDR Evaluation and VDR in Real Life

## Type

Two single-session proposals, one each for Day 2 and Day 3, plus an optional
Day 1 panel. Each technical session is 60 minutes and can be scheduled or
approved independently. Together, they connect the evaluation method to its
application in a running vulnerability management program.

## Leads

- Name: Matthew Venne
- Affiliation: Chief Technology Officer, stackArmor
- Link for the affiliation: <https://stackarmor.com/>
- Bio: Matthew Venne is Chief Technology Officer at stackArmor, with nearly
  15 years of experience in federal information security. He is the chief
  architect of three FedRAMP-authorized platforms and the author of
  [stackArmor's public white papers on FedRAMP VDR/VER](https://stackarmor.github.io/rfc-fedramp-vdr/),
  covering vulnerability evaluation, PAIN scoring, internet reachability, and
  evidence-backed response. He publishes his methods openly to support
  community scrutiny, reuse, and improvement.

## Session: Day 2 — VDR Evaluation

- Title: Show Your Work: Building a Defensible VDR Evaluation Method
- Tagline: Turn vulnerability findings into repeatable, explainable decisions
  about exploitability, internet reachability, and potential agency impact.
- Description:

  A scanner finding starts an evaluation. Completing it requires a method for
  determining likely exploitability, internet reachability, and potential agency
  impact in the context of the affected service and its agency use.

  This session walks through stackArmor's public, deterministic,
  CVSS-Environmental evaluation method and the evidence behind its decisions.
  We will examine how FedRAMP's eight evaluation factors inform the three
  evaluation outputs, including asset security-impact profiles, intended agency
  use, exploitation signals, reachability, and affected-agency scope. Worked
  examples will show how the same vulnerability can receive different
  evaluations in different deployments.

  We will explain the assumptions, calibration choices, and tradeoffs in this
  method, including where another provider could reasonably choose a different
  approach. Attendees can follow the examples and discuss what additional
  evidence would change the result. The session gives teams a way to inspect
  and explain their evaluations, whether they adopt this method or develop
  their own.

- What attendees will do or leave with: Work through contrasting examples;
  receive the worked evaluations, a reusable decision-record template, and
  links to the public method and supporting white papers. Participants will
  have practical questions for assessing the evidence, assumptions, and
  consistency of their own evaluation method.
- Prerequisites: Familiarity with vulnerability findings and basic VDR/VER
  terminology is helpful. No product account or advance reading is required.
- Preferred time of day and length: Day 2, January 20, 2027; 60 minutes;
  flexible on time of day.
- Tools or data you will use: Public white papers, stackArmor's public
  Trivy-based VDR tooling, and sanitized or synthetic findings and deployment
  examples. Materials will be prepared for the workshop and shared publicly.

### Proposed 60-minute outline

1. 10 minutes: What an evaluation method needs to produce and explain.
2. 15 minutes: The public method, its inputs, and the eight evaluation factors.
3. 25 minutes: Contrasting worked examples and audience discussion.
4. 10 minutes: Questions and answers.

## Session: Day 3 — Remediation and Reporting

- Title: VDR in Real Life: From Scanner Disposition to Evidence-Backed Response
- Tagline: Follow a finding through source-code analysis, mitigation, and a
  reviewed attestation in TSW.
- Description:

  Scanners provide an initial disposition using the evidence available to
  them. The next step is to investigate the specific vulnerability in the
  deployed environment, determine what action is appropriate, and record the
  evidence behind that decision.

  This session applies the evaluation approach from Day 2 to real operational
  work. We will follow sanitized examples from an initial scanner assessment
  through in-depth source-code and deployment analysis: what code is affected,
  how it is invoked, what conditions exploitation requires, and which
  protections or mitigations apply. The investigation may confirm the initial
  assessment or establish evidence for revising it.

  We will then demonstrate the attestation process in ThreatAlert (TSW):
  documenting the analysis and supporting evidence, scoping the assertion to
  affected resources, submitting it for separate review, and recording the
  resulting disposition and response. We will show how the original assessment
  and subsequent decisions remain traceable, how mitigation limitations and
  outstanding remediation stay visible, and when changed conditions require
  reevaluation.

  The published Brotli response case will illustrate mitigation when the
  exposure belongs to the operator but the patch belongs to a vendor. The
  session connects the research, operational action, and documented decision
  so attendees can apply the process in their own systems.

- What attendees will do or leave with: Examine the evidence supporting an
  initial and a researched assessment; follow a mitigation and attestation
  workflow; receive a reusable investigation and attestation worksheet and a
  worked response record. The examples show how to preserve the rationale and
  history needed for ongoing management and reporting.
- Prerequisites: Day 2 is useful background but is not required; the session
  opens with a short recap. Familiarity with vulnerability findings is helpful.
  No TSW account or advance reading is required.
- Preferred time of day and length: Day 3, January 21, 2027; 60 minutes;
  flexible on time of day.
- Tools or data you will use: TSW as the demonstrated operational system;
  public vulnerability advisories and source-code excerpts; sanitized or
  synthetic scanner findings, deployment evidence, mitigation records, and
  attestations. The walkthrough and shared worksheets will be usable without
  a TSW account. Workshop examples and materials will be prepared in advance.

### Proposed 60-minute outline

1. 5 minutes: Initial scanner disposition and a recap of the evaluation method.
2. 20 minutes: Source-code and deployment analysis.
3. 15 minutes: Selecting and validating mitigations, including their limits.
4. 10 minutes: TSW attestation, separate review, and the resulting disposition.
5. 10 minutes: Questions and answers.

## Optional Session: Day 1 Panel

- Title: What's Blocking Your VDR Implementation?
- Tagline: A practitioner discussion of the decisions and capabilities needed
  to move from plans to an operating VDR program.
- Description:

  Matthew is also available to participate in an opening panel that sets the
  stage for the technical sessions. The discussion would draw on firsthand
  implementation experience to explore organizational commitment, evaluation
  methods, gaps between scanner capabilities and operational needs, staffing,
  tooling, and authority to act.

  The opening question is what the organization wants its federal program to
  achieve and whether it has committed the resources needed to support that
  goal. Panelists would then discuss concrete implementation obstacles and
  how they addressed them, with time for audience questions. A short readiness
  worksheet would help attendees identify their own missing capabilities and
  leadership decisions. The focus is organizational readiness and security
  implementation, using general examples and individual self-assessment.

- What attendees will do or leave with: Identify their most immediate
  implementation obstacles and the next decisions, evidence, or resources
  needed to move forward.
- Prerequisites: None.
- Preferred time of day and length: Day 1, January 19, 2027; suggest 60 minutes,
  with format and timing flexible.
- Tools or data you will use: Practitioner examples and a short readiness
  worksheet; no product access required.
- Panel coordination: Matthew is offering to participate. Moderator and other
  panelists would be arranged with the organizer; no additional participants
  are being committed by this proposal. This panel is optional and independent
  of the two technical sessions.

## Supporting Resources

The public white-paper collection is the methodological foundation and optional
supporting reading for the sessions:

- [White-paper collection and interactive resources](https://stackarmor.github.io/rfc-fedramp-vdr/).
- [A Deterministic, CVSS-Environmental Method for FedRAMP VDR/VER Vulnerability Prioritization](https://stackarmor.github.io/rfc-fedramp-vdr/vdr-pain-cvss.pdf).
- [Before the PAIN Equation: Deriving Security-Requirements Ceilings from Intended Federal Information Types](https://stackarmor.github.io/rfc-fedramp-vdr/vdr-pain-security-requirements.pdf).
- [High-Centered PAIN Calibration](https://stackarmor.github.io/rfc-fedramp-vdr/vdr-pain-calibration.pdf).
- [Internet Reachability at Scale under the FedRAMP VDR/VER Rules](https://stackarmor.github.io/rfc-fedramp-vdr/internet-reachability.pdf).
- [Beyond the Patch: A Real-World Look at FedRAMP Vulnerability Response](https://stackarmor.com/fedramp-vulnerability-response-beyond-the-patch/).

## Disclosures

- Product the sessions feature: ThreatAlert (TSW), stackArmor's vulnerability
  management and attestation system, and stackArmor's public Trivy-based VDR
  tooling. Matthew is stackArmor's Chief Technology Officer. The techniques,
  examples, and shared materials will support attendees using other systems.
- Any relationship with a sponsor: Matthew's stackArmor affiliation is disclosed
  above. Workshop sponsorship relationships remain to be confirmed by the lead
  before this draft is finalized.

## Agreement

- [x] I have read the [Lead Agreement](https://nocap-workshop.com/lead-agreement/),
      including the Positivity Rule and the competition-law rules, and I agree
      to it if this proposal is approved.
