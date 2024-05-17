#!/usr/bin/env python3

import subprocess
import sys

def main():
    try:
        # Mettre à jour la liste des paquets
        subprocess.check_call(['apt', 'update'])

        # Mettre à niveau les paquets installés
        subprocess.check_call(['apt', 'upgrade', '-y'])

        print('Le système a été mis à jour avec succès.')
    except subprocess.CalledProcessError as e:
        print(f'La mise à jour du système a échoué avec le code de sortie {e.returncode}.')
        sys.exit(1)

if __name__ == '__main__':
    main()
