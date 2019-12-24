import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="drf_dynamics",
    version="0.0.4",
    author="Ilya Bokov",
    author_email="eli.k.bokov@gmail.com",
    description="Dynamic mixins for Django REST Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/imbokov/drf_dynamics",
    packages=["drf_dynamics"],
    install_requires=["django>=1.11", "djangorestframework>=3.7.0"],
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 1.11",
        "Framework :: Django :: 2.0",
        "Framework :: Django :: 2.1",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Internet :: WWW/HTTP",
    ],
)
