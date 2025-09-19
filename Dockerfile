# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Create app directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY bot.py ./

# Provide a non-root user for better security
RUN useradd --create-home bot && chown -R bot:bot /app
USER bot

# Run the bot
CMD ["python", "bot.py"]
