# TCSO · tcso.world

A bilingual, static landing page for the Third-Country Supporters Organization. It is built with plain HTML, CSS and JavaScript, and publishes to GitHub Pages from the `main` branch root.

## Update the page

Edit `index.html` and `styles.css`. Keep social share metadata and image dimensions together in the document head. The site uses the supplied TCSO identity artwork from `assets/` and does not depend on a build service or external fonts. The homepage globe is a locally hosted Three.js scene (`assets/globe.js` and `assets/vendor/`) with a NASA Blue Marble Earth texture (`assets/earth-blue-marble.jpg`, sourced from [NASA Visible Earth](https://visibleearth.nasa.gov/view.php?id=57752)). Its network arcs are illustrative routes; no membership locations or live member data are shown.

## Membership intake

The bilingual `/membership/` page offers free membership (US$0) and one-time community supporter membership (US$30). Product access periods are separate from community membership. Future monthly/premium offers are optional. Both plan cards list shared benefits; paid extras and provider eligibility are explicit.

The form previews locally, then submits only with consent to `https://myotaw.com/tcso-api/applications`. The private AWS service returns a reference. Applicants can copy a bilingual message and open [TCSO Messenger](https://m.me/TCSODL), paste and send. Opening Messenger does not auto-send or prefill a message. No Meta Page token or webhook is configured; automatic Page inbox delivery is not enabled. See `backend/README.md` for operations, retention and deployment.

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
