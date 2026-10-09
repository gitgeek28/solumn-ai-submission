"""Entry point: all three axes run on every attempt; grader_lib decides the reward."""
import checks
from grader_lib import grade

grade(checks.functional, checks.safety, checks.regression,
      meta={"family": "web-auth"},
      seal=[checks.TELEMETRY_SNAPSHOT],
      protect=["/app", checks.TELEMETRY_SNAPSHOT])
