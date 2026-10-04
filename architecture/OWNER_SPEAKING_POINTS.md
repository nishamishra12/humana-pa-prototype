# Policy owner: speaking points

Use these when you walk through the policy owner screens. Plain words, short sentences.

## What the policy owner does
1. **Brings in a policy.** Picks a CMS policy from the list, or uploads a plan PDF. The system drafts the rules. Each rule carries the exact sentence it came from.
2. **Decides every rule.** Reads each rule beside the official text. Approves it, changes it, or rejects it. Nothing is live yet.
3. **Publishes.** Publishing makes a new version. New cases are checked against it. Cases that already have a recommendation keep it. The owner can go back to the last version at any time.

## Why it is built this way
- The AI drafts. It never publishes. A person signs every rule.
- Code checks every quote and number before the owner sees it. A rule that fails cannot be approved.
- A rule that needs something the packet reader cannot find yet can still be approved. It waits, and it changes nothing until the reader learns it.
- The list of CMS policies is built by the back end on a schedule. The owner picks from it. The owner does not hunt for numbers.
- Every version is kept. Every action is in an audit trail that cannot be edited.

## If someone asks
- **Who is the policy owner?** The clinical policy lead who is accountable for what the rules say.
- **What happens when CMS changes a policy?** "Check for updates" compares the official text with the last saved copy. If it changed, the owner builds a new draft and reviews it. A scheduled version of this check is not built yet.
- **Has a real policy owner used it?** No. I tested it myself on made-up data.
