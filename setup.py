from setuptools import setup

setup(
    name='genomic_data_service',
    packages=['genomic_data_service'],
    include_package_data=True,
    install_requires=[
        'Flask==1.1.2',
        'elasticsearch',
        'requests',
        'pyBigWig',
        'sklearn',
        'pytest',
        'gunicorn',
        'boto3',
        'redis',
        'celery==4.4.6',
        'flower',
        'sqlalchemy',
        'psycopg2',
        'boto3'
    ],
)
