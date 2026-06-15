class EmailTemplates:
    VERIFICATION_SUBJECT = "Подтверждение email"
    VERIFICATION_TEXT = "Подтвердите email перейдя по ссылке: {link}"

    PASSWORD_RESET_SUBJECT = "Сброс пароля"
    PASSWORD_RESET_TEXT = (
        "Подтвердите сброс пароля перейдя по ссылке: <a href='{link}'>подтвердить</a>"
    )
