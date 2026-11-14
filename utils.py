from email.mime.text import MIMEText
import email.utils
import json
import os
import smtplib
import urllib.error
import urllib.request

FROM_EMAIL = "noreply@theforgeinitiative.org"
FROM_NAME = "TFI CheckMeIn"
RESEND_URL = "https://api.resend.com/emails"


def sendEmail(toName, toEmail, subject, message, ccName="", ccEmail=""):
    apiKey = os.environ.get('RESEND_API_KEY')
    if apiKey:
        _sendResend(apiKey, toName, toEmail, subject,
                    message, ccName, ccEmail)
    else:
        _sendSMTP(toName, toEmail, subject, message, ccName, ccEmail)


def _sendResend(apiKey, toName, toEmail, subject, message, ccName, ccEmail):
    payload = {
        'from': email.utils.formataddr((FROM_NAME, FROM_EMAIL)),
        'to': [email.utils.formataddr((toName, toEmail))],
        'subject': subject,
        'text': message,
    }
    if ccEmail:
        payload['cc'] = [email.utils.formataddr((ccName, ccEmail))]

    request = urllib.request.Request(
        RESEND_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Authorization': f'Bearer {apiKey}',
                 'Content-Type': 'application/json',
                 'User-Agent': 'CheckMeIn'},
        method='POST')
    try:
        with urllib.request.urlopen(request, timeout=10):
            pass
    except urllib.error.HTTPError as e:
        print('Resend rejected email:', e.code, e.read().decode('utf-8', 'replace'))
    except OSError as e:
        print('Resend email failed:', e)


def _sendSMTP(toName, toEmail, subject, message, ccName, ccEmail):
    msg = MIMEText(message)
    msg['To'] = email.utils.formataddr((toName, toEmail))
    if ccEmail:
        msg['Cc'] = email.utils.formataddr((ccName, ccEmail))

    msg['From'] = email.utils.formataddr((FROM_NAME, FROM_EMAIL))
    msg['Subject'] = subject

    try:  # pragma: no cover
        server = smtplib.SMTP('localhost')
        server.sendmail(FROM_EMAIL, [toEmail], msg.as_string())
        server.quit()
    except IOError:
        print('Email would have been:', msg)
