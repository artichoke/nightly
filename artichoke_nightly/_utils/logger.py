import logging
import sys
from functools import cache


@cache
def standard_log_record_attrs() -> set[str]:
    """
    Get the standard attributes of a LogRecord.

    This function is cached to avoid recalculating the set of standard attributes
    for each LogRecord instance.

    Returns:
        set[str]: The standard attributes of a LogRecord.
    """
    return set(
        logging.LogRecord("", logging.INFO, "", 1, "", None, None, "").__dict__.keys()
    )


class ExtrasKeyValueFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base_log = super().format(record)

        # Extract only extra fields
        extra_fields = {
            k: v
            for k, v in record.__dict__.items()
            if k not in standard_log_record_attrs()
        }

        # Format extra fields as key=value
        extra_str = " ".join(f"{k}={v}" for k, v in extra_fields.items())

        return f"{base_log} {extra_str}".strip()


def setup_logger() -> None:
    """
    Set up the root logger to log to stdout with a specified format.
    This configuration ensures that log messages are flushed immediately.
    """
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Set your desired logging level here

    # Clear existing handlers to avoid duplicate logs.
    if logger.hasHandlers():
        logger.handlers.clear()

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    formatter = ExtrasKeyValueFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


# Example usage in main:
if __name__ == "__main__":
    setup_logger()
    logging.info("Logger is set up and logging to stdout.")
