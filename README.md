# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

This system covers student experiences with campus dining and nearby food options at UC Santa Cruz. It spans official dining hall information (locations, hours, meal-plan pricing and currency — Slug Points, Banana Bucks, Flexi Dollars), student reviews of specific dining halls (Cowell/Stevenson, Crown/Merrill, Porter/Kresge, College Nine/Ten, Rachel Carson/Oakes), and off-campus restaurant recommendations popular with students. This knowledge is hard to find through official channels because it is scattered across Reddit, Yelp, official pages, and travel/food sites, and because the most useful questions ("which dining hall is actually best?", "where do students really eat?") are subjective — no single official source answers them.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | UCSC Dining — locations & hours | Official site | https://dining.ucsc.edu/locations-hours/ (+ per-hall pages nine-jrl, cowell-stevenson, crown-merrill) → documents/01_dining_locations_hours.txt |
| 2 | UCSC Dining — residence hall meal plans | Official site | https://dining.ucsc.edu/plans-pricing/residence-hall/ → documents/02_meal_plans_pricing.txt |
| 3 | Wanderlog — restaurants near UCSC | Travel/food list | https://wanderlog.com/list/geoCategory/75129 → documents/03_wanderlog_restaurants.txt |
| 4 | Yelp — Cowell/Stevenson dining hall | Review site | https://www.yelp.com/biz/cowell-stevenson-dining-hall-santa-cruz → documents/04_yelp_cowell_stevenson.txt |
| 5 | Yelp — Porter/Kresge dining hall | Review site | https://www.yelp.com/biz/porter-kresge-dining-hall-santa-cruz → documents/05_yelp_porter_kresge.txt |
| 6 | Yelp — College Nine & Ten dining hall | Review site | https://www.yelp.com/biz/college-nine-and-ten-dining-hall-santa-cruz → documents/06_yelp_college_nine_ten.txt |
| 7 | Yelp — Crown/Merrill dining hall | Review site | http://yelp.com/biz/crown-merrill-dining-santa-cruz → documents/07_yelp_crown_merrill.txt |
| 8 | Reddit r/UCSC — best dining hall/cafe | Forum thread | https://www.reddit.com/r/UCSC/comments/1n2g02r/best_dining_hallcafe/ → documents/08_reddit_best_dining_hall.txt |
| 9 | Reddit r/UCSC — dining prices 2026/2027 | Forum thread | https://www.reddit.com/r/UCSC/comments/1rtvb1z/dining_hall_prices_for_20262027_has_risen_again/ → documents/09_reddit_prices_2026_2027.txt |
| 10 | Reddit r/UCSC — dining hall food quality | Forum thread | https://www.reddit.com/r/UCSC/comments/16u7gfq/dining_hall_food/ → documents/10_reddit_dining_hall_food.txt |
| 11 | Reddit r/UCSC — how consistent are dining halls | Forum thread | https://www.reddit.com/r/UCSC/comments/1r488hw/how_consistent_are_the_dining_halls/ → documents/11_reddit_consistency.txt |
| 12 | Reddit r/UCSC — off-campus restaurant recs | Forum thread | https://www.reddit.com/r/UCSC/comments/11gos4s/people_of_ucsc_i_need_your_restaurant/ → documents/12_reddit_restaurant_recs.txt |
| 13 | Reddit r/UCSC — prices raised 50% (3 yrs ago) | Forum thread | https://www.reddit.com/r/UCSC/comments/166haj0/dining_hall_is_raising_food_prices_by_50/ → documents/13_reddit_prices_3yr_ago.txt |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 256 tokens (measured with the all-MiniLM-L6-v2 tokenizer, the same model used for embedding)

**Overlap:** 35 tokens (~15% of chunk size)

**Why these choices fit your documents:** I used recursive chunking — splitting on natural separators (paragraph → line → sentence → clause → word) before any hard cut, so facts are not severed mid-sentence. Length is measured in *tokens* and capped at 256 because that is the input limit of all-MiniLM-L6-v2; this guarantees no chunk is silently truncated by the encoder. The recursive approach suits a mixed corpus: long, structured sources (official hours/pricing pages, Wanderlog list) get split on natural boundaries so a price table or hours block stays intact, while short Yelp reviews and Reddit comments usually fall under 256 tokens and pass through whole, keeping each opinion self-contained instead of merging several into one blurry chunk. The 35-token overlap carries context across boundaries on the longer documents (e.g. a meal-plan currency rule spanning two chunks) without meaningfully affecting the short reviews. Preprocessing before chunking: stripped HTML tags and entities (`&amp;`, `&nbsp;`), normalized odd Unicode punctuation, and removed source-specific boilerplate — UCSC site nav (`Check out…`, `›`), Yelp review-card chrome (reviewer names, Elite badges, user IDs, dates, locations, photo counts), and Reddit comment headers (usernames + timestamps), promoted ads, and `N more replies`. Each document also carries a `SOURCE:`/`URL:` attribution header that is preserved as chunk metadata.

**Final chunk count:** 78 chunks across 13 documents.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**

**Production tradeoff reflection:**

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
