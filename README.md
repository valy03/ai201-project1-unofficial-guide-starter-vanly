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

**Model used:** I used all-MiniLM-L6-v2 via sentence-transformers, with embeddings stored in ChromaDB using cosine distance. It runs locally with no API key or rate limits, which fits a small project, and its 384-dim vectors are fast to embed and query. Each chunk's source label is prepended before embedding (a contextual chunk header) to restore document-level context lost during splitting; retrieval uses top-k = 5. Across the 5 evaluation queries, top-result cosine distances were 0.18–0.50 (4 of 5 clearly below 0.5).

**Production tradeoff reflection:** MiniLM's main limitation is its ~256-token context window — longer or messier chunks get truncated before embedding, which is why chunking was capped at 256 tokens. If cost weren't a constraint and this were deployed for real users, I'd weigh a longer-context, higher-accuracy model (e.g. a hosted `text-embedding-3-large` or a larger BGE/GTE model): longer context would remove the truncation constraint and let chunks carry more semantic signal, and a stronger model would better distinguish near-duplicate opinions ("good but crowded" vs. "crowded so it's bad") and separate semantically similar but distinct topics — exactly the failure I hit where "off-campus restaurants" retrieved on-campus dining halls. The tradeoffs would be added per-call latency and cost and a dependency on an external API instead of a free local model. Multilingual support isn't relevant here since the corpus is English-only.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:** The Groq (Llama 3.3) model is given a system prompt that constrains it to the retrieved passages:

> Answer ONLY using the numbered context passages provided. Do not use outside knowledge. If the passages do not contain the answer, say you don't have that information in your sources. Do not guess prices, hours, or facts. Cite the passages you rely on with their bracket numbers, e.g. [1], [3]. When sources disagree (e.g. opinions about a dining hall), reflect that range rather than picking one.

The user message then supplies the context as **numbered, source-labeled passages** (`[1] (Source: …) <chunk text>`) followed by the question, and generation runs at low temperature (0.2) to discourage embellishment. This structure is what makes citation possible and lets the model refuse when the answer isn't present — e.g. on Q5 it correctly replied that the sources don't specify the exact recent price increase instead of inventing a number.

**How source attribution is surfaced in the response:** Two ways. (1) The model cites passages inline by bracket number (`[1]`, `[2]`) tied to the numbered context. (2) The Gradio UI prints a **Sources** panel under every answer listing each retrieved passage's source label, cosine distance, and original URL, so the user can trace any claim back to the document it came from and judge the match quality.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What are the operating hours of the College Nine / John R. Lewis dining hall? | Open 7AM-11PM Tuesday-Saturday (breakfast 7-11, lunch 11:30-2, dinner 5-8, Late Night 8-11) and 7AM-8PM Sunday-Monday (no Late Night). Bonus: it offers Late Night service, which most halls don't. | "7AM to 11PM Tuesday–Saturday, and 7AM to 8PM Sunday–Monday [1]" — top dist 0.18 | Relevant | Accurate |
| 2 | Can I use Banana Bucks at any dining hall, and do they roll over between quarters? | Should mention that Banana Bucks carry over quarter to quarter but expire at the end of the academic year; where Banana Bucks are accepted + rollover/expiration rule from the dining.ucsc.edu meal-plan page | Stated Banana Bucks usable only after Slug Points are used up, carry over quarter to quarter, expire in June [1] — top dist 0.50 | Partially relevant (borderline distance) | Accurate |
| 3 | Which dining hall do UCSC students consider the best, and why? | Should mention that Cowell/Stevenson, Crown/Merrill are consistent, C9/C10 is considered the most liked, and Porter dining hall is viewed as the worst; most-praised hall(s) across Reddit #8/#10/#11 + reasons cited (food quality, variety) | Reflected the split of opinions: C9/10 praised (late night, brunch), Crown/Merrill homey, Cowell/Stevenson better food, lines hurt quality; concluded opinions are divided [1][2][4][5] | Relevant | Accurate |
| 4 | What off-campus restaurants near UCSC do students recommend? | Zoccolis, Jack's, Sesame, Zachary's, Abbott Square, Betty's, The Bagelry, Lillian's, Mission St. BBQ, Pizza my Heart, Dolphin. Can also mention any restaurants from Reddit that corroborate Wanderlog's top restaurants in Santa Cruz; named restaurants across Wanderlog #3 + Reddit recommendation thread #12 | Listed Reddit recs (Poki Bowl, Island Grille, Point Market, Tramonti, Real Thai, Sala Thai, Mission St BBQ) from [1] — top dist 0.29 | Partially relevant (3 of 5 chunks were on-campus Yelp; Wanderlog list not retrieved) | Partially accurate (valid but incomplete coverage) |
| 5 | How much have dining hall prices risen for the 2026–2027 year? | Should mention that a few years back the price of dining entry was about 9 dollars and recently it is 13-15$ depending on breakfast or dinner; price-increase figures/percentages from Reddit #9, cross-checked against official pricing page #2 | Said sources don't specify the exact recent increase; noted a 50% increase three years ago [2] — top dist 0.38 | Partially relevant | Partially accurate (honest refusal; missed the specific figures) |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

Summary: 3 of 5 fully accurate, 2 partially accurate. No hallucinations — where evidence was thin (Q5) the model declined rather than inventing numbers. 4 of 5 top-result distances were below 0.5.

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** Q5 — "How much have dining hall prices risen recently?"

**What the system returned:** The model said the sources don't specify the exact recent increase, and only noted a "50% increase three years ago" from one chunk. It did not produce concrete figures, even though the corpus does contain price numbers (e.g. "$8 a meal in 2012 with Flexi Dollars," "worth $8 a meal," a "50%" jump).

**Root cause (tied to a specific pipeline stage):** This is a retrieval/chunking coverage problem, not a generation problem. The price figures are *distributed across many separate Reddit comments* — each user mentions one fragment ($8 in 2012, a 50% jump, "half the price when I was there"). No single chunk contains a coherent before/after trajectory. The query "prices risen recently" embeds closest to chunks expressing *sentiment* about rising prices (complaints about cost vs. quality) rather than the sparse chunks that state actual dollar amounts, so the numeric evidence mostly fell outside the top-5. Because the system is correctly grounded, the model declined rather than stitching together or inventing numbers. (Worth noting: the planning.md "expected answer" of ~$9→$13–15 doesn't fully match what the documents actually say, which is ~$8 in 2012 — so part of the gap is that the corpus never states the specific recent figures cleanly.)

**What you would change to fix it:** (1) Collect a source that states the current per-meal price explicitly (the official pricing page lists plan totals but not per-entry cost), since the answer simply isn't well-represented in the corpus; (2) optionally chunk the price threads so numeric statements aren't separated from their context. The cleanest fix is corpus coverage — retrieval and grounding both behaved correctly given what was available.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** Writing the Chunking Strategy and Retrieval Approach sections before coding meant the implementation prompts were concrete: chunk size 256 / overlap 35, recursive splitting, all-MiniLM-L6-v2, ChromaDB, top-k 5. Because those decisions were already made and justified in planning.md, the generated code matched my intent on the first pass and I could verify it against a written spec instead of guessing whether it was "right." The 256-token cap in particular came directly from reconciling chunk size against MiniLM's context window during planning, which prevented a silent-truncation bug later.

**One way your implementation diverged from the spec, and why:** I added a "contextual chunk header" that wasn't in the original plan: prepending each chunk's source label before embedding. I added it because retrieval testing showed the off-campus-restaurants query returning on-campus dining-hall reviews — once a document is chunked, an individual chunk loses the document-level signal of what it's about, and re-injecting the source label fixed it. The changes are recorded in planning.md's Retrieval Approach update.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1 — Chunking implementation**

- *What I gave the AI:* Use my Documents and Chunking Strategy sections from planning.md to implement chunking of the documents. Documents are a mixed of official pages, Yelp reviews, Reddit threads.
- *What it produced:* A recursive, token-based `chunk_text()` measuring length with the MiniLM tokenizer, plus an ingestion loader with HTML/entity stripping and a source-attribution header.
- *What I changed or overrode:* The first merge logic summed per-segment token counts, which let a chunk reach 258 tokens (re-joining text re-tokenizes differently); I directed a fix to measure length on the joined text and to drop the overlap tail when it would push a chunk over 256. I also iteratively tightened the cleaning rules per source type after inspecting real chunks (Yelp reviewer cards, Reddit username/timestamp headers, promoted ads).

**Instance 2 — Retrieval debugging**

- *What I gave the AI:* The retrieval test output for my 5 evaluation queries, including a chunk that matched Q1 at distance 0.30 but contained leftover navigation text.
- *What it produced:* A diagnosis that the chunk was polluted by un-stripped nav lists in the dining-hours document, plus the contextual-chunk-header idea for the off-campus query that was matching on-campus content.
- *What I changed or overrode:* I had it trim document 01 down to substantive content (dropping the time-sensitive "open now" snapshot and duplicated nav lists), which lowered the Q1 distance from 0.30 to 0.18. I chose to leave Q2's borderline 0.50 distance as-is rather than over-engineer, since the correct chunk was already retrieved at rank 1.