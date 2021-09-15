from setuptools import setup

setup(
    name='genomic_data_service',
    packages=['genomic_data_service'],
    include_package_data=True,
    install_requires=[
        'click==8.0.1',
        'Flask==1.1.2',
        'Flask-SQLAlchemy',
        'Flask-Migrate',
        'Flask-Script',
        'Flask-Excel',
        'elasticsearch==5.4.0',
        'requests',
        'pyBigWig',
        'scikit-learn==0.20.3',
        'gunicorn',
        'boto3',
        'redis',
        'celery==4.4.6',
        'flower==0.9.4',
        'snovault-search==1.0.2',
        'sqlalchemy==1.3.22',
        'psycopg2',
    ],
    extras_require={
        'test': [
            'pytest==6.2.4',
            'pytest-mock==3.6.1',
            'pytest-cov==2.12.1',
        ]
    }
)
