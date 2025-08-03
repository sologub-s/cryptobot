# temporary procedure for fast logging to both stderr/stdout and Telegram (for debug purposes)
from logging import error, info, warning


def l(sc, message: str, chat_id: int, level: str = 'error'):
    message = f"{level} : {message}"
    if level == 'error':
        error(message)
    elif level == 'warning':
        warning(message)
    else:
        info(message)
    sc.send_telegram_message(chat_id=chat_id, message=message)