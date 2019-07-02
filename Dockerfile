FROM ubuntu:18.04
#Install the dependencies
RUN apt-get update && apt-get install -y python3 xsltproc python3-lxml apt-transport-https ca-certificates curl software-properties-common
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
RUN add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
RUN apt-get update && apt-get install -y docker-ce

#Copy the workflow to /app in the container
COPY ./workflow /app

ENTRYPOINT ["python3", "/app/run_workflow.py"]

