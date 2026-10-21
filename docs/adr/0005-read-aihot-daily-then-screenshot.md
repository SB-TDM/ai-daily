# Read the aihot daily, then screenshot our page

We send an internal 日报. A Run reads `https://aihot.news/api/v1/dailies/YYYY-MM-DD` for the Beijing date, lays the lead and sections into our own HTML, and screenshots that page. It does not read agents-radar or Hugging Face, does not screenshot aihot.news, and does not call a model to write or choose copy. `flashes` are not drawn. This supersedes 0001 and 0004.
