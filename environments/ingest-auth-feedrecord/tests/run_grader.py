"""Entry point: all three axes run on every attempt; grader_lib decides the reward."""
import checks
from grader_lib import grade

grade(checks.functional, checks.safety, checks.regression,
      meta={"family": "ingest-auth"},
      seal=[checks.PROD_DB],
      protect=["/app"])
