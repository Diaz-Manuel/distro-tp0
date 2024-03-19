FROM python:3.9.7-slim
COPY server/common /common
COPY server/tests /tests
COPY server/main.py /main.py
COPY lib /lib
RUN python -m unittest tests/test_common.py
ENTRYPOINT ["/bin/sh"]
