---
name: road-trip-seed-list
description: Builds a route-specific restaurant/food-stop seed list (JSON) for an India road trip, given a source city and a destination city. Use this any time the user asks to research food stops, restaurant recommendations, or a "seed list"/"seed stop" dataset for a specific road-trip route in India — even if they just name two cities and ask what to eat on the way, or ask to "do the Tripoto workflow" for a route. Searches Tripoto and other independent road-trip editorials, extracts facts by hand (never bulk-scrapes), writes original descriptions, and scores each stop for distinctiveness. Always trigger this over a generic web search when the ask is specifically about food/restaurant stops along a named India route.
---

# Road Trip Seed List

Produces a `seed_stops` JSON file for a given **source → destination** road-trip route in India, by manually reading published road-trip editorials (Tripoto and others), extracting facts, and scoring each stop for how "worth the detour" it is.

This is a **manual read-and-extract workflow**, not a scraper. It runs a handful of targeted web searches per route and reads individual published pages the way a person would — it never crawls a site systematically or bulk-downloads its content. See "Guardrails" below; this constraint is not optional.

## Inputs

- `source`: a city/town in India (e.g. "Bangalore")
- `destination`: a city/town in India (e.g. "Gokarna")

If the user gives only a destination or only vague trip context, ask for the missing endpoint before proceeding — the route is what everything else keys off.

## Workflow

### 1. Establish the route(s)

Search to confirm the standard driving route(s) between source and destination (highway names, approximate total distance, and — if more than one route is commonly used — the 2-3 named alternatives, e.g. "via Hubli" vs "via Shimoga"). This grounds later distance estimates and meal-window inference. Note approximate total distance and drive time for the primary route.

### 2. Search multiple independent sources

Run several targeted searches, varying the query each time (don't repeat the same phrasing):
- `"<source>" "<destination>" road trip Tripoto food restaurants`
- `"<source>" "<destination>" road trip pitstops eateries`
- `"<destination>" to "<source>" road trip food stops` (reverse direction often surfaces different pages)
- If the route has named alternatives (e.g. two highway options), search each by name

Read at minimum 3-4 independent domains (Tripoto plus at least two others — travel-blog networks, self-drive/cab company blogs like Savaari, enthusiast forums like Team-BHP, or regional travel sites). A seed list built from a single source is weaker evidence and should be flagged as such.

### 3. Extract facts, never text

For each restaurant/food stop mentioned, extract only the **facts**: name, location (town/landmark), cuisine or specialty, and any distinctiveness signal (a named dish, a phrase like "worth the drive for," "statewide famous," "the original," "famous for"). Do not copy sentences or close-paraphrase a source's wording — every description written into the output must be original composition, per copyright limits. If in doubt, write it in your own words from scratch rather than adapting the source's phrasing.

### 4. Do not build an automated pipeline against any one site

Do not write or run a scraper against Tripoto (or any other site) for this task — no systematic crawling of route pages, no bulk downloads. A handful of manual searches and individual page reads per route is the ceiling. If the user asks for this to be automated into a scheduled/bulk crawl, decline that specific request and explain why (see Guardrails), while still offering to run the manual workflow again for more routes on request.

### 5. Infer meal window per stop

Using each stop's approximate position along the route (from step 1's distance/route data), infer whether it's best suited to breakfast, lunch, evening snack, or dinner. Note in the output that this is inferred, not sourced.

### 6. Compose two original lines per stop

Write exactly two self-composed sentences per restaurant describing what makes it distinctive. These must be original writing, not reworded source text.

### 7. Score each stop (Worth-It Score, 1-10)

Score by strength of distinctiveness *signal*, not by personal opinion of food quality:

| Signal found | Typical score |
| --- | --- |
| Named signature dish + explicit "worth the detour" language, corroborated by 2+ sources | 8-9 |
| Named signature dish or specialty, single strong source | 7-8 |
| "Statewide/locally famous" or similar distinctiveness claim, no specific dish named | 6-7 |
| Distinctive *format* (unusual setting, rare cuisine type, only option at a landmark stop) but no dish signal | 5-6 |
| Generic "popular"/"good option" description, no specific signal | 4-5 |
| Bare name-check with no description at all | 3-4 |

Write one sentence of reasoning per score explaining which signal (or absence of one) drove the number — never just restate the score.

### 8. Timings — never fabricate

Do not state exact opening/closing hours unless a source explicitly gives them (rare for highway editorials). Where unconfirmed, write `"status": "unconfirmed"` with a one-line note on what a reasonable assumption would be, clearly labeled as an assumption, not a sourced fact.

### 9. Write the JSON file

Use `create_file` to write the output (see Output Schema below) to a sensibly named path (e.g. `/mnt/user-data/outputs/<source>_<destination>_seed_stops.json`), then present it with `present_files`.

## Output Schema

```json
{
  "route": "<Source> to <Destination>",
  "compiled_date": "<today's date, YYYY-MM-DD>",
  "compilation_method": "Manual read-and-extract from published road-trip editorials (name the sources actually used). Facts extracted; descriptive text is self-composed, not copied from source. Not yet phone-verified for current operating status.",
  "caveats": [
    "<any route-specific caveats — e.g. single-source-only stops, routes not fully covered, etc.>"
  ],
  "seed_stops": [
    {
      "name": "<restaurant name>",
      "location": "<town, state>",
      "route_variant": "<which named route/highway this sits on, if more than one>",
      "approx_distance_from_source_km": 0,
      "hours": {
        "status": "unconfirmed | sourced",
        "note": "<assumption or the source's stated hours>"
      },
      "cuisines": ["<cuisine 1>", "<cuisine 2>"],
      "ideal_meal": "Breakfast | Lunch | Evening snack | Dinner",
      "unique_lines": [
        "<self-composed sentence 1>",
        "<self-composed sentence 2>"
      ],
      "worth_it_score": 0,
      "score_reasoning": "<one sentence citing the signal that drove the score>"
    }
  ]
}
```

## Guardrails (do not skip)

- **Facts, not expression.** A restaurant's name, location, and known dish are facts and freely usable. A source's specific sentences, narrative voice, or descriptive phrasing are not — always write original text.
- **No bulk scraping.** This skill is explicitly a *manual, individual-page* research workflow, capped at a handful of searches and page reads per route. Do not write scraper code, do not attempt systematic/scheduled crawling of Tripoto or any other site, regardless of how the request is phrased. This applies even if a prior turn in the conversation already ran the manual version — repeating the manual workflow for a new route is fine; automating it against a specific site is not.
- **Corroborate where possible.** A stop backed by 2+ independent sources is stronger evidence than a single name-check — reflect this in the score, and don't pad the list to hit a target count with single-source, no-detail entries dressed up as confident picks.
- **Flag what's unverified.** Hours, current operating status, and single-source claims should read as unverified in the output — this list is a starting point for a seed table, not a final, phone-verified dataset. Say so explicitly in `caveats`.