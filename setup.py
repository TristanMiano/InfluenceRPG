from setuptools import setup, find_packages

setup(
    name="influence_rpg",
    version="0.1.0",
    description="A tabletop RPG of Influence & Strategic Command",
    author="Tristan Miano",
    packages=find_packages(where="src"),  # Look for packages under the 'src' directory
    package_dir={"": "src"},  # Tells Python that packages are under 'src'
    install_requires=[
        "fastapi",
        "psycopg2-binary",
        "pydantic",
        "requests",
        "tiktoken",
        # Add any other dependencies here
    ],
    entry_points={
        "console_scripts": [
            # Optional: Define CLI scripts if needed.
            # For example, "rpg-server=src.server.main:main"
        ],
    },
)
