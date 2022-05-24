from setuptools import setup, find_packages


with open('README.md') as f:
    long_description = ''.join(f.readlines())

setup(
    name='dsw_mailer',
    version='3.12.0',
    description='Worker for sending email notifications',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Marek Suchánek',
    keywords='email jinja2 notification template',
    license='Apache License 2.0',
    url='https://github.com/ds-wizard/mailer',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Topic :: Communications :: Email',
        'Topic :: Text Processing',
    ],
    zip_safe=False,
    python_requires='>=3.9, <4',
    install_requires=[
        'click',
        'jinja2',
        'pathvalidate',
        'psycopg2',
        'PyYAML',
        'tenacity',
    ],
    entry_points={
        'console_scripts': [
            'dsw-mailer=dsw_mailer:main',
        ],
    },
)
