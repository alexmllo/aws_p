FROM python:3.8

# Working directory in the container
WORKDIR /app

# Copy requirements file into the container
COPY requirements.txt .

RUN pip install -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

CMD [ "python", "app.py" ]