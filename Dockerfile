# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Create app directory
WORKDIR /app

# Copy project metadata and source
COPY pyproject.toml README.md MANIFEST.in ./
COPY bot.py ./

# Install the packaged application
RUN pip install --no-cache-dir .

# Provide a non-root user for better security
RUN useradd --create-home bot && chown -R bot:bot /app
USER bot

# Run the bot via the console script entrypoint
CMD ["invite-role-bot"]
