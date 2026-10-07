# Interview packets

Six services, two packets each (bariatric also has a third, C, a covered gastric bypass). A is straightforward, B is complex. Build the service first (describe it, add the billing code, build the policy, review it, submit), then upload the packets.

| Service | Billing code | Policy | Packet A | Packet B |
|---|---|---|---|---|
| Bariatric surgery | 43775 | NCD 100.1, plus LCD L35022 (Novitas) | A_straightforward_carter_sleeve.pdf | B_complex_hayes_sleeve.pdf; C_approve_walker_gastric_bypass.pdf |
| Total knee replacement | 27447 | LCD L36575 (Noridian) | A_straightforward_evans_right_knee.pdf | B_complex_jennings_laterality_mismatch.pdf |
| Spinal cord stimulator | 63685 (also 63650) | LCD L36204 (Noridian) | A_straightforward_mitchell_permanent_implant.pdf | B_complex_lopez_weak_trial.pdf |
| Hypoglossal nerve stimulation | 64582 | LCD L38528 (WPS) | A_straightforward_anderson.pdf | B_complex_nguyen.pdf |
| Vertebral augmentation | 22514 (also 22513) | LCD L38213 (WPS) | A_straightforward_collins_acute_fracture.pdf | B_complex_stevens_old_fracture_cancer_history.pdf |
| TMS for depression | 90867 (also 90868, 90869) | LCD L34641 (WPS) | A_straightforward_foster.pdf | B_complex_brennan.pdf |

All patient data is made up. Regenerate with `python scripts/make_interview_packets.py`.
