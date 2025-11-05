import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configparser
import os
import traceback

def send_email(subject: str, body: str, to_list: list):
    """
    Gửi email thông báo khi ETL thành công hoặc thất bại.
    """
    try:
        # Đọc thông tin email từ file config.ini
        config = configparser.ConfigParser()
        config.read(os.path.join("config", "config.ini"))
        email_cfg = config["email"]

        sender = email_cfg["sender"]
        password = email_cfg["password"]

        # Tạo nội dung email
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = ", ".join(to_list)
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Gửi mail qua SMTP Gmail
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Mã hóa kết nối
            server.login(sender, password)
            server.send_message(msg)

        print(f"📧 Email đã gửi tới: {', '.join(to_list)}")

    except Exception as e:
        print("❌ Lỗi khi gửi email:", e)
        print(traceback.format_exc())
