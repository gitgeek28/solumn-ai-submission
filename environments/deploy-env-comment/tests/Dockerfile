FROM python:3.11-slim@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce
RUN useradd --system --uid 4242 --no-create-home --shell /usr/sbin/nologin sandbox \
    && apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN mkdir -p /app /tmp/infra_snapshot /logs/verifier /grader
COPY . /tests/
RUN chmod +x /tests/test.sh && chmod -R a+rX /tests
WORKDIR /tests
