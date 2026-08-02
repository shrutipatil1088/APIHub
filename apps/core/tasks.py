import logging
from celery import shared_task

logger = logging.getLogger(__name__)



# @shared_task : This decorator tells Celery:
#                 "Register this function as a background task."
#                  Without it: just a normal python function
@shared_task
def say_hello():
    """
    First learning task for Celery.
    When executed:
    - Prints "Hello from Celery!" to stdout (visible in Celery worker terminal)
    - Writes a log message
    - Returns "Task Completed"
    """
    print("Hello from Celery!")
    logger.info("say_hello Celery task executed successfully.")
    return "Task Completed"
