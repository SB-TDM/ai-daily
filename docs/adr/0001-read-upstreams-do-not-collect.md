# Read two Upstreams, do not run a collector

Superseded by 0005. The Run no longer reads agents-radar or Hugging Face.

We send an internal 日报. We do not operate a news platform. A Run reads the agents-radar daily RSS and Hugging Face Daily Papers, then an LLM places items onto plates and composes one 日报. We do not self-host Horizon, ai-news-brief, or any other collector. Those projects already publish curated lists; running one would add a database, scrapers, and a second editorial pipeline we do not need.
