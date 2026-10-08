# TCSO · tcso.world

A bilingual, static landing page for the Third-Country Supporters Organization. It is built with plain HTML, CSS and JavaScript, and publishes to GitHub Pages from the `main` branch root.

## Update the page

Edit `index.html` and `styles.css`. Keep social share metadata and image dimensions together in the document head. The site uses the supplied TCSO identity artwork from `assets/` and does not depend on a build service or external fonts.

## GitHub Pages and DNS

The `CNAME` file sets the custom domain to `tcso.world`. GitHub Pages must be enabled for the repository with the `main` branch root as the publishing source. At Name.com, set the apex records to GitHub Pages and create the `www` CNAME:

| Type | Host | Value |
| --- | --- | --- |
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| AAAA | `@` | `2606:50c0:8000::153` |
| AAAA | `@` | `2606:50c0:8001::153` |
| AAAA | `@` | `2606:50c0:8002::153` |
| AAAA | `@` | `2606:50c0:8003::153` |
| CNAME | `www` | `Thiha-Lynn.github.io` |

Keep the GitHub ownership-verification TXT record `_github-pages-challenge-Thiha-Lynn.tcso.world` in place. Remove only Name.com parking records for `@` and `www`; leave email/MX records alone. Do not add a wildcard record. DNS can take time to propagate; enable GitHub Pages HTTPS after GitHub detects the domain.

## Support records

The home-page archive links to `/support/` and four individual certificate pages. Original, unedited images are in `assets/certificates/`. Each public HTML page includes its own canonical URL, description, Open Graph and Twitter image metadata. Add new record URLs to `sitemap.xml`. The 404 page is marked `noindex`.

Healthcare record `/support/healthcare/`: certificate TL-26/1058, dated 16 September 2026, acknowledging MMK 700,000 for hospital healthcare services. The supplied image is preserved unedited.
