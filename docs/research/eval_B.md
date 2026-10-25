# Evaluation of Reader B (reader_B.md) against assignment.txt lines 36-127, with tags checked against lines 128-215

Line refs are to reader_B.md unless marked "src".

## (1) Verdict

- **Facts: PASS.** All 60 section summaries (reader lines 23-100) and all 10 index rows (lines 9-18) match the source. Every duration, threshold, system name, owner, approver and effective date is exact. I found no invented detail and no dropped detail.
- **Actionable-hook tags: FAIL as written. This section needs revision before an agent uses it.** The reader tags by wording, not by tool. It never maps a section to the §3 tool catalog or a §4 disposition. That produces:
  - Mis-tags that would route things to `iam.create_approval` when the right move is a GREEN `servicenow.create_request`.
  - Missing hooks for the most common action tickets: password reset, MFA, lost device, return kit.
  - One safety-relevant omission: 1.4 unlock with no compromise check.
- **Tensions: roughly 5 real, 14 spurious or duplicated.** The most important real tensions are missing (see part 4).
- Net: the summaries are safe to ground on. Do not use the section 3 tags as dispositions.

## (2) Factual errors

No wrong numbers, names, approvers or dates. Minor issues only:

- Line 39 (3.1): "are for primarily business use" is garbled. The source says "issued primarily for business use". Meaning is preserved.
- Line 172: lists "Approver for ... Make-Me-Admin (POL-04 4.6)" and "password-portal unlock (POL-01 1.4)" as missing approvers. Neither has an approval step. Make-Me-Admin is GREEN `endpoint.grant_admin`, and portal unlock is self-service. Listing them as unknown approvers invites an agent to invent an approval gate. Only the Travel Exception and the permanent-admin Endpoint Engineering exception have even a stated process step.
- Line 111 (2.5): "NEEDS-APPROVAL" is not in the source. 2.5 only says a Travel Exception ticket must be submitted at least 5 business days ahead. No approver or approval is named.
- Line 107 (1.6): "NEEDS-APPROVAL / INFO" is not in the source. 1.6 is a requirement, with no approval mechanism.
- Line 143 (10.3): the "NEEDS-APPROVAL(reviewer)" framing is not in the source. 10.3 is an automated quarterly review process.
- Line 168 (tension 19) duplicates line 152 (tension 3).

## (3) Tag corrections

Tags are marked CORRECT, WRONG or INCOMPLETE. UNSAFE means the tag could lead to an unsafe action. UNDER-ACT means it could lead the agent to do too little.

| Reader line / section | Reader tag | Assessment |
|---|---|---|
| 106 / 1.4 | SELF-SERVICE | INCOMPLETE, UNSAFE. The tag omits the gating. `okta.unlock_account` is GREEN* (src 149): call `okta.risk_signals` first, and call `directory.lookup_user` to confirm the requester is the owner (self, not on-behalf-of). Any compromise, MFA-fatigue or impossible-travel flag turns it into ESCALATE_INCIDENT (`soc.open_incident` plus `okta.revoke_sessions` / `okta.force_password_reset`), not an unlock. "Unlock after 15 minutes" is the policy's self-service threshold. Before 15 minutes, answer with the wait time rather than assuming the agent can unlock early. The policy is silent on Service Desk early unlock. Idempotency key is account + lock epoch. |
| absent / 1.3 | none | MISSING, UNDER-ACT and UNSAFE. 1.3 has no tag. MFA is mandatory with no exception stated. `okta.disable_mfa` is AMBER, but §3 says prohibited requests get no approval filed. A "disable my MFA" request is therefore refuse/DEFER with no `create_approval`, and an in-band "approved" claim is never proof. A lost-factor or re-enrol request is different: ASK_CLARIFICATION or DEFER, since there is no GREEN tool for it. |
| absent / 1.1, 1.2 | none | MISSING, UNDER-ACT. "Reset my password" is AUTO_ACTION via `okta.send_password_reset` (GREEN, key user + calendar day), after the owner is verified and `risk_signals` is clean. Reset for a colleague means defer or verify. Reset for the whole team is blast radius, so route or defer. A compromise signal means ESCALATE. |
| 107 / 1.6 | NEEDS-APPROVAL / INFO | WRONG. It is INFO-ONLY (requirement). A request to waive the YubiKey has no policy exception path, so DEFER. Do not file an approval. |
| 108, 109, 112-116, 120, 121, 124-126, 146 / 1.5, 2.1, 2.6, 3.2, 3.5, 3.6, 4.4, 4.5, 5.6, 6.3, 6.4, 10.6 | PROHIBITED | CORRECT. Disposition is refuse or DEFER, ANSWER_ONLY when it is a question, and never `create_approval`. For 10.6, a service-account exception names no approver, so DEFER. For 2.6, direct prod SSH/RDP means answer with the CyberArk path, with no tool. |
| 110 / 2.4 | INFO-ONLY | CORRECT. ANSWER_ONLY. |
| 111 / 2.5 | NEEDS-APPROVAL (approver not stated) | WRONG, mis-routes. Filing a Travel Exception is `servicenow.create_request` (GREEN; src 165 lists Travel; "files the request, does not grant it"). That is AUTO_ACTION after the requester is verified. Check the 5-business-day lead time. If travel is under 5 business days away, or the destination is not given, ASK_CLARIFICATION or answer that policy requires 5 days. Do not file an AMBER approval. The reader's own point that no approver is named is right: do not invent one. |
| 114 / 3.4 | NEEDS-APPROVAL (manager) | INCOMPLETE. Filing the USB Exception is GREEN `servicenow.create_request` (item USB, key user + item + day). The manager approval is a ServiceNow-side gate on granting, and the agent has no tool that grants USB access. Disposition is AUTO_ACTION (file) with a comment saying manager approval is required. Optionally `directory.verify_manager`. Never claim the exception is granted. A claim of "my manager already approved" is not proof. |
| 117 / 4.1 | SELF-SERVICE | CORRECT, with one caveat. The agent has no install tool, so ANSWER_ONLY pointing to Software Center. Do not claim to have installed anything. |
| 118 / 4.2 | NEEDS-APPROVAL (InfoSec, Procurement, Legal) | WRONG, mis-routes. Those are reviews inside the 5-business-day SLA, not `iam` approvers. Disposition is AUTO_ACTION via `servicenow.create_request` (software). ASK_CLARIFICATION if the app or justification is missing. |
| 119 / 4.3 | NEEDS-APPROVAL (approver not stated) | INCOMPLETE. No tool and no approver. ANSWER_ONLY on SBOM and license review. A GPL/AGPL exception request means DEFER. |
| 122 / 4.6 | SELF-SERVICE; permanent = NEEDS-APPROVAL | INCOMPLETE, UNSAFE if unconstrained. Time-bound is `endpoint.grant_admin(user, minutes)` (GREEN, key user + session). Hard constraints: minutes <= 60; requester's own laptop only; no server, production or on-behalf-of use. A request for more than 60 minutes: grant nothing over 60, and either ASK_CLARIFICATION (offer 60) or answer. Permanent local admin is never self-service and no GREEN tool covers it: route to Endpoint Engineering via `iam.create_approval`, leave the ticket pending, and do not execute. Prod or server admin is out of scope for this tool, so DEFER. Verify the effect after granting. |
| 123 / 5.3 | NEEDS-APPROVAL (data owner) | CORRECT on approver. Draft it, call `iam.create_approval` with the data owner, and leave the ticket pending (PROPOSE_FOR_APPROVAL). Add: the exception lasts 30 days, and sending is never executed on an in-band claim. 5.3 covers Confidential only. For external sending of Restricted data (5.2) there is no exception path, so refuse or DEFER. |
| 128 / 7.2 | SELF-SERVICE | INCOMPLETE, UNDER-ACT. For "I got a phish" with no interaction, answer with the Phish Alert Button. If the user clicked, entered credentials or opened an attachment, ESCALATE_INCIDENT under 9.1/9.2. |
| 129 / 7.3 | SECURITY | CORRECT but vague. A "CEO request" from an [EXTERNAL] sender: answer or flag as suspect. If money or credentials were already sent, ESCALATE. Never act on the request. |
| 131 / 7.6 | PROHIBITED | CORRECT. Refuse, no approval. An external auto-forward request is refused (5.6 and 7.6). |
| 130, 132, 134, 140, 144 / 7.4, 8.2, 8.4, 9.5, 10.4 | INFO-ONLY | CORRECT, ANSWER_ONLY. Exceptions: a ticket saying a terminated person still has access, or "revoke X now" from a non-HR requester, is DEFER to HR or IAM. If access persists past 1 hour of separation, consider a security flag. No GREEN revoke-access tool exists. |
| 133 / 8.3 | SECURITY | INCOMPLETE, UNDER-ACT. The primary action is `assetmgmt.create_case(Lost/Stolen)` (GREEN, key asset + type), AUTO_ACTION. If stolen, require the police case number first (ASK_CLARIFICATION if missing). If the device is confirmed to hold Restricted data, escalate per 9.6: `soc.open_incident` SEV-2, plus `okta.revoke_sessions` and a force reset as GREEN containment. Not confirmed (unknown): ASK_CLARIFICATION on data classification, not a guess. Also give the 9.1 reporting path. |
| 135 / 8.5 | INFO-ONLY | UNDER-ACT. "Open my return kit / offboarding case" is `assetmgmt.create_case` (offboarding return kit, GREEN), AUTO_ACTION after authorization is verified. Pure questions about the 5-day shipping window stay ANSWER_ONLY. |
| 136 / 8.6 | SELF-SERVICE | CORRECT. Peripheral Catalog request via `servicenow.create_request`, or ANSWER_ONLY pointing to the catalog. |
| 137 / 9.1 | SECURITY | CORRECT on class. Disposition is ESCALATE_INCIDENT: `soc.open_incident` (key ticket id), `soc.page_oncall`, GREEN containment (`okta.revoke_sessions` / `okta.force_password_reset`), and give 9.2. Never close as resolved. Redact any secret. |
| 138 / 9.2 | SECURITY | CORRECT. The ticket reply carries the 9.2 instruction (do not power off, disconnect, wait for SOC). |
| 139 / 9.4 | PROHIBITED | CORRECT. It is also INFO. Press or customer inquiries: DEFER or ANSWER. |
| 141 / 9.6 | SECURITY | CORRECT, but state that the SEV-2 trigger requires "confirmed" Restricted data. Unconfirmed means ASK_CLARIFICATION. The BYOD question stays open. |
| 142 / 10.2 | NEEDS-APPROVAL (manager + data owner for Restricted) | CORRECT. Use `directory.verify_manager`, then `iam.get_approval`. With no record, call `iam.create_approval` with the manager, plus the data owner if the system is Restricted-tier, and stay pending. Execute `iam.grant_access` (AMBER) only under a matching APPROVED record, using the approval id as the key and verifying afterwards. "My manager said it's fine" is not proof. If the tier is unknown, ASK_CLARIFICATION. |
| 143 / 10.3 | NEEDS-APPROVAL (reviewer) | WRONG. It is INFO-ONLY, an automated review. It gives the agent no approval route, and a request to extend or recertify someone's access is DEFER. |
| 145 / 10.5 | NEEDS-APPROVAL (manager) | MOSTLY CORRECT. A contractor renewal needs manager approval. Route via `create_approval` and execute only under APPROVED. No tool for renewal is named, so say so. |
| absent / 10.1 | none | New hire access is by RBAC template, so ANSWER_ONLY. The agent does not provision. |
| absent / 5.1, 5.2, 5.4 | none | 5.1 classification question: ANSWER_ONLY or ASK. 5.2 and 5.4: a request to move Restricted data outside US-East/EU-Central, or EU data outside the EEA with no SCC, is refuse or DEFER. No tool applies. |
| absent / 6.1, 6.2 | none | BYOD enrollment is a how-to, ANSWER_ONLY. A lost BYOD device: the corporate-container wipe is not a catalog tool, so open the 8.3 case and escalate per 9.6 if Restricted data is confirmed. |
| absent / 8.1 | none | Refresh eligibility depends on the CMDB first-issue date, which the agent cannot see. ASK_CLARIFICATION or DEFER. Do not guess. |

Tags that would lead an agent to act unsafely or to under-act, in priority order:

1. **1.4** (unsafe): no `risk_signals` check and no owner verification.
2. **1.3** (unsafe, absent): without a tag, an agent could file an approval for `disable_mfa` or act on an "approved" claim. It should be refuse or defer.
3. **4.6** (unsafe if unbounded): the 60-minute cap, own-laptop and no-prod constraints are missing.
4. **8.3 and 9.6** (under-act): no `assetmgmt.create_case`, and no SEV-2 escalation chain.
5. **2.5, 4.2, 3.4** (over-routing to AMBER): wrongly pushes GREEN `servicenow.create_request` actions into the approval flow. Safe, but an AUTO_ACTION would be scored as a miss.
6. **1.6, 10.3** (spurious NEEDS-APPROVAL): the agent may file approvals for things that are not approvals.
7. **1.1/1.2 reset** and **8.5 return kit** (under-act): no tag for common GREEN actions.

## (4) Real vs spurious tensions

Numbers refer to reader lines 150-168.

**Real (keep):**

- **3 and 19 (merge)**: 8.3's 24-hour ticket vs 9.1's 1-hour SOC report vs 9.6's SEV-2.
  - Resolution: both apply. File the case, and if a suspected incident exists, report it to the SOC within 1 hour.
  - Reconcile it with 9.2: "do not power off, disconnect" cannot be done for a lost device.
- **4**: BYOD lost device. 6.2 limits the wipe to the corporate container. 8.3 and 9.6 say "devices". Whether they cover BYOD is unspecified, so do not guess.
- **5**: 7.2 Phish Alert Button vs 9.1 SOC within 1 hour. Phish Alert is for no-interaction reports. A click or credential entry becomes an incident.
- **1 and 2 (merge)**: Approved Country List (POL-02, "Germany") vs approved geographies (POL-05 US-East/EU-Central). The units are unclear. Do not infer one list from the other.
- **13**: data owner is the approver for both DLP (5.3) and Restricted access (10.2). It is the same role, but no identity source is stated, so the agent cannot assume a named person.

**Spurious or low-value (drop):**

- **6, 7**: complementary controls (MFA plus YubiKey; YubiKey plus CyberArk). Both apply, so there is no conflict.
- **8, 9**: speculative gaps (rotation for service accounts; contractor as standard account). The policy simply does not say. These are unknowns, not tensions.
- **10**: 3.1 permits only use that does not "violate any other policy", so 2.1 does not conflict with it.
- **11, 18**: the reader itself says "consistent".
- **12**: different data sets.
- **14**: hardware request and access provisioning are separate processes, so there is no conflict.
- **15, 16, 17**: restatements or unrelated.

**Real tensions the reader missed (and that matter for the agent):**

- **1.4 vs §3 okta.unlock_account**: self-service unlock after 15 minutes conflicts with "GREEN only when no compromise signal, otherwise RED".
- **1.3 vs `okta.disable_mfa` (AMBER)**: the tool exists, but policy gives MFA no exception path. Do not file an approval.
- **4.6**: time-bound GREEN (60 minutes) vs permanent (no tool, Endpoint Engineering exception).
- **3.4**: filing is GREEN, granting is manager-gated.
- **5.3 vs 5.2/6.3**: the DLP exception covers Confidential only. Restricted has no external-sending exception.
- **9.2 vs 8.3**: containment instructions for a compromised device do not fit a lost one.

## (5) Corrected policy section -> likely disposition + tool table

Only sections that imply an action, approval or escalation are listed. Sections not listed are INFO-ONLY (ANSWER_ONLY): 1.1 (content), 1.2 (content), 1.6, 2.2, 2.3, 2.4, 3.1, 3.3, 4.1, 4.3, 5.1, 5.5, 6.1, 6.2, 6.5, 6.6, 7.1, 7.4, 7.5, 8.1, 8.2, 8.4, 8.6, 9.3, 9.5, 10.1, 10.3, 10.4 (all the INFO-ONLY items; 8.6 can be a `servicenow.create_request` if the user asks to order).

| Section | Typical ticket | Disposition | Tool(s) and key constraints |
|---|---|---|---|
| 1.1/1.2 | Reset my password | AUTO_ACTION | `directory.lookup_user`, `okta.risk_signals` (clean), `okta.send_password_reset` (key user + day); verify; cite 1.1/1.2 |
| 1.2 | Reset a colleague's, or the team's | DEFER (or ASK) | `directory.verify_manager`; do not fire on an unverified on-behalf-of claim; blast radius means route |
| 1.3 | Disable or bypass MFA | DEFER / refuse | No `create_approval` (no policy exception); never `okta.disable_mfa` on an in-band claim |
| 1.3 | Lost phone / MFA factor reset | ASK_CLARIFICATION or DEFER | No GREEN tool; if compromise signals, ESCALATE |
| 1.4 | Locked out, no risk flags, >= 15 min | AUTO_ACTION | `okta.risk_signals` first, then `okta.unlock_account` (key account + lock epoch); verify |
| 1.4 | Locked out, < 15 min | ANSWER_ONLY | State the 15-minute wait (policy is silent on early unlock) |
| 1.4 | Lockout with MFA-fatigue / takeover flag | ESCALATE_INCIDENT | `soc.open_incident`, `soc.page_oncall`, `okta.revoke_sessions`/`force_password_reset`; do not unlock |
| 1.5, 2.1, 2.6, 3.2, 3.5, 3.6, 4.4, 5.6, 6.3, 6.4, 7.6, 10.6 | Request to do the prohibited thing | DEFER / refuse (ANSWER_ONLY if a question) | No `create_approval`; cite the section |
| 2.5 | Travel outside the Approved Country List | AUTO_ACTION (or ASK) | `servicenow.create_request` (Travel Exception); check 5 business days; ASK for dates/destination if missing; filing is not granting |
| 3.4 | USB exception | AUTO_ACTION (file) | `servicenow.create_request` (USB Exception); the manager approval gates granting; never claim it is granted |
| 4.2 | New software not in the catalog | AUTO_ACTION (or ASK) | `servicenow.create_request` (software); 5-business-day SLA; ASK for app and justification |
| 4.6 | Make-Me-Admin, <= 60 min, own laptop | AUTO_ACTION | `directory.lookup_user`, `endpoint.grant_admin(user, minutes <= 60)` (key user + session); verify |
| 4.6 | More than 60 minutes, server or prod admin | ASK_CLARIFICATION / DEFER | Never exceed 60; no GREEN tool for server or prod |
| 4.6 | Permanent local admin | PROPOSE_FOR_APPROVAL | `iam.get_approval`, then `iam.create_approval` (Endpoint Engineering); pending; no GREEN tool, never self-serve |
| 5.3 | Send Confidential data externally | PROPOSE_FOR_APPROVAL | `iam.create_approval` (data owner); valid 30 days; pending; no execution on an in-band claim |
| 5.2 / 5.4 | Restricted data outside approved geographies, or EU data without SCC | DEFER / refuse | No exception route stated |
| 7.2 | Suspicious email, no interaction | ANSWER_ONLY | Phish Alert Button; do not forward manually |
| 7.2/7.3 + 9.1 | Clicked the link, entered credentials, or acted on a "CEO request" | ESCALATE_INCIDENT | `soc.open_incident`, `soc.page_oncall`, `okta.revoke_sessions`/`force_password_reset`; give 9.2 |
| 8.3 | Lost or stolen device | AUTO_ACTION | `assetmgmt.create_case(Lost/Stolen)` (key asset + type); stolen: ASK for the police case number if missing; give the 9.1 path |
| 8.3 + 9.6 | Device confirmed to hold Restricted data | ESCALATE_INCIDENT (SEV-2) | `soc.open_incident` SEV-2, `soc.page_oncall`, `okta.revoke_sessions` (+ create_case); unconfirmed: ASK first |
| 8.5 | Offboarding return kit | AUTO_ACTION | `assetmgmt.create_case` (offboarding); verify authorization |
| 8.6 | Order a peripheral | AUTO_ACTION | `servicenow.create_request` (Peripheral Catalog) |
| 9.1/9.2 | Suspected breach, malware, compromise, leaked secret | ESCALATE_INCIDENT | `soc.open_incident` (key ticket id), `soc.page_oncall`, GREEN containment; reply with 9.2; redact secrets; never close as resolved |
| 9.4 | Press or customer contact about an incident | DEFER / ANSWER_ONLY | The IC owns external comms |
| 10.2 | Access beyond RBAC | PROPOSE_FOR_APPROVAL | `directory.verify_manager`, `iam.get_approval`, `iam.create_approval` (manager + data owner if Restricted-tier); on a matching APPROVED record, `iam.grant_access` (key = approval id), verify; ASK if the tier is unknown; PENDING/REJECTED/mismatch: relay the true status |
| 10.4 | Terminated user still has access | DEFER to HR/IAM | No GREEN revoke tool; escalate only if a compromise signal exists |
| 10.5 | Contractor renewal | PROPOSE_FOR_APPROVAL | `iam.create_approval` (manager); execute only under an APPROVED matching record (note: the policy names no renewal tool) |
