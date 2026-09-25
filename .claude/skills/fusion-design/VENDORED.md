# Vendored copy

`fusion-design/` and the sibling `print-in-place-design/` are copies of the
skills from the FusionHelper project:

    C:\Users\gethi\sources\FusionHelper\skills\fusion-design
    C:\Users\gethi\sources\FusionHelper\skills\print-in-place-design

fusion-design copied 2026-09-06, re-checked identical 2026-09-25;
print-in-place-design copied 2026-09-25. FusionHelper is the source of truth.
Re-copy after any change there rather than editing these copies.

The `fusionhelper` Python package (preflight gate, bundler, verify block) is a
separate dependency, installed editable (`pip install -e
C:\Users\gethi\sources\FusionHelper`) into Python 3.12 at
`%LOCALAPPDATA%\Programs\Python\Python312`. Verified 2026-09-25: the preflight
gate runs and passes on `cad/lap_disc_n.bundled.py`.
