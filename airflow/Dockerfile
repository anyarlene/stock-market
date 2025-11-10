FROM ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.9.1}

USER airflow

COPY requirements.txt /tmp/airflow-requirements.txt
RUN pip install --user --no-cache-dir -r /tmp/airflow-requirements.txt

