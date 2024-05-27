FROM python:3.10-slim-bullseye
# Setup env first to make use of docker caching
COPY requirements.txt ./
RUN pip install -r requirements.txt
# now copy the rest of the files to the container
COPY . ./
WORKDIR /
CMD ["python", "ilaris_bot.py"]