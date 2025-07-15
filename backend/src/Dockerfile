# Use an official Python runtime as a parent image
FROM python:3.9

ARG DEVELOPER_KEY=
ENV DEVELOPER_KEY=$DEVELOPER_KEY

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-dev

# Set the working directory in the container
WORKDIR /backend/src

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port your application listens on (if applicable)
EXPOSE 8000

# Define the command to run your application
CMD ["uvicorn", "youtube_scrape:app", "--host", "0.0.0.0", "--reload"]