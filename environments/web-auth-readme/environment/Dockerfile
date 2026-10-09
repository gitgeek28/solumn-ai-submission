FROM python:3.11-slim@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce
RUN apt-get update && apt-get install -y --no-install-recommends tmux asciinema curl \
    && rm -rf /var/lib/apt/lists/*
COPY repo/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY acme_pytest_ops /tmp/acme_pytest_ops
RUN pip install --no-cache-dir /tmp/acme_pytest_ops && rm -rf /tmp/acme_pytest_ops
WORKDIR /app
COPY repo/ /app/
