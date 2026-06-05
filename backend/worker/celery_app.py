# worker/celery_app.py

from celery import Celery

# Create the Celery application.
# - "worker" is just the name we give this app — shows up in logs.
# - broker: Redis is the queue. Celery sends tasks here, worker picks them up.
# - backend: Redis also stores task results so FastAPI can check on them later.
celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["worker.tasks"]
)

# Tell Celery where to find our task functions.
# Without this, it won't know "process_document" exists.


# Optional but good practice — serialize everything as JSON, not pickle.
# Pickle can be a security risk. JSON is safe and readable.
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    broker_connection_retry_on_startup=True, 
    task_default_queue="document_processing" # ← add this
)