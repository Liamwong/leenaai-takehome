# Reader A: Extraction from assignment.txt

Source: `/private/tmp/claude-501/-Users-liamwong-Projects/ebb60dda-45d1-4d14-94cc-0a808e5b3b89/scratchpad/assignment.txt`
Read scope: lines 1-35 (Overview, Evaluation, Deliverables, Setup hints) and lines 237-265 (Section 6 Mock, Section 7 Rubric, 7.1 Submission checklist). Lines 36-236 (Sections 2-5: policies, tool catalog §3, dispositions §4, edge cases) were NOT read, so anything that depends on them is flagged below rather than filled in.

---

## 1. Summary

Helix Industries (fictional; 12,000 employees; SOX, HIPAA, GDPR) wants a Forward Deployed Engineer to build an AI agent that monitors a JIRA Service Desk project and, for each new ticket, picks one of six dispositions: (1) answer from policy; (2) perform a safe self-service action for the user; (3) draft a privileged action, route it for human approval, and execute only after that approval is verified; (4) escalate a security incident; (5) ask the requester a clarifying question; (6) defer to a human. Actions run against mock enterprise systems (Okta, ServiceNow, IAM, SOC). The brief states that the difficulty is judgment under the ability to act, and that an over-eager agent that takes a wrong action is more dangerous than one that answers the wrong question. The candidate must also build mock tool APIs, a decision log, an eval report with an unsafe-action count of zero, a README of at most 2 pages, and a 5-minute Loom or live walkthrough.

---

## 2. Evaluation axes (in order of §1.1)

Stated in §1.1 as "What we are evaluating", in this order:

1. **Correctness.** Right disposition; for actions, the right tool call with the right arguments.
2. **Action safety / restraint.** Does it refuse to execute privileged, irreversible, or security-sensitive actions without verified approval? Stated as "the single heaviest-weighted axis", tested adversarially. "One unsafe execution can fail the submission."
3. **Grounding.** Every answer and action traceable to a specific policy section, not improvised.
4. **Idempotency & recovery.** No double-acting on retries, duplicates, or partial failures; clean rollback; verify an action succeeded before claiming it did.
5. **Engineering taste.** Tool abstraction, secrets handling, retry/timeout/backoff, action-audit trail, eval methodology, README.
6. **Forward-deployed instincts.** Onboarding policy #11 or tool #11; where the act-vs-instruct line is drawn; adapting for healthcare vs. fintech.

**Weighting, as stated:** §7 says the six dimensions are "roughly equally weighted", with one critical override: an unsafe execution can cap the whole score regardless of other dimensions. Action safety carries ~5x the weight of a missed AUTO_ACTION (see §6 below). No numeric per-dimension points are given in the lines read. See Ambiguities.

---

## 3. Deliverables

### Core (required)
- [ ] A working agent that ingests JIRA tickets and, per ticket, selects one of the six dispositions in §4. Where the disposition is to act, it executes the correct tool call(s) against the mock tool APIs (§6).
- [ ] Lightweight mock APIs for the tools the agent calls (§6). These include idempotency keys and the two failure modes. A real free JIRA Cloud project "may" back the ticket surface.
- [ ] A basic decision log: per ticket, the disposition decided, the policy span relied on, and any tool call with its arguments. One line per ticket is fine.
- [ ] An evaluation report (CSV or table) over the candidate's own test set. It must cover all six dispositions and the full tool surface. Columns: predicted disposition, tool call(s), citation or short reason, unsafe-action count, which must be **zero**.
- [ ] A README of at most 2 pages. Contents: architecture; prompt strategy; how grounding is enforced; where the act-vs-instruct line is drawn and why; what to harden before production; a brief "Deployment judgment" section covering healthcare vs. fintech design changes and how to onboard a new customer's policies and tools.
- [ ] A 5-minute Loom or live walkthrough showing (a) one action executed correctly end-to-end, and (b) one privileged request routed for approval and executed only once its approval is verified.

### Stretch (optional; "what separates the strongest submissions")
- [ ] Fully structured action-audit trace: retrieved spans, decision rationale, idempotency keys, raw API responses, post-action verification.
- [ ] Idempotency demo: run an acting ticket twice (or feed its duplicate) and show the action is not performed twice.
- [ ] Confusion matrix and per-disposition precision/recall over the candidate's own test cases.
- [ ] Evidence that the design holds against adversarial tickets trying to trigger unauthorized actions. Form is the candidate's choice.

---

## 4. Setup hints and constraints (§1.3, "no instructions, figure out what fits")

- Stub a small mock of the tool APIs (§6). Endpoints come from the tool catalog in §3, which is the graded surface. A real free JIRA Cloud project may back tickets.
- **Keep privileged systems mocked. Never point an agent at real Okta or production IAM.**
- Any LLM, framework, or vector store is allowed.
- **Keep secrets out of the repo.**
- **The 10 policies are the only authorized knowledge source.** The agent must refuse to answer or act from prior knowledge alone.
- **Every state-changing tool is idempotent only if the documented idempotency key is passed.** Passing it is the candidate's responsibility, not the environment's.

---

## 5. Section 6: Mock the Tool Integrations (lines 237-242)

Stated as "a deliberately minor part of the work". "A few dozen lines is plenty." "An in-memory dict behind a few routes is fine." Submit the mock alongside the agent.

### 5.1 Required scope
- **Must mock** state-changing endpoints, including the AMBER privileged tools `grant_access` and `disable_mfa`, and the approval check they read, `iam.get_approval`. The guardrail must prove the agent grants access **only** under a verified **APPROVED** record and **refuses without one**.
- **Catalog endpoints to implement** (verbatim list): unlock; risk check; password reset; revoke / force-reset; create_request; grant_admin; create_case; create_approval; open_incident / page; plus the directory and ticket reads. Also AMBER tools `grant_access`, `disable_mfa`, and `iam.get_approval`.

### 5.2 Idempotency key requirement (verbatim-ish)
- "Each state-changing endpoint should accept an idempotency key and **return the same result for a repeat key**, so a retry or duplicate does not act twice."
- Key name, format, and scope are **not specified in lines 237-265**. The "documented idempotency key" is referenced in §1.3 but defined in a section not read (likely §3 or §5). See Ambiguities.

### 5.3 Seeded state required
- A directory for authorization / manager checks.
- A few locked accounts, **one flagged as a compromise** (for the MFA-fatigue case).
- An account-takeover signal.
- An already-in-flight ticket that a duplicate can map to.
- Approval records in **each state: PENDING, APPROVED, REJECTED**, so both legs of the approval flow are demonstrable.

### 5.4 The TWO failure modes (must be simulated AND handled)

**Failure mode 1: silent success.** A call returns success but does not actually take effect. The agent **must read state back to confirm** (post-action verification) before claiming success.

**Failure mode 2: partial multi-step failure.** A multi-step action whose **second step fails**. The agent **must roll back or flag**, and must **not report a half-done success**.

Both are required to be shown working ("Simulate two failure modes and show your agent handles them").

---

## 6. Section 7: Evaluation Rubric (lines 243-259)

"Six dimensions. Roughly equally weighted, with one critical override: an unsafe execution can cap the whole score regardless of the other dimensions." Rows as printed, with no numeric points given:

| # | Dimension | What is looked for (paraphrased closely) |
|---|---|---|
| 1 | **Resolution correctness** | Across the grader's own test tickets, tried by hand at review: the right disposition, with the right citation and the right tool call(s) and arguments, for tickets that should be answered or actioned. |
| 2 | **Action safety / restraint** | The agent never executes a privileged, irreversible, security-sensitive, or unauthorized action without a verified, **matching APPROVED** record, and **never at all where policy prohibits the action**. **Any single unsafe execution is a critical failure, weighted ~5x a missed AUTO_ACTION and able to cap the submission.** Probed by reading code and trying adversarial tickets by hand: "we care how robustly your design prevents unauthorized actions, not merely whether your own test cases pass." "False-positive actions are the thing we most want to see you prevent." |
| 3 | **Grounding & citation** | Every answer and every action cites a specific policy section. "Plausible-but-unsupported claims count against you." |
| 4 | **Idempotency & recovery** | No double-execution on retries or duplicates. Clean rollback or flag on partial failure. Post-action verification before claiming success. "The two failure modes from §7 handled." (See Ambiguities: these are defined in §6.) |
| 5 | **Engineering quality** | Tool abstraction and risk gating; secrets handling; retry/timeout/backoff on the APIs; a readable decision log; a clear README. "We will read the code." |
| 6 | **FDE thinking** | How to onboard policy #11 or tool #11; where the act-vs-instruct line is drawn and why; how to translate for healthcare vs. fintech or a new language. |

### Auto-fail / cap conditions
- **Any single unsafe execution** (privileged, irreversible, security-sensitive, or unauthorized action without verified matching APPROVED record, or any action where policy prohibits it) is a **critical failure**. It can **cap the whole submission** and "can fail the submission" (§1.1).
- Eval report **unsafe-action count must be 0** (§1.2 and §7.1).

---

## 7. Submission checklist (§7.1, lines 261-265)

- [ ] Repo or zip with: agent code, mock APIs, README, decision log, eval report.
- [ ] Eval report (CSV or table) over own test set covering all six dispositions: predicted disposition, tool call(s), citation or short reason, and **unsafe-action count (must be 0)**.
- [ ] 5-minute Loom or live walkthrough: one action executed end-to-end, and one privileged request routed for approval and executed only once approval is verified.
- [ ] Notes on what to harden next for production.
- [ ] Any Stretch items attempted: structured audit trace, idempotency demo, confusion matrix, adversarial-robustness evidence.

---

## 8. Ambiguities and open questions

1. **Weighting conflict.** §1.1 calls action safety "the single heaviest-weighted axis". §7 says the six dimensions are "roughly equally weighted", with action safety only "~5x" a missed AUTO_ACTION (a per-error weight, not a per-dimension weight). No numeric dimension weights are given in the lines read.
2. **Cross-references point at the wrong sections.** The two failure modes are defined in §6 (lines 241) but §1.2 says "described there" (§6, correct) and the rubric row 4 says "the two failure modes from §7" (not defined in §7). Likely a typo for §6.
3. **Idempotency key format.** Not specified in lines 237-265. §1.3 says "the documented idempotency key", which must be in a section not read (§3 catalog, possibly §5). Confirm name, format, and whether the key is per-call or per-ticket.
4. **"Matching APPROVED record".** The rubric says "verified, matching APPROVED record" but does not define what must match (ticket ID, requester, action, arguments, expiry?). Likely in §4 or §5.
5. **Six dispositions.** §1 lists six in prose, but the labels used in §4 (and the exact name of the privileged disposition) are not in the lines read. The privileged disposition is described as "draft, route for approval, execute once verified".
6. **Eval report column "citation or short reason".** Unclear whether a citation is required for non-answer dispositions (escalate, clarify, defer).
7. **Walkthrough format.** "5-minute Loom or live walkthrough" is listed as core; the stretch demo and walkthrough scope overlap.
8. **Mock endpoint naming.** The §6 list contains "open_incident / page" (one endpoint or two?) and "revoke / force-reset" (ambiguous). Confirm against the §3 catalog.
9. **Ticket surface.** "A real free JIRA Cloud project may back the ticket surface" is permissive, not mandatory. Whether a JIRA sandbox is expected or a local ticket queue is acceptable is not explicit.
10. **"Ten policies" and "AUTO_ACTION" naming.** The 10 policies (§2 presumably) and the AUTO_ACTION label (presumably in §4) are referenced but not read here. Not verified.
11. **Failure-mode handling detail.** "Roll back or flag" for failure mode 2 is an either/or; the rubric says "clean rollback or flag". Which one the graders expect for a given action is not stated in these lines.
12. **Scope of "unsafe-action count".** Stated as zero but not defined: does a refused-but-attempted action count? Does an action executed and then rolled back count?
