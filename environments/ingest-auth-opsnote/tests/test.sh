#!/bin/bash
# Fail closed before anything else can go wrong; grader_lib overwrites this.
mkdir -p /logs/verifier && printf 0 > /logs/verifier/reward.txt
cd /tests && python3 /tests/run_grader.py
exit 0
