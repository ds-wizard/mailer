from typing import Optional


class TemplateDescriptorPart:

    def __init__(self, part_type: str, template: str):
        self.type = part_type
        self.template = template

    @staticmethod
    def load_from_file(data: dict) -> 'TemplateDescriptorPart':
        return TemplateDescriptorPart(
            part_type=data.get('type', 'unknown'),
            template=data.get('template', ''),
        )


class TemplateDescriptor:

    def __init__(self, message_id: str, subject: str):
        self.id = message_id
        self.subject = subject
        self.parts = []  # type: list[TemplateDescriptorPart]
        self.modes = []  # type: list[str]

    @staticmethod
    def load_from_file(data: dict) -> 'TemplateDescriptor':
        result = TemplateDescriptor(
            message_id=data.get('id', ''),
            subject=data.get('subject', ''),
        )
        result.parts = [TemplateDescriptorPart.load_from_file(d)
                        for d in data.get('parts', [])]
        result.modes = data.get('modes', [])
        return result


class MessageRequest:

    def __init__(self, message_id: str, template_name: str, trigger: str,
                 ctx: dict, recipients: list[str]):
        self.id = message_id
        self.template_name = template_name
        self.trigger = trigger
        self.ctx = ctx
        self.recipients = recipients

    @staticmethod
    def load_from_file(data: dict) -> 'MessageRequest':
        return MessageRequest(
            message_id=data['id'],
            template_name=data['type'],
            trigger=data.get('trigger', 'input_file'),
            ctx=data.get('ctx', {}),
            recipients=data.get('recipients', []),
        )


class MailMessage:
    # TODO: images, attachments

    def __init__(self):
        self.from_mail = ''
        self.from_name = ''
        self.recipients = list()
        self.subject = ''
        self.plain_body = None  # type: Optional[str]
        self.html_body = None  # type: Optional[str]
        self.images = list()
