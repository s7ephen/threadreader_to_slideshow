FROM debian:buster
MAINTAINER s7ephen
RUN apt-get update
RUN apt-get install -y python2 python-dev python-pip build-essential swig git 
RUN apt-get install -y python-lxml python-requests
#RUN pip install requests

VOLUME ["/dev_share/"]
WORKDIR /root/

COPY ["code/","/root/"]
RUN chmod -R a+x /root/*.py
RUN export PATH=$PATH:/root/
#ENTRYPOINT ["/root/threadreader_to_slideshow.py"]
CMD ["/root/threadreader_to_slideshow.py"]
