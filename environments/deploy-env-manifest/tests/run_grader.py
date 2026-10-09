import checks
from grader_lib import grade

grade(checks.functional, checks.safety, checks.regression,
      meta={"family": "deploy-env"},
      seal=[checks.H.INFRA_SNAPSHOT],
      protect=["/app", checks.H.INFRA_SNAPSHOT])
