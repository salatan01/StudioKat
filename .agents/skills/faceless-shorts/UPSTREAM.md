# Upstream provenance

- Source: `/home/superkat01/Projects/faceless-shorts`
- Vendored: 2026-11-19
- Permission: the user confirmed permission to vendor this skill into OpenMontage on 2026-11-19.
- This is a maintained fork. The immutable tree is `scripts/**`, `styles/*/STYLE.md`,
  `styles/*/style-sheet.png`, and `styles/*/example/**`.
- Compatibility edits are limited to `SKILL.md`, `README.md`, `references/**`, and this file.
  The generated diff is `UPSTREAM.patch`.
- Checksums: `UPSTREAM.sha256` lists every immutable file.

Regenerate the checksums from the skill root:

```bash
find scripts styles -type f -print0 | sort -z | xargs -0 sha256sum > UPSTREAM.sha256
```
