# Island Migration Dashboard

Browse migrant-copy evidence, independent local optima networks (LONs), and paired 2D STN/LON figures for NK(18,6), TSP burma14, and 700-vertex weighted Max-Cut. The site covers seven algorithms and 210 matched pairs. It includes the 12,600 viewer records, the original 213 active PNGs, and CSV exports. The published result is a static research snapshot.

## Deploy with GitHub and Vercel

1. Put the contents of this folder at the root of the GitHub repository.
2. In Vercel, select **Add New → Project**, then import that repository.
3. Keep the root directory at the repository root. The included `vercel.json` configures **Other** and serves `public/`. There are no dependencies to install, environment variables to set, or build commands to run.
4. Deploy and open the production URL. Check the three problem selections and download one CSV before sharing it.

[Vercel GitHub import guide](https://vercel.com/docs/git/vercel-for-github) · [Static build settings](https://vercel.com/docs/builds/configure-a-build)

## Preview locally

Run this from the repository root, then open [the local preview](http://127.0.0.1:8000).

```sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory public
```

The viewer loads a compressed dataset when a problem is selected. **Export CSV** saves a regular CSV. Use a current browser and serve the site over HTTP or HTTPS. For a link that opens a specific view, append `?problem=maxcut700&algorithm=ga` to the deployed URL.

## Refresh the snapshot

After the source dashboard has been republished in the FYP project, run the exporter from this repository. Supply a path to the original `lon-reproduction` folder and a fresh destination. Verify the preview before replacing `public/`.

```sh
python3 scripts/export_dashboard.py ../lon-reproduction public-refresh
```

The export contains only the three active problems selected in the viewer. Raw island logs, archived Max-Cut instances, knapsack results, and internal reports stay in the research project.
