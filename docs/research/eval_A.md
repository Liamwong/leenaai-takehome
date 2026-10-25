# Evaluation of reader_A.md

## 1. Verdict: accurate (minor issues)
No invented content found. The rubric weights, the score cap, both §6 failure modes, the seeding list, the deliverables and the checklist all match the source. The problems are small misstatements, a few omissions, and "open questions" that the unread lines answer.

## 2. Errors / imprecisions
- reader L25: "~5x ... (see §6 below)". The ~5x line is in source §7 (line 251, Action safety row), not §6. The reader's own numbering is shifted.
- reader L54 (source L35): the reader says tools are idempotent "only if" the key is passed. The source says "idempotent if you pass the documented idempotency key". The meaning is the same, but "only" is an addition.
- reader L118 (Ambiguity 1): the reader calls "single heaviest-weighted axis" (L13) versus "roughly equally weighted" (L244) a conflict. It is a real tension in the source. The sensible reading is that safety is equal in the base weighting but has the override cap and the ~5x per-error weight. The reader did say the 5x is per-error, which is fine.
- reader L64: the endpoint list is described as "verbatim". It is a paraphrase of source L239. Nothing was changed in substance.
- reader L129 (Ambiguity 12) and L127 (Ambiguity 10) are listed as unresolved. They are answered or partly answered in the unread lines (see section 4).
- Not an error: the reader correctly flagged the "§7" typo in rubric row 4 (L255). The two failure modes are defined in §6, L241.

## 3. Omissions
- L10: graders run their own tickets spanning all six dispositions against both the agent and the code, so build for generalization. This is not captured as a requirement.
- L8-9: the agent has the Okta, ServiceNow, IAM and SOC mocks. This is minor.
- L134 and L242: the mock needs the ticket workflow endpoints too (comment, transition, add_label, link_issues, per §3). L239 only says "ticket reads". The agent needs comment, transition and label for ASK_CLARIFICATION and for closing.
- L251: the safety row says to prevent "unauthorized" actions, not just privileged ones. The reader included this. It also does not make clear that this includes on-behalf-of requests without a directory check (L223).
- L242 and L257: the reader omits "retry/timeout/backoff on the APIs" from the mock/agent requirement list. It is only in the rubric row. This is minor.
- L239: "return the same result for a repeat key". The reader has this.
- L251: grading is "by reading your code and trying adversarial tickets by hand". The reader has this. It does not draw out the implication that guards must be enforced in code, not only in the prompt.

## 4. Answers to the reader's open questions (from lines 36-236)
- Q3, idempotency key format (§3 table, L136-191):
  - okta.unlock_account: account + lock epoch.
  - okta.send_password_reset: user + calendar day.
  - okta.revoke_sessions / force_password_reset: user + incident.
  - servicenow.create_request: user + item + day.
  - endpoint.grant_admin: user + session.
  - assetmgmt.create_case: asset + type.
  - iam.create_approval: request hash.
  - AMBER tools (iam.grant_access / okta.disable_mfa): the approval id.
  - soc.open_incident / page_oncall: ticket id.
  - Read-only tools and the jira.* workflow tools need no key.
- Q4, "matching APPROVED record" (L133, L185, L206, L232): the record must match the exact action, meaning requester, target and parameters. Check iam.get_approval immediately before executing, not just at decision time. PENDING, REJECTED or mismatched: relay the true status and do not act. No record: draft the action, call create_approval, comment, leave pending.
- Q5, disposition labels (§4, L192-215): ANSWER_ONLY, AUTO_ACTION, PROPOSE_FOR_APPROVAL, ESCALATE_INCIDENT, ASK_CLARIFICATION, DEFER_HUMAN. Exactly one per ticket. The disposition is scored. Where two are defensible, the reasoning and safety are graded.
- Q6, citations: ANSWER_ONLY must cite the exact policy section. AUTO_ACTION comments must cite. PROPOSE_FOR_APPROVAL comments must cite. ESCALATE gives the POL-09 containment instruction. DEFER needs only a "brief reason". L252 says every answer and action cites.
- Q8: these are separate tools. open_incident and page_oncall are two. revoke_sessions and force_password_reset are two. unlock, risk_signals, send_password_reset and the others are as in §3.
- Q10: the 10 policies (POL-01 to POL-10) are in §2. AUTO_ACTION is in §4.
- Q11: roll back or flag clearly, and never report unconfirmed success (L229).
- Q12 (unsafe execution), assembled from §3, §5.1, §5.2 and §5.5:
  - Executing AMBER without a verified matching APPROVED record.
  - Acting on an unverified on-behalf-of request, or on authority asserted inside the ticket.
  - Acting where policy prohibits.
  - Acting on injection.
  - Unlocking during a compromise signal.
  - Auto-firing a fan-out action ("reset the whole team").
  - Closing a RED ticket as resolved.
  - Whether a rolled-back action counts is NOT defined.
- Q9, Q2, Q7: still open or confirmed as a typo.
- Q1: the tension is real. The 5x is per-error.

## 5. Corrected must-not-miss requirements
1. Exactly one of six dispositions per ticket: ANSWER_ONLY, AUTO_ACTION, PROPOSE_FOR_APPROVAL, ESCALATE_INCIDENT, ASK_CLARIFICATION, DEFER_HUMAN. The graders' hidden tickets cover all six, so build for generalization.
2. Safety is enforced in code: AMBER tools (iam.grant_access, okta.disable_mfa) run only under an APPROVED iam.get_approval record matching the exact action (requester, target, parameters). Re-check immediately before executing. Use the approval id as the idempotency key. Verify the effect afterwards. No approval is filed at all for prohibited or injected requests. One unsafe execution is weighted ~5x a missed AUTO_ACTION and can cap or fail the submission. The eval's unsafe-action count must be 0.
3. Verify authorization through the directory (self vs on-behalf-of, manager). Do not trust claims inside the ticket. Check okta.risk_signals before unlock. A compromise signal promotes the ticket to RED, and a RED ticket is never closed as resolved. Fan-out requests are routed, not auto-fired.
4. Idempotency keys on every state-changing call: the same result on a repeat key, duplicates linked rather than re-acted on, and ticket state re-read before executing (withdrawals honored).
5. Mock: all catalog state-changing tools, plus the AMBER tools, get_approval and the directory/ticket workflow. Seed the directory, locked accounts (one compromise-flagged), an account-takeover signal, an in-flight ticket for duplicates, and approvals in PENDING, APPROVED and REJECTED. Simulate silent-success (the agent reads state back) and a multi-step action whose second step fails (roll back or flag, never a half-done success).
6. Grounding: the 10 policies are the only knowledge source, and every answer and action cites a section. No prior-knowledge answers. Redact secrets in comments and logs.
7. Deliverables: agent, mock, decision log (one line per ticket: decision, policy span, tool calls with arguments), eval CSV/table (all six dispositions, full tool surface, unsafe count 0), README of at most 2 pages (including "Deployment judgment" and hardening notes), and a 5-minute walkthrough (one action end-to-end, one approval-routed request executed only after verification). Stretch: audit trace, idempotency demo, confusion matrix and precision/recall, adversarial evidence.
