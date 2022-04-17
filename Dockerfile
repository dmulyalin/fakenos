FROM rockylinux:8

# install misc libs
RUN dnf install -y python3.9 nano tree

# do python libs installation
RUN python3 -m pip install pip setuptools wheel --upgrade

# run Salt Nornir libs installation from local files 
COPY . /tmp/fakenos/
RUN python3 -m pip install /tmp/fakenos/ --upgrade

ENTRYPOINT ["fakenos"]