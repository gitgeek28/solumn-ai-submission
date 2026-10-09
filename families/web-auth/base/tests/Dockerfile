# Separate verifier image (tests/ is the build context; Harbor does not upload tests in this mode).
FROM python:3.11-slim@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce
RUN useradd --system --uid 4242 --no-create-home --shell /usr/sbin/nologin sandbox
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
# Artifact parents pre-created; the grader still distinguishes "absent" from "wrong".
RUN mkdir -p /app /tmp/telemetry_snapshot /logs/verifier /grader
COPY . /tests/
RUN chmod +x /tests/test.sh && chmod -R a+rX /tests
WORKDIR /tests
