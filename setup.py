from setuptools import setup, find_packages

setup(
    name="llm_model_cost",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests",
    ],
    author="SukithS",
    author_email="sukith.sd2001@gmail.com",
    description="A package to calculate token costs for LLM models",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Sukith-S/llm_model_cost",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
) 
