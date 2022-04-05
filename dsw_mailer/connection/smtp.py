import logging
import tenacity
import smtplib
import ssl

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from ..config import MailConfig
from ..context import Context
from ..model import MailMessage


RETRY_SMTP_MULTIPLIER = 0.5
RETRY_SMTP_TRIES = 3
EMAIL_ENCODING = 'utf-8'


class SMTPSender:

    def __init__(self, cfg: MailConfig):
        self.cfg = cfg
        self.timeout = 5

    @tenacity.retry(
        reraise=True,
        wait=tenacity.wait_exponential(multiplier=RETRY_SMTP_MULTIPLIER),
        stop=tenacity.stop_after_attempt(RETRY_SMTP_TRIES),
        before=tenacity.before_log(Context.logger, logging.DEBUG),
        after=tenacity.after_log(Context.logger, logging.DEBUG),
    )
    def send(self, message: MailMessage):
        self._send(message)

    def _send(self, mail: MailMessage):
        if self.cfg.is_ssl:
            return self._send_smtp_ssl(mail=mail)
        return self._send_smtp(mail=mail)

    def _send_smtp_ssl(self, mail: MailMessage):
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            host=self.cfg.host,
            port=self.cfg.port,
            context=context,
            timeout=self.timeout,
        ) as server:
            if self.cfg.auth:
                server.login(
                    user=self.cfg.login_user,
                    password=self.cfg.login_password,
                )
            return server.send_message(
                msg=self._convert_email(mail),
                from_addr=formataddr((mail.from_name, mail.from_mail)),
                to_addrs=mail.recipients,
            )

    def _send_smtp(self, mail: MailMessage):
        context = ssl.create_default_context()
        with smtplib.SMTP(
            host=self.cfg.host,
            port=self.cfg.port,
            timeout=self.timeout,
        ) as server:
            if self.cfg.is_tls:
                server.starttls(context=context)
            if self.cfg.auth:
                server.login(
                    user=self.cfg.login_user,
                    password=self.cfg.login_password,
                )
            return server.send_message(
                msg=self._convert_email(mail),
                from_addr=formataddr((mail.from_name, mail.from_mail)),
                to_addrs=mail.recipients,
            )

    def _convert_email(self, mail: MailMessage) -> MIMEMultipart:
        msg = MIMEMultipart('alternative')
        msg.set_charset(EMAIL_ENCODING)
        msg['From'] = formataddr((mail.from_name, mail.from_mail))
        msg['To'] = ', '.join(mail.recipients)
        msg['Subject'] = mail.subject
        if mail.plain_body is not None:
            msg.attach(MIMEText(mail.plain_body, 'plain', EMAIL_ENCODING))
        if mail.html_body is not None:
            msg.attach(MIMEText(mail.html_body, 'html', EMAIL_ENCODING))
        # TODO: attachments / related
        return msg
