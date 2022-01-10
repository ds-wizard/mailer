import yaml

from typing import List, Optional


class MissingConfigurationError(Exception):

    def __init__(self, missing: List[str]):
        self.missing = missing


class DatabaseConfig:

    def __init__(self, connection_string: str, connection_timeout: int,
                 queue_timout: int):
        self.connection_string = connection_string
        self.connection_timeout = connection_timeout
        self.queue_timout = queue_timout

    def __str__(self):
        return f'DatabaseConfig\n' \
               f'- connection_string = {self.connection_string} ' \
               f'({type(self.connection_string)})\n' \
               f'- connection_timeout = {self.connection_timeout} ' \
               f'({type(self.connection_timeout)})\n' \
               f'- queue_timout = {self.queue_timout} ({type(self.queue_timout)})\n'


class S3Config:

    def __init__(self, url: str, username: str, password: str,
                 bucket: str, region: str):
        self.url = url
        self.username = username
        self.password = password
        self.bucket = bucket
        self.region = region

    def __str__(self):
        return f'S3Config\n' \
               f'- url = {self.url} ({type(self.url)})\n' \
               f'- username = {self.username} ({type(self.username)})\n' \
               f'- password = {self.password} ({type(self.password)})\n' \
               f'- bucket = {self.bucket} ({type(self.bucket)})\n'


class LoggingConfig:

    def __init__(self, level: str, global_level: str, message_format: str):
        self.level = level
        self.global_level = global_level
        self.message_format = message_format

    def __str__(self):
        return f'LoggingConfig\n' \
               f'- level = {self.level} ({type(self.level)})\n' \
               f'- message_format = {self.message_format} ' \
               f'({type(self.message_format)})\n'


class MailConfig:

    def __init__(self, enabled: bool, ssl: Optional[bool], name: str, email: str,
                 host: str, port: Optional[int], security: Optional[str],
                 auth: Optional[bool], username: Optional[str],
                 password: Optional[str], rate_limit_window: int,
                 rate_limit_count: int):
        self.enabled = enabled
        self.name = name
        self.email = email
        self.host = host
        self.security = 'plain'
        if security is not None:
            self.security = security.lower()
        elif ssl is not None:
            self.security = 'ssl' if ssl else 'plain'
        self.port = port or self._default_port()
        self.auth = auth or (username is not None and password is not None)
        self.username = username if self.auth is not None else None
        self.password = password if self.auth is not None else None
        self.rate_limit_window = rate_limit_window
        self.rate_limit_count = rate_limit_count

    @property
    def login_user(self) -> str:
        return self.username or ''

    @property
    def login_password(self) -> str:
        return self.password or ''

    @property
    def is_plain(self):
        return self.security == 'plain'

    @property
    def is_ssl(self):
        return self.security == 'ssl'

    @property
    def is_tls(self):
        return self.security == 'starttls' or self.security == 'tls'

    def _default_port(self) -> int:
        if self.is_plain:
            return 25
        if self.is_ssl:
            return 465
        return 587

    def has_credentials(self) -> bool:
        return self.username is not None and self.password is not None


class ExperimentalConfig:

    def __init__(self, more_apps_enabled: bool):
        self.more_apps_enabled = more_apps_enabled

    def __str__(self):
        return f'ExperimentalConfig\n' \
               f'- more_apps_enabled = {self.more_apps_enabled}\n'


class MailerConfig:

    def __init__(self, db: DatabaseConfig, s3: S3Config, log: LoggingConfig,
                 mail: MailConfig, experimental: ExperimentalConfig):
        self.db = db
        self.s3 = s3
        self.log = log
        self.mail = mail
        self.experimental = experimental

    def __str__(self):
        return f'MailerConfig\n' \
               f'====================\n' \
               f'{self.db}' \
               f'{self.s3}' \
               f'{self.log}' \
               f'{self.experimental}' \
               f'====================\n'


class MailerConfigParser:

    DB_SECTION = 'database'
    S3_SECTION = 's3'
    LOGGING_SECTION = 'logging'
    EXPERIMENTAL_SECTION = 'experimental'

    DEFAULTS = {
        DB_SECTION: {
            'connectionString': 'postgresql://postgres:postgres@'
                                'postgres:5432/engine-wizard',
            'connectionTimeout': 30000,
            'queueTimeout': 120,
        },
        S3_SECTION: {
            'url': 'http://minio:9000',
            'vhost': 'minio',
            'queue': 'minio',
            'bucket': 'engine-wizard',
            'region': 'eu-central-1',
        },
        LOGGING_SECTION: {
            'level': 'INFO',
            'globalLevel': 'WARNING',
            'format': '%(asctime)s | %(levelname)8s | %(name)s: '
                      '[T:%(traceId)s] %(message)s',
        },
        EXPERIMENTAL_SECTION: {
            'moreAppsEnabled': False,
        },
        'mail': {
            'enabled': True,
            'name': '',
            'email': '',
            'host': '',
            'port': None,
            'ssl': None,
            'security': 'plain',
            'authEnabled': False,
            'username': None,
            'password': None,
            'rateLimit': {
                'window': 0,
                'count': 0,
            }
        },
    }

    REQUIRED = []  # type: list[str]

    def __init__(self):
        self.cfg = dict()

    @staticmethod
    def can_read(content):
        try:
            yaml.load(content, Loader=yaml.FullLoader)
            return True
        except Exception:
            return False

    def read_file(self, fp):
        self.cfg = yaml.load(fp, Loader=yaml.FullLoader)

    def read_string(self, content):
        self.cfg = yaml.load(content, Loader=yaml.FullLoader)

    def has(self, *path):
        x = self.cfg
        for p in path:
            if not hasattr(x, 'keys') or p not in x.keys():
                return False
            x = x[p]
        return True

    def _get_default(self, *path):
        x = self.DEFAULTS
        for p in path:
            x = x[p]
        return x

    def get_or_default(self, *path):
        x = self.cfg
        for p in path:
            if not hasattr(x, 'keys') or p not in x.keys():
                return self._get_default(*path)
            x = x[p]
        return x

    def validate(self):
        missing = []
        for path in self.REQUIRED:
            if not self.has(*path):
                missing.append('.'.join(path))
        if len(missing) > 0:
            raise MissingConfigurationError(missing)

    @property
    def db(self) -> DatabaseConfig:
        return DatabaseConfig(
            connection_string=self.get_or_default(
                self.DB_SECTION, 'connectionString'
            ),
            connection_timeout=self.get_or_default(
                self.DB_SECTION, 'connectionTimeout'
            ),
            queue_timout=self.get_or_default(
                self.DB_SECTION, 'queueTimeout'
            ),
        )

    @property
    def s3(self) -> S3Config:
        return S3Config(
            url=self.get_or_default(self.S3_SECTION, 'url'),
            username=self.get_or_default(self.S3_SECTION, 'username'),
            password=self.get_or_default(self.S3_SECTION, 'password'),
            bucket=self.get_or_default(self.S3_SECTION, 'bucket'),
            region=self.get_or_default(self.S3_SECTION, 'region'),
        )

    @property
    def logging(self) -> LoggingConfig:
        return LoggingConfig(
            level=self.get_or_default(self.LOGGING_SECTION, 'level'),
            global_level=self.get_or_default(self.LOGGING_SECTION, 'globalLevel'),
            message_format=self.get_or_default(self.LOGGING_SECTION, 'format'),
        )

    @property
    def experimental(self) -> ExperimentalConfig:
        return ExperimentalConfig(
            more_apps_enabled=self.get_or_default(
                self.EXPERIMENTAL_SECTION, 'moreAppsEnabled'
            ),
        )

    @property
    def mail(self):
        return MailConfig(
            enabled=self.get_or_default('mail', 'enabled'),
            name=self.get_or_default('mail', 'name'),
            email=self.get_or_default('mail', 'email'),
            host=self.get_or_default('mail', 'host'),
            ssl=self.get_or_default('mail', 'ssl'),
            port=self.get_or_default('mail', 'port'),
            security=self.get_or_default('mail', 'security'),
            auth=self.get_or_default('mail', 'authEnabled'),
            username=self.get_or_default('mail', 'username'),
            password=self.get_or_default('mail', 'password'),
            rate_limit_window=self.get_or_default('mail', 'rateLimit', 'window'),
            rate_limit_count=self.get_or_default('mail', 'rateLimit', 'count'),
        )

    @property
    def config(self) -> MailerConfig:
        return MailerConfig(
            db=self.db,
            s3=self.s3,
            log=self.logging,
            mail=self.mail,
            experimental=self.experimental,
        )
