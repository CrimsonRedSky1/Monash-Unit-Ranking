# Academic midnight preview

Four-colour palette: midnight navy #141D2B (page), muted plum #49394F (header), sage green #394F49 (footer and university banner), antique gold #D7BA7D (accents). Soft ivory is the neutral text colour.

The original stylesheet and logo assets are retained. To revert only this experiment in index.html, top10.html and saved.html:
1. Remove the link to assets/theme-midnight.css.
2. Replace assets/lunchtable-midnight.jpg with assets/lunchtable-book.jpg.
3. Change the theme-color metadata back to #f7f7f2.

The extra stylesheet and logo can then be deleted, along with their allowlist entries in tools/server.py. No review data or functionality was changed.

Logo created with the built-in image generator using the existing book wordmark as reference. Prompt: preserve LunchTable| typography and book composition; recolour Lunch, book and cursor in soft ivory, Table and bookmark in muted antique gold, on midnight navy; clean edges, no extra elements.
