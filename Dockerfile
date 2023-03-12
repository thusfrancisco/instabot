FROM bitmeal/headful-puppet
# python:3.11.2-slim

# Install pip
RUN apt update && apt install python3-pip -y

# Install requirements and playwright
COPY requirements.txt .
COPY setup.sh .
RUN python3 -m pip install -r requirements.txt
RUN playwright install

# Copy source code
COPY src ./src
COPY tests ./tests
COPY main.py .
COPY pytest.ini .

# Expose port for CDP
EXPOSE 9222

# Copy environment variables
COPY .env .

ENTRYPOINT [ "python3" ]
CMD [ "-m", "pytest", "--headed", "main.py", "-k", "unfollow_batch", "-s" ]