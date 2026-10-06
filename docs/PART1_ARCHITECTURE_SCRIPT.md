# Part 1 architecture: speaker script

In my own voice. Plain, active sentences. For the one-page Part 1 architecture slide.

## What Part 1 is
Let's look a little deeper at the architecture. Once we understand what happens inside, the product flow is easy to follow.

Part 1 is an onboarding flow. It is how we onboard a new service. Say Humana decides to cover allergen immunotherapy. Part 1 builds the policy library for that service. The output is a list of key facts, with a rule attached to each one.

Key fact is a term I coined for this prototype. It is a required checklist item. It is something the policy says must be in the incoming packet for the request to be covered.

Length of stay is a good example. The key fact is length of stay. The rule is that the stay should cross at least two midnights. In Part 2, the AI checks two things. Is this key fact in the incoming packet? And does it pass the rule?

## Stage 1: the refresh
We start with a scheduled job. It pulls three things from the CMS Coverage API: the billing articles, the billing codes on each article, and the policies.

It saves all of it in a CMS database with three tables. One table for articles. One for codes, with the article as a foreign key. And a separate table for policies. Each table keeps the code, the description and the text.

I built the job to run weekly. Articles and policies don't change that often, so monthly would work too.

## Stage 2: creating a service
Now the policy owner logs in to the portal. They create a new service and name it allergen immunotherapy.

The app server goes to the database. It finds the articles and billing codes related to immunotherapy, and it suggests billing codes. It ranks them by how many articles each code is found in. A code in nine out of nine articles comes first. The owner ticks the ones to use, and each code keeps its CMS article as its source.

Next, the app suggests policies tied to this service. It looks in our own library first, then the local coverage and national coverage lists. The owner selects the policies to apply.

## Stage 3: the pipeline
Now comes the interesting part, the AI part.

If a policy has not been built before, it goes through a pipeline. We build each policy only once. After that, any other service can reuse it.

Step one is the ETL. The policy goes through the Unstructured API. It has a partitioner. The partitioner reads the document and works out how to parse each page. It extracts the elements and keeps the structure. The output is a structured JSON list. Each element has its title, its text and its page number.

Step two is the AI. That JSON goes to Claude Sonnet. It has a 10-rule prompt and a fixed output form. The prompt says: turn one coverage policy into a checklist of testable criteria for a prior authorization tool. That tool is Part 2. A criterion is one condition the policy says must be true. That is our key fact.

I added guardrails because language models hallucinate, and they tend to flag everything on the page as a key fact. So the rules say: never add a rule from your own knowledge. One condition, one key fact. Split anything compound. Copy the exact sentence, word for word. Don't paraphrase. Don't round a number. If a rule applies to a subgroup, name the subgroup. If you can't model something, say so and leave it for a person.

The output form has fixed fields. The key fact to check. The rule and its threshold. The exact quote and the section it came from. And the question to ask the provider if the fact is missing.

Step three is the validator. It is code, and it does not trust the AI. It finds every quote in the policy text. It tries an exact match first. If the exact text isn't there, it uses fuzzy matching. A fuzzy match must carry the same numbers. Then it checks that every number in a rule is in its quote, and that every key fact exists.

Step four is the policy owner. For each policy, they see the list of key facts. Each one comes with its rule, the exact quote, and the question. They approve, edit or reject each rule. Only the approved ones are saved.

That question is the useful part. In Part 2, if a required key fact is missing from the packet, the AI tells the nurse: this was required for the policy to be covered, and it is missing. The nurse sends the provider that exact question.

That is Part 1. The output is the key fact list, with rules attached. Part 2 only uses what Part 1 approved.

## Check before you say it
- Unstructured strategies (fast, hi-res, vision model per page): not confirmed in our code. The saved run says "balanced". Verify in Unstructured's docs first.
- The refresh job is built but not scheduled yet. It runs by hand in the prototype.
