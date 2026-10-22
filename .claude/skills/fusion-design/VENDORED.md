# Vendored copy

`fusion-design/` and the sibling `print-in-place-design/` are copies of the
skills from the FusionHelper project:

    C:\Users\gethi\sources\FusionHelper\skills\fusion-design
    C:\Users\gethi\sources\FusionHelper\skills\print-in-place-design

fusion-design copied 2026-09-06, re-checked identical 2026-09-25;
print-in-place-design copied 2026-09-25. FusionHelper is the source of truth.
Re-copy after any change there rather than editing these copies.

The `fusionhelper` Python package (preflight gate, bundler, verify block) is a
separate dependency. The editable install into Python 3.12 recorded on
2026-09-25 is gone: by 2026-10-18 the machine has only Python 3.13, without
it. Run the gate in a throwaway uv environment instead, with nothing installed
globally (verified 2026-10-18 on `cad/lap_disc_n.bundled.py` and
`cad/lap_disc_o.bundled.py`):

    uv run --no-project --python 3.12 --with-editable C:/Users/gethi/sources/FusionHelper python -m fusionhelper.bundle cad/lap_disc_o.py
    uv run --no-project --python 3.12 --with-editable C:/Users/gethi/sources/FusionHelper python -m fusionhelper.preflight cad/lap_disc_o.bundled.py

The Fusion MCP server listens at `http://127.0.0.1:27182/mcp` while Fusion is
running. It is configured as an MCP server only in the FusionHelper project,
so from this repo, scripts go through FusionHelper's stdlib client
(`tests/integration/mcp_client.py`, `McpClient.execute`) via the launcher
(added 2026-10-22):

    python cad/fusion_run.py cad/<script>.bundled.py

It prints the script's stdout and any error text, then exits 0 when the last
`FH_VERDICT1` line says pass, 2 on any other verdict, 3 when the script raised
or printed no verdict. `FUSION_MCP_URL` overrides the endpoint. A script that
raises is rolled back atomically, so the document is left as it was.
