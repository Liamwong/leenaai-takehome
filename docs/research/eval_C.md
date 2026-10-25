# Evaluation of Reader C (source lines 128-236)

Line refs "S:n" = assignment.txt; "R:n" = reader_C.md.

## 1. Verdict

PASS, high fidelity. No tool name, argument, risk class or idempotency key is wrong. GREEN* for okta.unlock_account, the GREEN/AMBER/RED definitions, "minimum caution, not a maximum", "no approval filed for prohibited or injected requests", all six dispositions and the AMBER sequence match the source. All §5.1-5.6 bullets are captured (5.6 has all 9 categories). Only minor issues: a few unflagged inferences, one unflagged source tension, and some ambiguities the source actually resolves.

Verified items:
- Tool table (S:136-191): all 13 rows match in name, args, class, key. Examples: unlock key = "account + lock epoch", send_password_reset = "user + calendar day", revoke/force = "user + incident", create_request = "user + item + day", grant_admin = "user + session" with minutes <= 60 (POL-04 4.6), create_case = "asset + type", create_approval = "request hash", AMBER = "approval id", soc = "ticket id". The read-only tools are n/a.
- Risk classes (S:129-134): the GREEN condition (grounded in policy AND identity/authorization verified), the AMBER steps (get_approval, then draft, create_approval, comment, pending, never act on an in-band claim), the exact-match test (requester, target, parameters), approval id as key, verify afterwards, and no approval filed for prohibited or injected requests are all present (R:31-41).
- Dispositions (S:198-215): ASK_CLARIFICATION is one question, transition to "Waiting for Customer", clarification label, re-evaluate on reply, stays with the agent (R:72). ESCALATE_INCIDENT is open incident, page on-call, GREEN containment, POL-09 instruction, never close, redact secrets (R:67). The PROPOSE three-leg flow is correct (R:59-62).
- AMBER sequence incl. re-check immediately before execution (S:232, R:83, R:113): correct.

## 2. Errors / imprecisions

1. R:5 claims "Nothing below is inferred beyond what the text says", but some entries are inferences:
   - R:102 maps "verify through the directory" to `directory.verify_manager`. S:224 says only "directory". Reasonable inference.
   - R:105 maps "link duplicates" to `jira.link_issues`. The tool is in the catalog row (S:140-141), but S:226 does not name it.
   - R:106 maps "re-read state" to `jira.get`. This one is explicit in S:141 ("for duplicates/withdrawals").
   - R:68 and R:78 assign specific tools to dispositions. S:209 gives revoke sessions / force reset as examples ("e.g."), so the list is not exhaustive. R:78 "No mutation tools" for DEFER is stricter than the source. S:215 says "route to the right human queue", which in practice needs a comment, possibly a transition or label.
2. R:60 vs R:32. The source has a tension the reader missed:
   - S:133 says no record "or PENDING" means draft and route via create_approval.
   - S:206 says PENDING means relay the record's true status.
   - R:32 reflects S:133 and R:62 reflects S:206, but the conflict is never flagged.
   - Reconciliation: create_approval keys on the request hash, so re-calling it is idempotent. Safest behavior is get_approval, then relay PENDING status and avoid a duplicate filing. Treat this as a design decision.
3. R:136-139 is correct ("Only POL-04 4.6 and POL-09 appear"). It is worth noting that "POL-04 §4.6" is policy section 4.6, not the assignment's §4.
4. R:22 "Irreversible or privileged (per AMBER definition)" is fine. R:18 "Time-bound (not stated as reversible)" is fine.

No fabricated tools, args or classes.

## 3. Omissions

- soc.open_incident `sev` values are not tied to POL-09.3 (SEV-1..4). Nor is the rule POL-09.6 (a lost/stolen device with Restricted data auto-escalates to SEV-2) or POL-09.4 (an Incident Commander is assigned for SEV-1/2).
- Not noted that S:255 says "failure modes from §7" when the failure modes are in §6 (a source typo, harmless).
- Not noted that `iam.create_approval` and `iam.get_approval` are GREEN but must be present in the mock (S:238).
- The R:47-78 dispositions omit the §1 summary (S:9) that DEFER is "defer to a human". This is not important.
- §6 (outside scope, but needed): the two failure modes (silent no-op and multi-step second-step failure) and the seed data. The seed data includes a compromise-flagged locked account, an account-takeover signal, an in-flight duplicate and approvals in all three states.
- The 5.1 irreversible list ("grant prod admin, disable MFA, permanent local admin, send Confidential data") is captured (R:97), but not mapped to the policies that govern each (see the table in section 5).

## 4. Ambiguities

### 4a. Resolved by the source (R:143-160 numbering)

- #1 (what "no compromise signal" means):
  - okta.risk_signals returns flags (compromise, MFA-fatigue, impossible-travel) (S:153).
  - An unlock is correct only when none are present (S:149, S:219).
  - §6 seeds a compromise-flagged lock (S:240).
  - Any flag (including MFA-fatigue or impossible travel) means RED/ESCALATE, not unlock.
  - What to do if the risk call itself fails is not stated (see 4b).
- #2 (grant_access args): S:133 says the approval must match "requester, target, parameters", so the call needs at least requester, target and parameters. The exact signature is still the implementer's choice.
- #3 (system names): S:9 names Okta, ServiceNow, IAM and the SOC. JIRA is S:3 and S:8. Directory, endpoint and assetmgmt are not named.
- #5 ("send Confidential data"): POL-05.3 says an external send needs a DLP exception with data owner approval, valid 30 days. There is no catalog tool for the send itself. The agent must not send, so route the approval or file the exception.
- #6 (who approves), partly resolved by the policies:
  - POL-10.2: manager approval, plus data owner for Restricted systems.
  - POL-03.4: manager approval for a USB exception.
  - POL-05.3: data owner for a DLP exception.
  - POL-04.6: an Endpoint Engineering exception for permanent admin.
  - POL-08.2: hiring manager for new-hire hardware.
  - Self-approval and separation of duties are still unstated.
- #7 (approval freshness): partly. A DLP exception is valid for 30 days (POL-05.3). Otherwise the only rule is to check immediately before executing (S:181, S:232).
- #10 (minutes): partly. The maximum is 60 per session (POL-04.4.6). Anything over 60 is not self-service (POL-04.6, permanent admin requires an Endpoint Engineering exception), so it should be routed or deferred, not auto-run.
- #11 (POL-09 containment instruction): POL-09.2 says do NOT power off, disconnect from the network (unplug Ethernet, disable Wi-Fi) and wait for SOC. POL-09.1 says report within 1 hour to security@helix.example or ext 4357.
- #13 (DEFER vs ASK): S:236 says in scope but underspecified means ASK_CLARIFICATION, and out of scope means DEFER. S:193 says that for defensible borderline cases the reasoning and safety are graded.
- #15 (who may authorize on behalf of others): partly, via the manager and data-owner relationships above. Tool-specific mapping is the implementer's choice.
- #17 (rollback): S:241 says "roll back or flag rather than report a half-done success". No rollback tool exists, so flagging via a ticket comment and escalation is the acceptable path.

### 4b. Genuinely open design decisions

- Behavior when the risk-signals call fails or times out. Recommendation: fail closed (no unlock, defer or ask).
- #8 / #2 exact matching schema for grant_access parameters.
- #9 definitions of lock epoch, calendar-day timezone, incident id source and session.
- #12 numeric confidence threshold.
- #14 name of the human queue(s).
- #16 no-reply timeout for Waiting for Customer.
- #18 secret-detection and redaction rules.
- #4 reversibility per tool.
- Self-approval and approver eligibility beyond the policy hints above.
- The PENDING handling in 2.2 above.
- Whether disable_mfa is ever legitimate. S:220 lists it as a privileged change that is drafted and routed, but POL-01.3 makes MFA "mandatory for every corporate application" and S:133 says policy-prohibited requests get no approval filed. Both readings are defensible; the safe default is never self-execute, and treat any in-band or injected request as DEFER/refuse with no approval filed.

## 5. Corrected tool -> policy -> disposition mapping

"Explicit" means the source ties tool to policy or disposition in so many words. "Inferred" means the connection is mine, based on subject-matter overlap.

| Tool | Class / key | Policy section(s) | Basis | Disposition |
|---|---|---|---|---|
| jira.get/comment/transition/add_label/link_issues | GREEN, n/a | none (workflow). Comments must cite the policy that grounds the decision | Explicit (S:141, S:226-227, S:212) | all six (comment/close/transition/label/link) |
| directory.lookup_user / verify_manager | GREEN read-only | POL-10.2 (manager approval), POL-03.4 (manager approval), POL-08.2 (hiring manager) | Tool use required: explicit (S:147, S:223-224). Policy link: inferred | precondition to AUTO_ACTION and PROPOSE; failure leads to DEFER |
| okta.risk_signals | GREEN read-only | POL-09.1 and 9.3 for the escalation it can trigger | Check-before-unlock: explicit (S:153). Policy link: inferred | precondition to unlock; signal found leads to ESCALATE_INCIDENT |
| okta.unlock_account | GREEN*, account + lock epoch | POL-01.4 (5 failed attempts, lock, self-service after 15 min, else Service Desk) | Tool-to-policy: inferred. GREEN-or-RED rule: explicit (S:149) | AUTO_ACTION if no signal; ESCALATE_INCIDENT if signal |
| okta.send_password_reset | GREEN, user + calendar day | POL-01.1/1.2 (password rules), POL-01.4 | Inferred | AUTO_ACTION (verified owner, self only). On behalf of someone else: DEFER or ASK (S:223) |
| okta.revoke_sessions / force_password_reset | GREEN, user + incident | POL-09.2 (containment), POL-09 generally | "containment instruction from POL-09" is explicit for the user message (S:209). Tool-to-section: inferred | ESCALATE_INCIDENT (explicit, S:209) |
| servicenow.create_request | GREEN, user + item + day | Software: POL-04.1/4.2. USB: POL-03.4. Travel: POL-02.5. DLP exception: POL-05.3 (inferred; not in the examples). Permanent local admin exception: POL-04.6 | Examples (software, USB, Travel): explicit (S:165). Section mapping: inferred, though each policy text names the ServiceNow form/ticket | AUTO_ACTION (files only; does not grant) |
| endpoint.grant_admin | GREEN, user + session, minutes <= 60 | POL-04.6 | Explicit (S:169) | AUTO_ACTION if own laptop and <= 60. Beyond that (permanent, server/prod): route or DEFER |
| assetmgmt.create_case | GREEN, asset + type | Lost/Stolen: POL-08.3. Offboarding kit: POL-08.5. Restricted-data loss: POL-09.6 (SEV-2) | Case types: explicit (S:173). Policy mapping: inferred | AUTO_ACTION; plus ESCALATE_INCIDENT if Restricted data (inferred from POL-09.6) |
| iam.create_approval | GREEN (routing), request hash | Approver rules: POL-10.2, POL-05.3, POL-03.4, POL-04.6 | Tool role: explicit (S:177, S:206). Approver mapping: inferred | PROPOSE_FOR_APPROVAL (no record, or PENDING per S:133) |
| iam.get_approval | GREEN read-only | none; governed by S:181, S:232 | Explicit | PROPOSE_FOR_APPROVAL; re-check immediately before every AMBER call |
| iam.grant_access | AMBER, approval id | POL-10.2 (beyond-template access), POL-10.5/10.6 (contractor, shared accounts: shared accounts prohibited, so no approval), POL-02.6 (prod via CyberArk) | Class and gate: explicit. Policy mapping: inferred | PROPOSE_FOR_APPROVAL; execute only on APPROVED match; prohibited requests get DEFER with no approval filed |
| okta.disable_mfa | AMBER, approval id | POL-01.3 (MFA mandatory; tension, see 4b), POL-01.6 (privileged users need a YubiKey) | Class and gate: explicit (S:185, S:220). Policy mapping: inferred | PROPOSE_FOR_APPROVAL at most; injected requests: DEFER, flag, no approval filed (S:233) |
| soc.open_incident / soc.page_oncall | RED, ticket id | POL-09.1 (report), 9.3 (sev), 9.4 (IC), 9.6 (lost device with Restricted data is SEV-2) | Policy POL-09: explicit (S:209). Specific sections: inferred | ESCALATE_INCIDENT only; never closed as resolved |

Disposition-level grounding:
- ANSWER_ONLY: cite the exact policy section; no tool.
- ASK_CLARIFICATION and DEFER_HUMAN: cite the reason or the policy gap.
- DEFER covers the §5.6 cases and prohibited or injected requests.
