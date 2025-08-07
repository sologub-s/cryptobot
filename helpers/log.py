# temporary procedure for fast logging to both stderr/stdout and Telegram (for debug purposes)
from logging import error, info, warning


def l(sc, message: str, level: str = 'error', chat_id: int = None):
    message = f"{level} : {message}"
    if level == 'error':
        error(message)
    elif level == 'warning':
        warning(message)
    else:
        info(message)
    if chat_id is not None:
        sc.send_telegram_message(chat_id=chat_id, message=f"<pre>{message}</pre>")