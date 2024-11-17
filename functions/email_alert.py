import smtplib
from email.message import EmailMessage

def sent_email(subject, body, to):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['to'] = to

    user = 'xiahuang@umass.edu'
    password = 'youn pktv vqyy mqfe'
    msg['from'] = user

    # Use SMTP_SSL instead of SMTP
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(user, password)
    server.send_message(msg)
    server.quit()
