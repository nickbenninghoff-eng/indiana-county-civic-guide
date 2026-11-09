"""Framework for the Indiana County Civic Guide static-site generator.

Modules:
    html        escaping + tiny tag builder (Markup = already-safe HTML)
    data        Edition loader: CSV/JSON tables, joins, status/source lookups
    sitemap     every page of the site, the nav menus and the learning paths
    shell       Page object: relative links, masthead/nav/footer, index-vs-document output
    components  badges, citations, gaps, variants, tables, officeholder cards
    charts      inline-SVG chart toolkit (bars, columns, lines, party control, results, seat dots)
    glyph       Indiana glyph + full county map from counties_svg.json
    neutrality  banned-term list shared by the builder and the checker
"""
