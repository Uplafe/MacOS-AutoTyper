from setuptools import setup

APP = ['auto_typer_mac.py']
OPTIONS = {
    'packages': ['pynput', 'customtkinter', 'PIL', 'rumps'],
    'includes': ['tkinter'],
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)