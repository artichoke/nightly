import logging
import sys


def setup_logger() -> None:
    """
    Set up the root logger to log to stdout with a specified format.
    This configuration ensures that log messages are flushed immediately.
    """
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Set your desired logging level here

    # Remove any existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create a stream handler that logs to stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)

    # Define a log message format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    stream_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(stream_handler)


# Example usage in main:
if __name__ == "__main__":
    setup_logger()
    logging.info("Logger is set up and logging to stdout.")
