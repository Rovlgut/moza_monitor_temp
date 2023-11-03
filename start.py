import threading

from modules.app import App
from modules.log_util import logger


# def thread_custom_excepthook(args):
#     logger.info(f"Error {args.exc_value} in thread {args.thread}")
#     args.thread.error_message(args.exc_value)
#     logger.exception(args.exc_value)

# threading.excepthook = thread_custom_excepthook

app = App()
app.mainloop()