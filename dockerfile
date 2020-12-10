# Use the official image as a parent image.
FROM python:3.9-slim

# Set the working directory.
WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y python-opencv
RUN pip install gunicorn
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY start.sh ../start.sh
RUN chmod +x ../start.sh
CMD [ "../start.sh" ]
