FROM python:3.9-slim

ADD requirements.txt .

RUN pip install -r requirements.txt
ADD testplay_assistant.py .

CMD ["python", "./testplay_assistant.py"]