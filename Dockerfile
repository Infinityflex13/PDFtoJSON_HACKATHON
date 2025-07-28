# Use a lightweight base Python image
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Copy dependencies and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your main script and folders
COPY pdfconv.py .
COPY input/ input/
COPY output/ output/

# Set the default command
CMD ["python", "pdfconv.py"]
