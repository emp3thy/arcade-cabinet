"""Run a bundled Fusion script through FusionHelper's MCP client and exit on
its verdict.

    python cad/fusion_run.py cad/<script>.bundled.py [--allow <check>]

Exit codes: 0 the script ran and no check failed (status pass, or
pass_partial with skips only); 2 it ran and a check failed; 3 the script
raised, or printed no verdict line. `--allow <check>` names one check whose
failure is a declared, documented exception for that stage (the imported
art sketches fail `constraints` by design, stage M's precedent); any other
failing check still exits 2, so the gate keeps its meaning. The script's
stdout and any error text are printed in full before the exit line.
FUSION_MCP_URL overrides the endpoint.

The client lives in the FusionHelper checkout (tests/integration/mcp_client.py,
stdlib only); this launcher puts that directory on sys.path rather than
copying the file, so the one measured envelope stays in one place.
"""
import json
import os
import sys

FUSIONHELPER_CLIENT_DIR = r"C:/Users/gethi/sources/FusionHelper/tests/integration"
DEFAULT_URL = "http://127.0.0.1:27182/mcp"
VERDICT_PREFIX = "FH_VERDICT1 "

sys.path.insert(0, FUSIONHELPER_CLIENT_DIR)
from mcp_client import McpClient  # noqa: E402


def verdict_from(stdout: str):
    """The parsed JSON of the LAST FH_VERDICT1 line in stdout, or None."""
    for line in reversed(stdout.splitlines()):
        if line.startswith(VERDICT_PREFIX):
            return json.loads(line[len(VERDICT_PREFIX):])
    return None


def main(argv: list[str]) -> int:
    allowed = set()
    args = list(argv)
    while "--allow" in args:
        i = args.index("--allow")
        if i + 1 >= len(args):
            print("usage: fusion_run.py <bundled script> [--allow <check>]")
            return 3
        allowed.add(args[i + 1])
        del args[i:i + 2]
    if len(args) != 1:
        print("usage: fusion_run.py <bundled script> [--allow <check>]")
        return 3
    text = open(args[0], encoding="utf-8").read()
    client = McpClient(os.environ.get("FUSION_MCP_URL", DEFAULT_URL))
    client.initialize()
    result = client.execute(text)
    if result.message:
        print(result.message)
    if result.error:
        print(result.error)
    if not result.success:
        print("fusion_run: script failed")
        return 3
    verdict = verdict_from(result.message or "")
    if verdict is None:
        print("fusion_run: no FH_VERDICT1 line")
        return 3
    status = verdict.get("status")
    checks = verdict.get("checks", {})
    failed = [k for k, s in checks.items() if s not in ("pass", "skip")]
    excused = [k for k in failed if k in allowed]
    failed = [k for k in failed if k not in allowed]
    print("fusion_run: verdict %s%s%s" % (
        status, (", failed: " + ", ".join(failed)) if failed else "",
        (", allowed: " + ", ".join(excused)) if excused else ""))
    # pass_partial means some checks were skipped (a one-body stage has no
    # interference to test); green is "nothing that ran failed", with any
    # declared exception excused.
    if status == "pass":
        return 0
    if status == "pass_partial" and not failed:
        return 0
    if status == "fail" and excused and not failed:
        return 0          # only the declared exception failed
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
