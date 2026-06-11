# Maintainer Notes

These notes are for publishing and updating the World Cup schedule site.

## Publish On GitHub Pages

1. Push this folder to a GitHub repository.
2. In the repository, open **Settings > Pages**.
3. Set **Source** to deploy from a branch.
4. Choose the branch and `/root`.
5. Save.

GitHub Pages will serve `index.html` from the repository root.

## Automatic Match Updates

The site tries to load `matches.json` first, then falls back to `Schedule 2026(Schedule).csv`.

To refresh knockout matchups from football-data.org:

1. Create a football-data.org API token.
2. In GitHub, open **Settings > Secrets and variables > Actions**.
3. Add a repository secret named `FOOTBALL_DATA_TOKEN`.
4. The workflow in `.github/workflows/update-world-cup.yml` will run after each prior round is complete.

Configured update dates:

- June 28, 2026: Round of 32 field after group stage.
- July 4, 2026: Round of 16 field after Round of 32.
- July 8, 2026: Quarterfinal field after Round of 16.
- July 12, 2026: Semifinal field after quarterfinals.
- July 16, 2026: Final and third-place matchups after semifinals.

You can also run **Update World Cup matches** manually from the GitHub Actions tab with `force` enabled.
