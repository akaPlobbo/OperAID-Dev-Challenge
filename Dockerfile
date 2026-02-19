FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend ./backend
COPY frontend ./frontend

# Expose port
EXPOSE 8000

# Run the application
CMD ["sh", "-c", "python backend/app/mqtt_simulator.py & python backend/app/server.py"]
