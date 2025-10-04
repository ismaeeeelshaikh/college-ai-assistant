import random
from datetime import datetime, timedelta
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from passlib.context import CryptContext

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from ..models.user import User
from ..models.password_reset_token import PasswordResetToken

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

conf = ConnectionConfig(
    MAIL_USERNAME="shaikhaptab15@gmail.com",
    MAIL_PASSWORD="oyqzypgoormoiabh",
    MAIL_FROM="shaikhaptab15@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

def generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"

async def send_reset_email(email: str, otp: str):
    message = MessageSchema(
        subject="College AI Chatbot Password Reset OTP",
        recipients=[email],
        body=f"Your OTP to reset your password is: {otp}",
        subtype="plain"
    )
    fm = FastMail(conf)
    await fm.send_message(message)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def create_password_reset_token(db: AsyncSession, user: User, otp: str):
    expiry = datetime.utcnow() + timedelta(minutes=15)
    token = PasswordResetToken(user_id=user.id, otp=otp, expires_at=expiry)
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return token

async def verify_password_reset_token(db: AsyncSession, email: str, otp: str):
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    if not user:
        raise Exception("User not found")

    result_token = await db.execute(
        select(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.otp == otp,
            PasswordResetToken.used == 0,
            PasswordResetToken.expires_at > datetime.utcnow(),
        )
    )
    token = result_token.scalars().first()
    if not token:
        raise Exception("Invalid or expired OTP")

    return user, token

async def mark_token_used(db: AsyncSession, token: PasswordResetToken):
    token.used = 1
    db.add(token)
    await db.commit()

async def update_user_password(db: AsyncSession, user: User, new_password: str):
    user.hashed_password = hash_password(new_password)
    db.add(user)
    await db.commit()
