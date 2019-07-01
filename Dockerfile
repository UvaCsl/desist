FROM ubuntu:18.04
#Install the dependencies
RUN apt-get update && apt-get install -y python3 xsltproc

#Copy the workflow to /app in the container
COPY ./workflow /app

ENTRYPOINT ["python3", "/app/run_workflow.py"]

