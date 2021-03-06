from setuptools import setup

setup(
    name='genomic_data_service',
    packages=['genomic_data_service'],
    include_package_data=True,
    install_requires=[
        'Flask==1.1.2',
        'Flask-SQLAlchemy',
        'Flask-Migrate',
        'Flask-Script',
        'Flask-Excel',
        'elasticsearch',
        'requests',
        'pyBigWig',
        'scikit-learn==0.20.3',
        'pytest',
        'gunicorn',
        'boto3',
        'redis',
        'celery==4.4.6',
        'flower==0.9.4',
        'sqlalchemy==1.3.22',
        'psycopg2',
        'boto3'
    ],
    tests_require=['pytest']
)
