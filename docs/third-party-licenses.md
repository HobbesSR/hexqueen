# Third-party licences and notices

Status: audit of 2026-11-07, against `master` after 3ee0ae8.

`LICENSE` (MIT) covers the project's original work only. Third-party material keeps its own
licence. This document records what the project redistributes, the evidence for each licence,
how each obligation is met, and how to keep it current. `THIRD-PARTY-NOTICES.txt` holds the
licence texts and notices for anything redistributed; `python run.py --package` puts both files
into the itch.io zip next to `index.html`.

## Licence choice

MIT, matching the sibling project Last Exit (`astra_test`): anyone may reuse the code and
assets, commercially or closed-source, provided the copyright notice and licence text travel
with copies.

## Delivery

Other people receive project material by two routes:

- **The web game**: `web/`, served as static files or uploaded to itch.io as the zip from
  `python run.py --package` (everything in `web/` except `web/test/`, plus `LICENSE` and
  `THIRD-PARTY-NOTICES.txt`).
- **The repository**: source code, docs and tests.

Neither contains third-party code, fonts or images.

## Inventory

### Redistributed

None.

### Used but not redistributed

| Component | Licence | How it is used | Why no notice is due |
| --- | --- | --- | --- |
| Gabarito | SIL OFL 1.1 | `web/index.html` links Google Fonts CSS | The player's browser downloads it from Google; no font file is shipped |
| Young Serif | SIL OFL 1.1 | as above | as above |
| matplotlib | Matplotlib License (PSF-based) | Python generator's PNG/PDF output | Installed from PyPI via `requirements.txt`; not vendored |
| NumPy | BSD-3-Clause | Python generator | as above |
| Node.js test runner (`node --test`) | MIT | runs `web/test/` locally | development tool; not shipped |

## Project material checked for outside provenance

- Search of every tracked file for copyright, licence, "adapted from", "based on", "port of" and
  external URL markers found only the Google Fonts link and the SVG namespace URI.
- `web/index.html` SVG symbols (the queen bee, the ×, the hexagon wordmark): hand-written
  geometry (ellipses, rects and short paths) in the page itself, written for this project with
  AI assistance. They carry no editor metadata or attribution an imported asset would. Treated as
  original project assets under `LICENSE`. Being AI-assisted, their copyright may be thin; that
  limits what MIT grants others, not what the project may do with them.
- `src/dancing_links.py`: an original implementation of Knuth's Algorithm X with Dancing Links.
  Algorithms are not copyrightable; no code was copied.
- The game's rules belong to the family of region-and-line queen puzzles. Mechanics are not
  copyrightable; no names, art, text or levels from any existing game are included.

## Compatibility rules

Permissive licences (MIT, ISC, BSD, Apache-2.0, Zlib, PSF, Boost) and CC0/CC BY assets are
compatible: add them with their notices. CC BY needs a credit line in the notices file.
Apache-2.0 also needs any NOTICE file reproduced. SIL OFL 1.1 is compatible for fonts that are
bundled unmodified (or renamed if modified) with the licence text included.

Refuse without the repository owner's decision, because they would constrain the project's
licence or its users: GPL, AGPL and LGPL; MPL and EPL; CC BY-SA and other share-alike asset
licences; anything non-commercial (CC BY-NC) or no-derivatives; and anything without a licence.
"No licence" means all rights reserved, which covers code, art, fonts, sounds or puzzles found
online with no terms attached.

## Updating

When third-party code, fonts, images, sounds or other assets are added, or a dependency changes:

1. Check its licence against the rules above. Read the actual LICENSE/NOTICE files and, for
   bundles, the source headers; never paraphrase a licence.
2. If it will be redistributed (copied into `web/`, vendored, or included in the zip), add its
   full licence text and copyright notices to `THIRD-PARTY-NOTICES.txt` and move its row to
   "Redistributed" above.
3. Record where a new asset came from in its commit message or in this document.
4. Update the audit date at the top of this file and of `THIRD-PARTY-NOTICES.txt`.
