---
title: "VDR in Real Life: From Scanner Disposition to Evidence-Backed Response"
tagline: Follow a finding through source-code analysis, mitigation, and a reviewed attestation in TSW.
day: 3
start: 2027-01-21T12:00:00-08:00
end: 2027-01-21T13:00:00-08:00
leads: [matthew-venne]
---
Scanners provide an initial disposition using the evidence available to them. The next step is to investigate the specific vulnerability in the deployed environment, determine what action is appropriate, and record the evidence behind that decision.

This session applies the evaluation approach from Day 2 to real operational work. We will follow sanitized examples from an initial scanner assessment through in-depth source-code and deployment analysis: what code is affected, how it is invoked, what conditions exploitation requires, and which protections or mitigations apply. The investigation may confirm the initial assessment or establish evidence for revising it.

We will then demonstrate the attestation process in ThreatAlert (TSW): documenting the analysis and supporting evidence, scoping the assertion to affected resources, submitting it for separate review, and recording the resulting disposition and response. We will show how the original assessment and subsequent decisions remain traceable, how mitigation limitations and outstanding remediation stay visible, and when changed conditions require reevaluation.

The published Brotli response case will illustrate mitigation when the exposure belongs to the operator but the patch belongs to a vendor. The session connects the research, operational action, and documented decision so attendees can apply the process in their own systems.

**You will leave with:** Examine the evidence supporting an initial and a researched assessment; follow a mitigation and attestation workflow; receive a reusable investigation and attestation worksheet and a worked response record. The examples show how to preserve the rationale and history needed for ongoing management and reporting.

**Prerequisites:** Day 2 is useful background but is not required; the session opens with a short recap. Familiarity with vulnerability findings is helpful. No TSW account or advance reading is required.
