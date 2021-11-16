from setuptools import setup

setup(
    name='genomic_data_service',
    packages=['genomic_data_service'],
    include_package_data=True,
    install_requires=[
        'click==8.0.1',
        'Werkzeug==2.0.1',
        'Flask==1.1.2',
        'elasticsearch==5.4.0',
        'requests',
        'gunicorn',
        'boto3',
        'snovault-search==1.0.2',
    ],
    extras_require={
        'test': [
            'pytest==6.2.4',
            'pytest-mock==3.6.1',
            'pytest-cov==2.12.1',
        ]
    }
)
