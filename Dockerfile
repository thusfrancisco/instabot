FROM python:3.11.2-slim

# Install requirements and playwright
COPY requirements.txt .
COPY setup.sh .
RUN sh setup.sh

# Copy source code
COPY src ./src
COPY tests ./tests
COPY main.py .
COPY pytest.ini .

# Copy environment variables
COPY .env .

ENTRYPOINT [ "python" ]
CMD [ "-m", "pytest", "--headed", "main.py", "-k", "unfollow_batch", "-s" ]