import smtplib
from email.message import EmailMessage

def send_email(subject, body, to):

    if isinstance(to, list):
        to = ", ".join(to)

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

def notify_user(job_ids, recipient_email, method="email",):
    if method == "email":
        if not isinstance(recipient_email, list):
            recipient_email = [recipient_email]
        send_email("Jobs Completed", f"All jobs {job_ids} have completed.",recipient_email)
    elif method == "app":
        return f"Notification: All jobs {job_ids} have completed."
    else:
        print(f"All jobs {job_ids} have completed.")

notify_user("123, 456", ["xia.summer.huang@gmail.com",'xiaoxiami516@gmail.com'], method="email")