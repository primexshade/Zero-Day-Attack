from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="xids-framework",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="X-IDS: Explainable Deep Learning Framework for Real-Time Zero-Day Threat Detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/xids-framework",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Security",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "scikit-learn>=1.3.0",
        "torch>=2.0.0",
        "tensorflow>=2.13.0",
        "imbalanced-learn>=0.11.0",
        "shap>=0.43.0",
        "lime>=0.2.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
        "fastapi>=0.103.0",
        "pydantic>=2.3.0",
    ],
)
