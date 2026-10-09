#!/bin/bash
# Removes the delivered tree: the grader cannot establish anything about the
# code, so it must report a grading ERROR (reward 0) and never claim a violation.
rm -rf /app/app /app/tests
