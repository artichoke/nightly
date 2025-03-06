import logging
import sys


class CustomFormatter(logging.Formatter):
    """
    Custom formatter that appends extra keys from the log record formatted as
    `key=value another.key=a_thing` to the log message.
    """

    def format(self, record: logging.LogRecord) -> str:
        # First, format the message normally.
        formatted_message = super().format(record)
        # Define standard LogRecord attributes to exclude from extras.
        standard_attrs = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
        }
        # Collect extra attributes that were passed in.
        extras = {k: v for k, v in record.__dict__.items() if k not in standard_attrs}
        if extras:
            # Format extras as key=value pairs separated by a space.
            extras_str = " ".join(f"{k}={v}" for k, v in extras.items())
            formatted_message = f"{formatted_message} | {extras_str}"
        return formatted_message


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
    formatter = CustomFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


# Example usage in main:
if __name__ == "__main__":
    setup_logger()
    logging.info("Logger is set up and logging to stdout.")
