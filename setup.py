from setuptools import setup

setup(
    name="genomic_data_service",
    packages=["genomic_data_service"],
    include_package_data=True,
    install_requires=[
        'itsdangerous==2.0.1',
        'click==8.0.1',
        'Werkzeug==2.0.1',
        'Flask==2.0.1',
        'Flask-SQLAlchemy==2.5.1',
        'Flask-Migrate==3.1.0',
        'Flask-Script==2.0.6',
        'Flask-Excel==0.0.7',
        'elasticsearch==5.4.0',
        'requests==2.27.1',
        'pyBigWig==0.3.18',
        'scikit-learn==1.0.1',
        'gunicorn==20.1.0',
        'boto3==1.20.46',
        'redis==4.1.2',
        'celery==4.4.6',
        'flower==0.9.4',
        'snovault-search==1.0.5',
        'sqlalchemy==1.3.22',
        'psycopg2==2.9.3',
    ],
    extras_require={
        "test": [
            "pytest==6.2.4",
            "pytest-mock==3.6.1",
            "pytest-cov==2.12.1",
        ]
    },
)
