# Key tradeoff slide: speaker script

In my own voice. Plain, complete sentences. Two tradeoffs, with a person at both ends.

## Script
The biggest tradeoff I made is who approves what the AI writes.

In the prototype, the AI drafts the key facts for every policy, and the policy owner approves each one. That takes time. With around 2,000 policies, at five to ten key facts each, that is a lot of clicking. The obvious fix is to let the AI approve its own.

But that goes wrong in two ways. If the AI creates too many key facts, it treats everything on the page as a requirement, and floods the nurse with flags and pends. If it creates too few, the system is too lenient and misses a requirement. Both look fine on the screen. Only a person can tell.

So I kept the owner in the loop. It is a one-time job for each policy, and it only repeats when the policy changes. The owner isn't writing from scratch, they are checking and approving. And every decision shows us where the AI is wrong.

Here is how I bring the cost down. I start with about 100 policies, and the owner's decisions become a test set. I tighten the prompts, then run the next 100 and compare the AI's list to the owner's. I watch two numbers. Precision: of the key facts the AI created, how many were right. Recall: of the requirements that really exist, how many it found. When both are high on policies it hasn't seen, we let it approve on its own.

The second tradeoff is on the packet side. I tuned the AI for recall over precision. Recall means catching every case that needs a person. Precision means being right when I flag one. I accept some false alarms, because a missed problem is a wrong approval, and that is the failure I can't afford.

I tune this the same way, from the nurse's responses. If a nurse approves a lot of cases the AI flagged, those are false alarms, and I push precision up. If a nurse finds a problem in a case the AI cleared, that is a miss, and I fix that first.

It is the same principle at both ends. We start cautious, we watch what people do, and we relax the AI only as fast as the evidence allows.
