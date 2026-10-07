# Decisions and trade-offs slide: speaker script

In my own voice. Short, plain sentences. One business decision and two trade-offs, with a person at both ends. About 2 minutes.

## Script
These are the three biggest decisions I made.

The first is a business decision. I don't train the AI on Humana's past decisions. It's tempting, because there are years of history. But a model trained on past decisions learns what Humana usually did, not what the policy says. It copies old mistakes and old bias, and it can't show why. CMS said the same thing in 2024. A plan must decide on the patient's own record, not on a prediction from large data sets. So the AI reads this patient's packet against this policy, and quotes the evidence. History still helps. It becomes test data for the evals, and it tells us which services to onboard next.

The second is who approves what the AI writes. The AI drafts the key facts for every policy, and the policy owner approves each one. That is a lot of clicking. But if the AI drafts too many, the nurse gets flooded with pends. If it drafts too few, it misses a requirement. Only a person can tell. It's a one-time job for each policy, and the owner's decisions become a test set. When precision and recall stay high on new policies, the AI can approve on its own.

The third is recall over precision. A miss is a wrong approval, and that is the failure I can't afford. A false alarm costs a nurse a few minutes. I tune it from the nurses' decisions.

It's the same idea everywhere. Start cautious. Watch what people do. Relax the AI only as fast as the evidence allows.
