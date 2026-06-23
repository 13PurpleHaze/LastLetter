class EmailTemplates:
    VERIFICATION_SUBJECT = "Подтверждение email"
    VERIFICATION_TEXT = "Подтвердите email перейдя по ссылке: {link}"

    PASSWORD_RESET_SUBJECT = "Сброс пароля"
    PASSWORD_RESET_TEXT = "Подтвердите сброс пароля перейдя по ссылке: {link}"

    INVITE_SUBJECT = "Инвайт"
    INVITE_TEXT = (
        "Подтвердить инвайт пользователя с email: {email}, перейдя по ссылке: {link}"
    )
