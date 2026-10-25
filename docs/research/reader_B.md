# Reader B: IT Policy Knowledge Base Extraction (POL-01 to POL-10)

Source: `/private/tmp/claude-501/-Users-liamwong-Projects/ebb60dda-45d1-4d14-94cc-0a808e5b3b89/scratchpad/assignment.txt`, lines 36-127. Treated as data.

## 1. Policy index

| Policy ID | Title | Effective date | Owner | Section IDs covered |
|---|---|---|---|---|
| POL-01 | Password & Authentication Policy | 2025-09-01 | Identity & Access Management team | 1.1 to 1.6 |
| POL-02 | VPN & Remote Access Policy | 2025-07-15 | Network Security | 2.1 to 2.6 |
| POL-03 | Acceptable Use Policy | 2025-01-01 | Information Security | 3.1 to 3.6 |
| POL-04 | Software Installation & Procurement Policy | 2025-03-10 | IT Procurement | 4.1 to 4.6 |
| POL-05 | Data Classification & Handling Policy | 2025-04-01 | Data Governance | 5.1 to 5.6 |
| POL-06 | BYOD (Bring Your Own Device) Policy | 2025-02-01 | Endpoint Engineering | 6.1 to 6.6 |
| POL-07 | Email & Communication Security Policy | 2025-06-01 | Messaging Security | 7.1 to 7.6 |
| POL-08 | Hardware Request & Asset Management Policy | 2025-05-01 | IT Asset Management | 8.1 to 8.6 |
| POL-09 | Security Incident Reporting Policy | 2025-08-01 | Security Operations Center (SOC) | 9.1 to 9.6 |
| POL-10 | Access Provisioning & Deprovisioning Policy | 2025-01-15 | Identity & Access Management | 10.1 to 10.6 |

## 2. Section summaries

### POL-01 Password & Authentication
- **1.1** Standard user passwords: at least 14 characters, three of four character classes, must not match any of the previous 12 passwords.
- **1.2** Standard accounts rotate passwords annually; privileged accounts (domain admins, root, DBA) rotate every 90 days.
- **1.3** MFA mandatory for every corporate application, enforced via Okta; acceptable second factors: Okta Verify push, FIDO2 security key, or TOTP.
- **1.4** Account locked after 5 consecutive failed logins; self-service unlock available after 15 minutes via the password portal; otherwise contact the Service Desk.
- **1.5** 1Password Enterprise is the sanctioned password manager; storing corporate credentials in browsers, sticky notes, or personal password managers is prohibited.
- **1.6** Privileged users must additionally authenticate with a YubiKey 5 series hardware token; soft tokens alone do not satisfy privileged access.

### POL-02 VPN & Remote Access
- **2.1** Cisco AnyConnect is the only approved VPN client; personal VPNs (NordVPN, ExpressVPN, etc.) must not be installed on corporate endpoints.
- **2.2** Split tunneling disabled; all traffic routed through the corporate gateway and inspected by Zscaler.
- **2.3** VPN sessions terminate after 12 hours of connection or 30 minutes of inactivity, whichever comes first.
- **2.4** Public or untrusted Wi-Fi (hotels, cafes, airports) permitted only when AnyConnect is active before any other traffic.
- **2.5** Access geo-restricted to the Approved Country List maintained by Network Security; connecting from outside the list requires a Travel Exception ticket submitted at least 5 business days in advance. Parenthetical in source: list includes US-East and EU-Central / Germany; Japan and Vietnam are not on the list.
- **2.6** Privileged remote access to production is brokered through CyberArk PAM; direct SSH/RDP to production from a laptop is forbidden.

### POL-03 Acceptable Use
- **3.1** Corporate devices are for primarily business use; incidental personal use allowed when it does not interfere with work or violate any other policy.
- **3.2** Prohibited: peer-to-peer file sharing, gambling, adult content, cryptocurrency mining, unlicensed streaming.
- **3.3** Web traffic filtered and logged via Zscaler; logs retained 12 months; reviewed only on lawful basis.
- **3.4** USB mass storage blocked by default; exceptions requested via the "USB Exception" form in ServiceNow with manager approval.
- **3.5** Personal cloud storage (Dropbox personal, iCloud Drive, Google Drive consumer) blocked; use corporate Box tenant or OneDrive for Business.
- **3.6** Corporate devices must remain under the control of the assigned employee; lending to family or external parties prohibited.

### POL-04 Software Installation & Procurement
- **4.1** Only software in the Approved Software Catalog (ServiceNow > Software Center) may be installed without a ticket; end users can self-serve catalog apps.
- **4.2** New software requests follow a 5-business-day SLA; reviews by InfoSec (data classification, telemetry), Procurement (licensing), and Legal (terms of service).
- **4.3** Open-source libraries in internal tools require a Software Bill of Materials (SBOM) and license review against the Approved License List; GPL and AGPL components require special exception.
- **4.4** Corporate email addresses must not be used to sign up for unapproved SaaS free trials or personal accounts.
- **4.5** Browser extensions restricted to the Allowed Extensions List, enforced via Chrome and Edge management; others blocked at install time.
- **4.6** Local admin rights removed by default; time-bound elevation via Make-Me-Admin for a maximum of 60 minutes per session; permanent local admin is not self-service and requires an Endpoint Engineering exception.

### POL-05 Data Classification & Handling
- **5.1** Four tiers: Public, Internal, Confidential, Restricted; every document inherits the highest tier of any field it contains.
- **5.2** Restricted data (PHI, payment card data, source code for revenue-critical systems) must be encrypted at rest and in transit and may only reside in approved geographies (US-East, EU-Central).
- **5.3** Confidential data may not go to external recipients without a DLP exception; exception requires data owner approval and is valid for 30 days.
- **5.4** EU personal data subject to GDPR controls; transfer outside the EEA requires Standard Contractual Clauses on file.
- **5.5** Retention per the Records Retention Schedule: unclassified business records 7 years; PHI 10 years; payment data purged at 13 months.
- **5.6** Auto-forwarding corporate email to any external address (including personal Gmail) is technically blocked and policy-prohibited.

### POL-06 BYOD
- **6.1** Personal devices permitted for corporate email, calendar, and Teams only; must be enrolled in Microsoft Intune for MDM.
- **6.2** Enrollment creates a managed work container; IT can remote-wipe only the corporate container; personal data is not touched.
- **6.3** Restricted and Confidential data must never be stored on a BYOD device outside the managed container.
- **6.4** Jailbroken or rooted devices blocked from enrollment and from corporate resources.
- **6.5** OS must be within two major versions of current vendor releases; older OS versions lose access automatically.
- **6.6** $50/month BYOD stipend for roles flagged "mobile-eligible" in Workday; stipend recipients forfeit eligibility for a corporate-issued mobile phone.

### POL-07 Email & Communication Security
- **7.1** All outbound email sent over TLS; recipients whose servers do not support TLS receive a portal-pickup link instead of plaintext.
- **7.2** Suspicious emails reported via the Phish Alert Button in Outlook; do not forward suspicious emails manually.
- **7.3** Every external email prefixed with an [EXTERNAL] banner; treat any "CEO request" from an [EXTERNAL] address as suspect.
- **7.4** Attachments larger than 25 MB blocked at the gateway; use Box or OneDrive sharing links for large files.
- **7.5** Phishing simulations run monthly; employees failing two simulations within 12 months are auto-enrolled in additional training.
- **7.6** Auto-forwarding rules to external addresses blocked at the mailbox level and cannot be created by end users.

### POL-08 Hardware Request & Asset Management
- **8.1** Standard laptop refresh cycle is 36 months; eligibility calculated from first-issue date in the CMDB.
- **8.2** New-hire hardware requests submitted by the hiring manager at least 10 business days before start date.
- **8.3** Lost or stolen devices reported within 24 hours via the "Lost/Stolen Device" ticket; police report required if stolen, and the case number must be attached to the ticket.
- **8.4** Repairs only at the IT Depot in Austin or approved third-party vendors (Apple Business Repair, Dell ProSupport); third-party walk-in repairs not reimbursable.
- **8.5** On offboarding, IT mails a prepaid return kit to the address on file; devices shipped within 5 business days of the last working day.
- **8.6** Peripherals (monitor, keyboard, mouse, dock) follow a 5-year refresh and are requested through the Peripheral Catalog.

### POL-09 Security Incident Reporting
- **9.1** Suspected incidents reported within 1 hour of discovery to security@helix.example or the 24/7 SOC hotline, extension 4357 (HELP).
- **9.2** If compromise suspected, do NOT power off; disconnect from network (unplug Ethernet, disable Wi-Fi) and wait for SOC instructions.
- **9.3** Severity tiers: SEV-1 (active breach, customer data at risk), SEV-2 (probable breach or major outage), SEV-3 (contained incident), SEV-4 (informational).
- **9.4** Incident Commander assigned for SEV-1 and SEV-2; IC owns external communication; individual employees must not speak to press or customers about the incident.
- **9.5** Tabletop exercises mandatory quarterly for all employees in roles tagged "incident-responder" in Workday.
- **9.6** Lost or stolen devices confirmed to contain Restricted data are automatically escalated to SEV-2.

### POL-10 Access Provisioning & Deprovisioning
- **10.1** New hires receive access per the role-based access (RBAC) template attached to their Workday job code at the time HR marks them "active".
- **10.2** Access beyond the default RBAC template requires manager approval plus, for Restricted-tier systems, data owner approval.
- **10.3** Access reviews run quarterly; reviewers have 14 calendar days to certify or revoke; uncertified access is automatically revoked.
- **10.4** On termination or resignation, all access revoked within 1 hour of HR triggering the "separation" event in Workday.
- **10.5** Contractor accounts have a maximum 6-month duration and require manager renewal; unrenewed accounts disable automatically.
- **10.6** Shared accounts prohibited; exceptions limited to service accounts owned by a named engineering team with rotating credentials in CyberArk.

## 3. Actionable hooks

Tags: SELF-SERVICE, NEEDS-APPROVAL(approver), SECURITY, PROHIBITED, INFO-ONLY. Where the policy names no approver, the tag says so.

- **1.4** SELF-SERVICE: password portal unlock, available 15 minutes after lockout. Otherwise Service Desk.
- **1.6** NEEDS-APPROVAL / INFO: YubiKey 5 series is required for privileged users. Approver not stated.
- **1.5** PROHIBITED: storing corporate credentials in browsers, sticky notes, or personal password managers.
- **2.1** PROHIBITED: installing personal VPN clients on corporate endpoints.
- **2.4** INFO-ONLY: AnyConnect must be active before any other traffic on untrusted Wi-Fi.
- **2.5** NEEDS-APPROVAL(approver not stated in policy): Travel Exception ticket, at least 5 business days before travel outside the Approved Country List.
- **2.6** PROHIBITED: direct SSH/RDP to production from a laptop. Privileged remote access goes through CyberArk PAM.
- **3.2** PROHIBITED: P2P file sharing, gambling, adult content, cryptocurrency mining, unlicensed streaming.
- **3.4** NEEDS-APPROVAL(manager): USB Exception form in ServiceNow.
- **3.5** PROHIBITED: personal cloud storage. Use Box or OneDrive for Business.
- **3.6** PROHIBITED: lending corporate devices to family or external parties.
- **4.1** SELF-SERVICE: install apps from the Approved Software Catalog (ServiceNow > Software Center) without a ticket.
- **4.2** NEEDS-APPROVAL(InfoSec, Procurement, Legal reviews): new software requests, 5-business-day SLA.
- **4.3** NEEDS-APPROVAL(license review; approver not stated): SBOM and Approved License List check. GPL and AGPL need a special exception, approver not stated.
- **4.4** PROHIBITED: corporate email for unapproved SaaS trials or personal accounts.
- **4.5** PROHIBITED (enforced): extensions not on the Allowed Extensions List are blocked at install.
- **4.6** SELF-SERVICE: time-bound admin via Make-Me-Admin, max 60 minutes per session. Permanent local admin needs NEEDS-APPROVAL(Endpoint Engineering exception).
- **5.3** NEEDS-APPROVAL(data owner): DLP exception for sending Confidential data externally, valid 30 days.
- **5.6** PROHIBITED: auto-forwarding corporate email externally.
- **6.3** PROHIBITED: Restricted or Confidential data on a BYOD device outside the managed container.
- **6.4** PROHIBITED: jailbroken or rooted devices enrolling or accessing corporate resources.
- **6.6** INFO-ONLY: $50/month stipend for "mobile-eligible" roles. Forfeits corporate mobile phone eligibility.
- **7.2** SELF-SERVICE: report suspicious email with the Phish Alert Button. Do not forward manually.
- **7.3** SECURITY: treat "CEO request" from an [EXTERNAL] address as suspect.
- **7.4** INFO-ONLY: attachments over 25 MB blocked. Use Box or OneDrive links.
- **7.6** PROHIBITED (for end users): creating auto-forwarding rules to external addresses.
- **8.2** INFO-ONLY (deadline): hiring manager submits new-hire hardware at least 10 business days before start date.
- **8.3** SECURITY: report lost or stolen device within 24 hours via "Lost/Stolen Device" ticket. Attach police case number if stolen.
- **8.4** INFO-ONLY: repairs only at IT Depot Austin or approved vendors. Third-party walk-in repairs not reimbursable.
- **8.5** INFO-ONLY: return devices within 5 business days of last working day on offboarding.
- **8.6** SELF-SERVICE: request peripherals via the Peripheral Catalog. Approval not stated.
- **9.1** SECURITY: report suspected incidents within 1 hour to security@helix.example or SOC hotline ext. 4357.
- **9.2** SECURITY: if compromise suspected, do not power off. Disconnect from network and wait for SOC.
- **9.4** PROHIBITED: employees speaking to press or customers about an incident. IC owns external comms.
- **9.5** INFO-ONLY: quarterly tabletop exercises for "incident-responder" roles.
- **9.6** SECURITY: lost or stolen device confirmed to hold Restricted data is auto-escalated to SEV-2.
- **10.2** NEEDS-APPROVAL(manager; plus data owner for Restricted-tier systems): access beyond default RBAC.
- **10.3** NEEDS-APPROVAL(reviewer; reviewers not named): certify or revoke within 14 calendar days. Uncertified access auto-revoked.
- **10.4** INFO-ONLY (automated): all access revoked within 1 hour of HR "separation" event in Workday.
- **10.5** NEEDS-APPROVAL(manager): contractor account renewal. Unrenewed accounts disable automatically.
- **10.6** PROHIBITED: shared accounts. Only named-team service accounts with rotating CyberArk credentials are excepted.

## 4. Cross-policy interactions and tensions

1. **Geography: POL-02 2.5 vs POL-05 5.2.** POL-02 uses a Network Security "Approved Country List" for access. POL-05 uses "approved geographies" (US-East, EU-Central) for Restricted data residency. Both name US-East and EU-Central, but they are different controls. POL-02 also says the list includes "Germany," while POL-05 uses region names. Whether the two lists are the same is not stated.
2. **Scope of "US-East" and "EU-Central".** POL-02 2.5 says the list "includes US-East and EU-Central / Germany." POL-05 5.2 lists them as geographies. The policies do not say whether these are countries or regions.
3. **Lost devices: POL-08 8.3 vs POL-09 9.1 and 9.6.** A lost device has a 24-hour ticket deadline (POL-08) and a 1-hour SOC reporting deadline for suspected incidents (POL-09). POL-09 9.6 auto-escalates to SEV-2 if Restricted data is confirmed. Whether the ticket, the SOC hotline, or both are required is not stated.
4. **BYOD and lost devices: POL-06 6.2 vs POL-08 8.3 and POL-09 9.6.** POL-06 limits IT remote-wipe to the corporate container. POL-08 and POL-09 cover "devices" without limiting them to corporate devices. Whether a lost BYOD device triggers the 8.3 ticket or the 9.6 escalation is not stated.
5. **Phishing reporting: POL-07 7.2 vs POL-09 9.1.** Suspicious emails go through the Phish Alert Button. Suspected security incidents go to SOC within 1 hour. The policies do not say which channel applies to a phishing email that may be a compromise.
6. **Privileged authentication: POL-01 1.2, 1.3, 1.6.** Standard accounts rotate annually and privileged accounts every 90 days. MFA is mandatory, and privileged users must also use a YubiKey. The YubiKey is additive; it does not replace the MFA factors in 1.3.
7. **Privileged access: POL-01 1.6 vs POL-02 2.6.** Privileged access to production needs a YubiKey (POL-01) and must go through CyberArk PAM (POL-02). Both apply.
8. **Shared and service accounts: POL-10 10.6 vs POL-01 1.2 and POL-02 2.6.** Shared accounts are prohibited. The exception is service accounts with rotating credentials in CyberArk. POL-01 sets rotation periods for named account types, and the policies do not say which period applies to these service accounts.
9. **Contractor accounts: POL-10 10.5 vs POL-01 1.2.** Contractor accounts end after 6 months unless renewed. POL-01 does not say whether contractor accounts are "standard" (annual rotation) or otherwise.
10. **Personal use vs personal VPN: POL-03 3.1 vs POL-02 2.1.** Incidental personal use is allowed, but personal VPNs are banned on corporate endpoints. The specific prohibition in POL-02 2.1 should control.
11. **Personal cloud storage: POL-03 3.5 vs POL-07 7.4 and POL-05.** POL-03 blocks personal cloud storage, and POL-07 7.4 points to Box or OneDrive for large files. These are consistent. POL-05 5.3 DLP applies to external sharing of Confidential data, which POL-07 7.4 links do not override.
12. **Retention: POL-03 3.3 vs POL-05 5.5.** Web logs are kept 12 months (POL-03). Business records are kept 7 years, PHI 10 years, and payment data purged at 13 months (POL-05). These cover different data, and the agent must not apply one to the other.
13. **Data owner approvals: POL-05 5.3 vs POL-10 10.2.** Both require data owner approval. POL-05 5.3 is for DLP exceptions (30 days). POL-10 10.2 is for Restricted-tier access beyond the RBAC template. The policies do not say whether the same person acts as data owner in both.
14. **Hiring timing: POL-08 8.2 vs POL-10 10.1.** Hardware must be requested 10 business days before start date. Access is provisioned when HR marks the employee "active." The policies do not define how these two steps are sequenced.
15. **Approved software: POL-04 4.1 vs 4.2.** Catalog software can be self-served. Anything else needs a 5-business-day review by InfoSec, Procurement, and Legal. Non-catalog open-source also needs 4.3 review.
16. **Restricted source code: POL-05 5.2 vs POL-04 4.3.** Revenue-critical source code is Restricted and must stay in approved geographies. Open-source libraries in internal tools need an SBOM and license review. The policies do not say how the two interact.
17. **Stipend vs hardware: POL-06 6.6 vs POL-08.** Stipend recipients give up eligibility for a corporate phone. POL-08 covers other hardware, so the effect on laptop or peripheral requests is not stated.
18. **Email auto-forwarding: POL-05 5.6, POL-07 7.6, and POL-03 3.5.** All three restrict forwarding or personal storage. POL-05 says auto-forwarding is technically blocked. POL-07 says end users cannot create such rules. These are consistent.
19. **Lost and stolen report timing: POL-08 8.3 (24 hours) vs POL-09 9.1 (1 hour).** The 1-hour rule applies to suspected security incidents. The 24-hour rule applies to lost or stolen devices. A lost device may fall under both.

## 5. Facts an agent must not fill from prior knowledge

- Approver for the Travel Exception (POL-02 2.5), for Make-Me-Admin (POL-04 4.6), for Peripheral Catalog requests (POL-08 8.6), and for password-portal unlock (POL-01 1.4). None is stated.
- Full list of Approved Countries beyond US-East, EU-Central / Germany, Japan (excluded), and Vietnam (excluded).
- Whether US-East and EU-Central are countries or regions.
- Contents of the Approved Software Catalog, Allowed Extensions List, Approved License List, and Approved Geographies list.
- Who the reviewers are in quarterly access certification (POL-10 10.3).
- Which systems are "Restricted-tier" (POL-10 10.2).
- Whether POL-09 9.6 applies to BYOD devices.
- Whether POL-07 7.4's 25 MB limit applies per attachment or per message.
- Full SOC hotline phone number. Only extension 4357 (labelled HELP) is given.
- Disciplinary or penalty consequences for any violation. None is stated.
- Repair reimbursement amounts, or any reimbursement process beyond "third-party walk-in repairs are not reimbursable."
- Whether the Make-Me-Admin 60-minute limit resets per day or per session. The source says "per session."
- How a phishing simulation "failure" is defined, beyond "fail two within 12 months."
- Which roles are tagged "mobile-eligible" or "incident-responder" in Workday. Tagging is by Workday, not listed in policy.
- Vendor product details (Okta Verify, Zscaler, CyberArk, Intune, Chrome/Edge management). Only the names and the stated uses appear.
- Whether privileged passwords have a different length or complexity rule from 1.1. Only the rotation period (90 days) is stated for privileged accounts.
- How long an account stays locked before any automatic unlock. Only self-service unlock after 15 minutes is stated.
- Whether MFA exceptions exist. None are stated.
- Whether the 12-month log retention in POL-03 3.3 is also the retention for Zscaler data generally.
- Any policy on personal devices beyond email, calendar, and Teams (POL-06 6.1).
