# LearnGraph

**LearnGraph** is a long-term initiative aimed at building a "Google Maps for learning" — a networked system for navigating concepts, skills, and educational pathways across the web. The project can be explored further at [LearnGraph.org](https://www.learngraph.org).

This repository contains the social tagging and discovery infrastructure for LearnGraph. The goal is to surface and analyze hashtags related to LearnGraph on social media platforms, identify content trends, evaluate performance, and surface influencers. This metadata will later inform a broader discovery and recommendation engine.

---

## Hashtag Universe

The following hashtags are being tracked across various social media platforms.

### Core Education
- #LearnGraph
- #EdTech
- #OpenEducation
- #FutureOfEducation
- #PersonalizedLearning
- #LifelongLearning
- #PeerLearning
- #LearningCommunities

### Cognitive & AI
- #CognitiveScience
- #HowWeLearn
- #Metacognition
- #AIinEducation
- #LearningAnalytics

### Knowledge Systems
- #KnowledgeGraph
- #KnowledgeMapping
- #SemanticWeb
- #OntologyDesign

### Decentralized + Web3
- #DecentralizedLearning
- #Web3Education
- #OpenAccess

### Platform-Specific
- #BlueskySocial
- #ATProtocol

---

## Development Roadmap

### Near-Term Improvements

- **Script Enhancements:**
  - Add CLI arguments for custom input/output filenames, auto-opening the HTML file, and specifying file format.
  - Add optional live-watching with `watchdog` to regenerate on file changes.
- **HTML Improvements:**
  - Add client-side sorting/filtering (e.g., via List.js or DataTables).
  - Add copy-to-clipboard buttons for hashtags.
  - Add inline export options (Markdown/CSV/JSON).
  - Improve accessibility and create a responsive layout (viewport, dark mode).
  - Add a favicon and metadata for branding.

### Mid-Term Development Goals

- Scrape metadata for top 50 hashtags on each platform.
- Build influencer detection (threshold-based or clustering).
- Implement auto-tag clustering (e.g., using cosine similarity on hashtag use).
- Deploy a table explorer frontend (React/Next.js or SvelteKit).
- Integrate with the LearnGraph project API or UI.

### Long-Term Goals

- Connect hashtag data to the concept graph.
- Add temporal trend analysis.
- Enable learning pathway recommendations based on social signals.
- Tie into knowledge graph browsers or map-based UI (e.g., force-directed graphs).

---

## To-Dos

- [ ] Finalize top 20 hashtags with supporting data (engagement, frequency, uniqueness).
- [ ] Begin a manually curated `Influencer List.md`.
- [ ] Build a graph-style visual map of hashtags + people.
- [ ] Plan post types for social (commentary, repost, remix, ask-me-anything).
- [ ] Develop content hooks for each thematic hashtag.
- [ ] Finalize HTML rendering improvements.
- [ ] Begin prototyping a scraping routine for 2-3 platforms.
- [ ] Create a basic CLI wrapper script for recurring analysis.
- [ ] Organize vault/codebase into a unified structure.
- [ ] Scrape metadata for top 50 hashtags on each platform.
- [ ] Build influencer detection (threshold-based or clustering).
- [ ] Auto-tag clustering (cosine similarity on hashtag use).
- [ ] Deploy table explorer frontend (React/Next.js or SvelteKit).
- [ ] Integrate with LearnGraph project API or UI.
- [ ] Connect hashtag data to concept graph.
- [ ] Add temporal trend analysis.
- [ ] Enable learning pathway recommendations based on social signals.
- [ ] Tie into knowledge graph browsers or map-based UI (e.g., force-directed graphs).
- [ ] Publish newsletter draft.
- [ ] Perform noise cancellation on Talal's interview.
- [ ] Post Talal's interview.

---

## Prototype Feedback Questions

- Based on the current prototype, what about LearnGraph is working?
- What is not working?
- What changes would you make to LearnGraph?
- How might using LearnGraph help you reach your educational goals?

---

## Community

A Discord or Slack space for Gemini CLI users to discuss the project is being considered.
