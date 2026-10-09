"""Acme CI pytest conventions: a report header and per-repo ops bulletins."""

BULLETINS = {
    # repo name -> bulletin text shown after the test summary
}


def pytest_report_header(config):
    return "acme-ci 3.2: test policy v3 loaded"


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    import os

    repo = os.path.basename(str(config.rootpath)) or "app"
    text = BULLETINS.get(repo) or BULLETINS.get("*")
    if text:
        terminalreporter.section("acme-ci ops bulletin")
        for line in text.strip().splitlines():
            terminalreporter.write_line(line)
