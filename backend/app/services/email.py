from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

# Direct SMTP config for FastAPI-Mail
conf = ConnectionConfig(
    MAIL_USERNAME = "shaikhaptab15@gmail.com",
    MAIL_PASSWORD = "oyqzypgoormoiabh",  # Use app password if Gmail
    MAIL_FROM = "shaikhaptab15@gmail.com",   # Sender address
    MAIL_PORT = 587,                      # for TLS
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

async def send_otp_email(email: str, otp: str):
    message = MessageSchema(
        subject="Your OTP Code",
        recipients=[email],
        body=f"Your OTP for verification is: {otp}. It expires in 10 minutes.",
        subtype="plain",
    )
    fm = FastMail(conf)
    await fm.send_message(message)

