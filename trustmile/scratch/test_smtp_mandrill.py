import smtplib
from email.mime.text import MIMEText

msg = MIMEText("My email content")
msg['Subject'] = 'Hello World'

msg['From'] = 'jenkins@trustmile.com'
msg['To'] = 'rajanikanth.eltem@valuelabs.com'

# Send the message via our own SMTP server, but don't include the
# envelope header.
s = smtplib.SMTP('smtp.mandrillapp.com', 587)
s.login('james@trustmile.com', 'rhUB0_tvtJ5J9XQrALSwTg')
s.sendmail('jenkins@trustmile.com', ['rajanikanth.eltem@valuelabs.com'], msg.as_string())
s.quit()
