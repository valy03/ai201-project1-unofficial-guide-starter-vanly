# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

For my domain, I chose a system that covers student experiences with campus dining and nerby food options at UC Santa Cruz. It spans official dining hall information and student reviews of specific dining halls like Cowell, Crown, RCC, C9/C10. It also covers meal plan currency (Slug Points, Banana Bucks, Flexi Dollars), and off-campus restaurant recommendations popular with students. This knowledge is hard to find because it's scattered across Reddit, Yelp, official pages, and other food review sites. Since choosing the best dining hall is subjective, there is no single source that answers "which dining hall is the best?" or "where do UCSC students actually eat?"

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | UCSC Dining (official) | Dining hall and café locations and hours of operation | https://dining.ucsc.edu/locations-hours/ |
| 2 | UCSC Dining (official) | Residence hall meal plan pricing and currency (Slug Points / Banana Bucks / Flexi Dollars) | https://dining.ucsc.edu/plans-pricing/residence-hall/ |
| 3 | Wanderlog | Curated list of popular off-campus restaurants near UCSC | https://wanderlog.com/list/geoCategory/75129 |
| 4 | Yelp | Student/customer reviews of Cowell & Stevenson dining hall | https://www.yelp.com/biz/cowell-stevenson-dining-hall-santa-cruz?osq=stevenson+dining |
| 5 | Yelp | Student/customer reviews of Porter & Kresge dining hall | https://www.yelp.com/biz/porter-kresge-dining-hall-santa-cruz?osq=Cafeteria |
| 6 | Yelp | Student/customer reviews of College Nine & Ten dining hall | https://www.yelp.com/biz/college-nine-and-ten-dining-hall-santa-cruz?osq=Cafeteria |
| 7 | Yelp | Student/customer reviews of Crown & Merrill dining hall | http://yelp.com/biz/crown-merrill-dining-santa-cruz?osq=Cafeteria |
| 8 | Reddit (r/UCSC) | Student discussion ranking the best dining hall / café | https://www.reddit.com/r/UCSC/comments/1n2g02r/best_dining_hallcafe/ |
| 9 | Reddit (r/UCSC) | Discussion of 2026–2027 dining hall price increases | https://www.reddit.com/r/UCSC/comments/1rtvb1z/dining_hall_prices_for_20262027_has_risen_again/ |
| 10 | Reddit (r/UCSC) | Student opinions on dining hall food quality | https://www.reddit.com/r/UCSC/comments/16u7gfq/dining_hall_food/ |
| 11 | Reddit (r/UCSC) | Discussion of how consistent the dining halls are | https://www.reddit.com/r/UCSC/comments/1r488hw/how_consistent_are_the_dining_halls/ |
| 12 | Reddit (r/UCSC) | Student off-campus restaurant recommendations | https://www.reddit.com/r/UCSC/comments/11gos4s/people_of_ucsc_i_need_your_restaurant/ |
| 13 | Reddit (r/UCSC) | Discussion of dining hall prices from a thread 3 years ago | https://www.reddit.com/r/UCSC/comments/166haj0/dining_hall_is_raising_food_prices_by_50/ |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:** 256 tokens


**Overlap:** 35 tokens

**Reasoning:** I'm using recursive chunking (split on a priority of natural separators — paragraphs → lines → sentences → words — before falling back to a hard cut). This single strategy fits my mixed corpus because recursive splitting only divides content that exceeds the chunk size. Long, structured sources (official UCSC dining pages, Wanderlog restaurant lists) get broken on natural boundaries so sections, hours blocks, and price/currency info stay intact rather than being cut mid-fact. Short sources (Yelp reviews, Reddit comments) are usually under 300 tokens, so they pass through as a single whole chunk — keeping each opinion self-contained instead of merging several reviews into one blurry chunk. The 35-token overlap (15% of chunk size) repeats text across boundaries on the longer documents so a fact that straddles a split (e.g. a meal-plan currency rule spanning two chunks) still lands complete in at least one chunk; it has little effect on the short reviews since they aren't split.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** Use all-MiniLM-L6-v2 via sentence-transformers

**Top-k:** 5

**Production tradeoff reflection:**
Since my sources mostly contain reviews and reddit threads, I think that MiniLM would be best embedding model sine it is quick and simple because it can only handle 256 tokens on average. This also means that we won't be able to efficiently retrieve messier or longer text that well. 

**Implementation update (Milestone 4):** Stored vectors in ChromaDB with cosine distance and L2-normalized embeddings. Added a *contextual chunk header* — each chunk's source label is prepended to its text before embedding (the stored/displayed text stays clean). This restores document-level context that is lost when a document is split into chunks (e.g. a bare "Gabriella Cafe: Italian..." list item no longer signals "off-campus restaurant"), and fixed the off-campus-restaurants query, which had been returning on-campus dining-hall reviews. Also learned that noisy chunks both pollute content and inflate distance: trimming nav/boilerplate out of the dining-hours document dropped its hours query distance from 0.30 to 0.18.
---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What are the operating hours of the College Nine / John R. Lewis dining hall? | Open 7AM-11PM Tuesday-Saturday (breakfast 7-11, lunch 11:30-2, dinner 5-8, Late Night 8-11) and 7AM-8PM Sunday-Monday (no Late Night). Bonus: it offers Late Night service, which most halls don't. (Source: dining.ucsc.edu/locations-hours/nine-jrl) |
| 2 | Can I use Banana Bucks at any dining hall, and do they roll over between quarters? | [Should mention that Banana Bucks carry over quarter to quarter but expire at the end of the academic year: where Banana Bucks are accepted + rollover/expiration rule from dining.ucsc.edu meal-plan page] |
| 3 | Which dining hall do UCSC students consider the best, and why? | [Should mention that Cowell/Steven, Crown/Merrill are consistent, C9/C10 is considered the most liked, and Porter dining hall is viewed as the worst: most-praised hall(s) across Reddit #8/#10/#11 + reasons cited (food quality, variety) — checklist] |
| 4 | What off-campus restaurants near UCSC do students recommend? | [Zoccolis, Jack’s, Sesame, Zachary’s, Abbott Square, Betty’s, The Bagelry, Lillian’s, Mission St. BBQ, Pizza my Heart, Dolphin. Can also mention any resturants from reddit that corrporates with wanderlog's top resturants in santa cruz: named restaurants appearing across Wanderlog #3 + Reddit recommendation thread #12] |
| 5 | How much have dining hall prices risen for the 2026–2027 year? | [Should mention that a few years back, the prices of dining entry was about 9 dollars and recently it is 13-15$ depending on breakfast or dinner: price-increase figures/percentages from Reddit #9, cross-checked against official pricing page #2] |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. I think the biggest issue is missing source attribution. There aren't enough sources to cover very specific questions.

2. Since our chunk split is 256 tokens, there may be inconsistent in the split and may retrieve irrelevant and inconsistent information

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

Stages 1–3 are the **offline indexing** pipeline (run once to build the vector store).
The **query → retrieval → generation** path is the **online** pipeline that runs per question.

```
┌────────────────────┐
│  User question     │
└─────────┬──────────┘
          │ embed query (MiniLM)
          ▼
[1] Document Ingestion ──> [2] Chunking ──> [3] Embedding + Vector Store
  UCSC / Yelp /            recursive          all-MiniLM-L6-v2
  Reddit / Wanderlog       256 tok / 35       → ChromaDB
  (requests + BS4,         overlap                  │
   saved to documents/)                             │
                                                    ▼
                                          [4] Retrieval
                                          cosine sim, top-k = 5
                                                    │
                                                    ▼
                                          [5] Generation
                                          Groq API (Llama 3.x)
                                          question + 5 chunks
                                                    │
                                                    ▼
                                          Answer with sources
```

---


## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
I'll use **Claude** for this milestone. As input I'll give it my **Documents** table (the 12 sources and their types) and my **Chunking Strategy** section. I'll ask it to (a) write an ingestion script that loads each source from `documents/` — using `requests` + `BeautifulSoup` to strip HTML to clean text, and saving Reddit/Yelp content where scraping is blocked — and (b) implement a `chunk_text()` function using a recursive splitter with my exact parameters (256 tokens, 35-token overlap), attaching source metadata (source name + URL) to each chunk so attribution survives into retrieval. I'll verify by running it on 2–3 sources and checking that chunks land on natural boundaries (not mid-sentence), stay at/under 256 tokens, and each carries its source metadata.

**Milestone 4 — Embedding and retrieval:**
I'll use **Claude** with my **Retrieval Approach** and **Architecture** sections as input. I'll ask it to write code that embeds every chunk with `all-MiniLM-L6-v2` via `sentence-transformers`, stores the vectors plus metadata in **ChromaDB**, and implements a `retrieve(query, k=5)` function that embeds the query and returns the top-5 chunks by cosine similarity. I'll verify by running my 5 evaluation questions through `retrieve()` and confirming the returned chunks actually come from the sources I expect (e.g. Q1 pulls from the official hours page, Q3 pulls from the Reddit threads) — this directly tests the off-topic-retrieval risk in my Anticipated Challenges.

**Milestone 5 — Generation and interface:**
I'll use **Claude** (as my coding assistant) with my **Evaluation Plan** as input. I'll ask it to write the generation step that sends the user's question plus the 5 retrieved chunks to the **Groq API** (Llama 3.x — the free, no-credit-card key the starter is set up for via `GROQ_API_KEY`) with a prompt that requires answering only from the provided chunks and citing the source of each claim (addressing my missing-attribution risk), plus a simple interface (CLI or Streamlit) to type a question and see the answer with sources. I'll verify by running all 5 evaluation questions end-to-end and comparing each response against my recorded expected answers, checking both correctness and that citations point to the right source.
