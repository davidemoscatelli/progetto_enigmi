#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
# IMPORTANTE: Aggiungi questo import per python-dotenv
from dotenv import load_dotenv

def main():
    """Run administrative tasks."""
    # IMPORTANTE: Chiama load_dotenv() all'inizio della funzione main()
    # per caricare le variabili dal file .env
    load_dotenv(override=True)

    # Questa riga imposta le impostazioni di default (lasciala)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'enigma_project.settings')

    # Questo blocco gestisce l'import di Django (lascialo)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Questa riga esegue il comando Django (lasciala)
    execute_from_command_line(sys.argv)


# Questo blocco avvia la funzione main() (lascialo)
if __name__ == '__main__':
    main()