import os
import ssl
import time
import base64
import smtplib
import logging
import schedule

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

from deta import Deta
from dotenv import load_dotenv

ssl._create_default_https_context = ssl._create_unverified_context
logging.basicConfig(level=logging.DEBUG)

# Load environment variables from .env file
load_dotenv()

DETA = Deta(os.getenv("DETA_KEY"))

def connect_db(db: str):
    return DETA.Base(db)

def get_subscription_list() -> list:
    subscription_db = connect_db('subscription_db')
    subscribed_list = []
    for subscribed in subscription_db.fetch().items:
        if subscribed['is_subscribed']:
            subscribed_list.append(subscribed['key'])
    return subscribed_list

def get_item(item_name: str) -> dict:
    item_db = connect_db('item_db')
    key = item_name.replace(' ',f'_')
    return item_db.get(key=key)

def get_image(catalog: str, name:str):
    return DETA.Drive('images_db').get(f"/{catalog}/{name}").read()


# Function to send the email
def send_email(recipient_email: str, item_dict: dict):
    sender_email: str = os.getenv('email_sender_name')
    image_data = get_image(name=item_dict['image_name'], catalog=item_dict['catalog'])
    item_name = item_dict['name']
    item_description = item_dict['description']
    item_link = item_dict['affiliate_link']
    item_image_name = item_dict['image_name']
    item_viewed = item_dict['clicked']
    
    # Create the email message
    subject = 'Hello from Python!'
    message = 'This is the body of the email.'

    msg = MIMEMultipart()
    msg['From'] = formataddr(("AIBestGoods", f"{sender_email}"))
    msg['To'] = recipient_email
    msg['Subject'] = subject
    # msg.attach(image)
    
    # Read the HTML file
    with open("./email_body.html", "r") as file:
        html_content = file.read()
    image_base64 = base64.b64encode(image_data).decode("utf-8")
    
    html_content = html_content\
                    .replace("ITEM_NAME", item_name)\
                    .replace("ITEM_LINK", item_link)\
                    .replace("IMAGE_DATA", image_base64)\
                    .replace("IMAGE_ALT", item_image_name)\
                    .replace("ITEM_DESCRIPTION", item_description)
    
    msg.attach(MIMEText(html_content, 'html'))
    
    # Setup the SMTP server
    smtp_server = 'smtp.titan.email'
    smtp_port = 587

    # Create a secure connection to the SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()

    # Login to the sender's email account
    server.login(sender_email, os.getenv("email_password"))

    # Send the email
    server.sendmail(sender_email, recipient_email, msg.as_string('email_password'))

    # Close the connection to the SMTP server
    server.quit()

    logging.info(f'Email sent successfully to {recipient_email}!')


if __name__ == '__main__':
    emails_to_send = get_subscription_list()
    item_dict = get_item("August_Home")
    
    for email in emails_to_send:
        if not item_dict['email_sent']:
            send_email(recipient_email=email, item_dict=item_dict)

    # Schedule the email to be sent every day at a specific time
    # schedule.every().day.at("11:22").do(x)
    # schedule.every(1).minutes.do(x)

    # Continuously run the scheduler
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)

