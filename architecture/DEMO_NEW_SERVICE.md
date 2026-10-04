# Demo: a packet with no policy, then onboarding a new service

The story: a request arrives for something we do not cover. The tool says so and does not guess. The policy owner brings in the policy, the codes and a new service. The same packet is checked again and gets a real recommendation.

Packets (made up, in `packets/demo_new_service/`, made by `scripts/make_cpap_packets.py`):
| File | Documented | Expected result once the service exists |
|---|---|---|
| `cpap_complete.pdf` | Everything the policy asks for | Approve |
| `cpap_missing_test.pdf` | No sleep study report | Pend: ask the provider for it |
| `cpap_low_ahi.pdf` | Sleep study shows mild apnea (AHI 9) | Escalate to a medical director |

## Steps
1. **Intake (Carla Mendez).** Upload `cpap_complete.pdf`, then the other two. Each case reads "No policy yet". The procedure code is E0601 and no service uses it. Nothing was guessed. The nurse can still approve, ask the provider or escalate.
2. **Policy owner (Dana Whitfield), Requests without a policy.** The first page. E0601 shows with the number of waiting cases and the oldest wait. This is the demand list: the codes that come in most are the next services to onboard. Click "Add to the rollout list".
3. **Services.** The form is filled in with the code. Name the service (CPAP therapy for obstructive sleep apnea), short name (CPAP), keep the code with its source and add it to the rollout list. It is **Planned**: no packet is sent to it.
4. **Policy library.** Search "positive airway", pick NCD 240.4, choose "A new service" and Build a draft. (An earlier draft is already in Policies to review if you want to skip the wait.)
5. **Policies to review, open the draft.** Official text on the left, rules on the right.
   - Approve the rules for: adult patient, clinical evaluation, sleep test type, ordered by the treating physician, physician supervision, AHI at least 15, beneficiary education.
   - Reject the rules for the AHI 5 to 14 pathway, the minimum test duration and continued benefit after 12 weeks. Other pathways stay with a person.
6. **Which cases use this policy?** Pick the planned service CPAP. Tick "Add the new details to CPAP", and check the questions the reader will use. Publish. The policy and its details are now in the service, which is still Planned.
7. **Services.** Click **Start pilot**. It refuses if the service has no policy, no code or no details, so the gate is real. The service is now a **Pilot**. A pilot can become **Live** only with a written note on what was tested.
8. **Back at the cases.** Open a "No policy yet" case and click "Check again with the current policies". The packet is read again and the recommendation appears, marked "Pilot service". The other two packets pend and escalate.
9. **Version history.** Every step is in the audit trail. "Go back to this" returns the library to before the CPAP service, so the demo can be run again.

(Shortcut: in step 6 you can choose "Create a new service for this policy" instead. That creates the service and starts it as a pilot in one go.)

## What to say when asked
- **Where did E0601 come from?** CMS's own policy article for CPAP devices lists it. The screen stores the article next to the code.
- **Why a pilot?** The reader is an AI and these details are new. In production a service goes live after its test packets pass. Nurses check every recommendation until then.
- **Why were some rules rejected?** The policy has several ways to qualify. The system models the main one. The others stay with a person.

## Known limits
- The engine has no "either of these" logic, so a policy with several ways to qualify is modeled one way at a time.
- Tested end to end on these three made-up packets only. No accuracy claim for the CPAP service.
- The AI drafted the rules. The owner's review is what makes them trustworthy.
