FROM python:3.10

ENV HOME /root
WORKDIR /root

COPY . .

RUN pip3 install -r requirements.txt

EXPOSE 8080

CMD python -u server.py
