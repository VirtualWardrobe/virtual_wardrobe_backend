import resend
import logging
from env import env
import anyio, anyio.to_thread
import logging
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

resend.api_key = env.RESEND_API_KEY

# Custom exception for email sending failures
class EmailSendingError(Exception):
    pass

# Async send_mail function with retry mechanism
@retry(
    stop=stop_after_attempt(3),  # Retry up to 3 times
    wait=wait_fixed(30),         # Wait 30 seconds between retries
    retry=retry_if_exception_type(Exception),  # Retry on any exception
    before=lambda retry_state: logging.warning(f"Retrying email send attempt {retry_state.attempt_number}..."),
    after=lambda retry_state: logging.error(f"Failed after {retry_state.attempt_number} attempts") if retry_state.outcome.failed else None
)

async def send_mail(contacts: list, subject: str, message: str) -> resend.Email:
    """
    Asynchronously send an email with retry mechanism.
    Raises EmailSendingError if all retries fail.
    """
    params: resend.Emails.SendParams = {
        "from": "virtualwardrobe@virtualwardrobe.in",
        "to": contacts,
        "subject": subject,
        "html": message,
    }
    try:
        # Run synchronous resend.Emails.send in a thread
        email: resend.Email = await anyio.to_thread.run_sync(lambda: resend.Emails.send(params))
        logging.info(f"Email sent successfully to {contacts}")
        return email
    except Exception as e:
        logging.error(f"Failed to send email to {contacts}: {str(e)}")
        raise EmailSendingError(f"Failed to send email: {str(e)}")
