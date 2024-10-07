#!/usr/bin/env python3
import subprocess
import sys
import os
import logging
import argparse
from datetime import datetime, timedelta
import shutil

def clean_old_logs(log_dir, retention_days=365):
    """Nettoie les fichiers de logs plus anciens que retention_days"""
    try:
        current_time = datetime.now()
        count_deleted = 0
        
        # Parcourir tous les fichiers de log
        for filename in os.listdir(log_dir):
            if filename.startswith('update_') and filename.endswith('.log'):
                file_path = os.path.join(log_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                
                # Supprimer si plus vieux que retention_days
                if (current_time - file_time) > timedelta(days=retention_days):
                    os.remove(file_path)
                    count_deleted += 1
                    
        return count_deleted
    except Exception as e:
        logging.error(f"Erreur lors du nettoyage des vieux logs: {str(e)}")
        return 0

def setup_logging():
    """Configure le système de logging avec rétention"""
    log_dir = '/var/log/system-update'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Nettoyer les vieux logs
    deleted_count = clean_old_logs(log_dir)
    
    log_file = os.path.join(log_dir, f'update_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    if deleted_count > 0:
        logger.info(f"Nettoyage des logs: {deleted_count} fichiers supprimés")
    
    return logger

def check_disk_space(min_space_gb=1):
    """Vérifie l'espace disque disponible"""
    disk = shutil.disk_usage("/")
    free_gb = disk.free / (2**30)  # Convertit en GB
    return free_gb >= min_space_gb

def run_command(command, logger):
    """Exécute une commande système et log le résultat"""
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        logger.info(f"Commande réussie: {' '.join(command)}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de l'exécution de {' '.join(command)}")
        logger.error(f"Code de sortie: {e.returncode}")
        logger.error(f"Sortie d'erreur: {e.stderr}")
        return False

def clean_system(logger):
    """Nettoie les paquets et caches inutiles"""
    commands = [
        ['apt', 'autoremove', '-y'],
        ['apt', 'clean'],
        ['apt', 'autoclean']
    ]
    
    for cmd in commands:
        if not run_command(cmd, logger):
            return False
    return True

def main():
    # Vérifier les privilèges root
    if os.geteuid() != 0:
        print("Ce script doit être exécuté avec les privilèges root (sudo).")
        sys.exit(1)

    # Configurer l'analyseur d'arguments
    parser = argparse.ArgumentParser(description="Script de mise à jour système")
    parser.add_argument('--no-upgrade', action='store_true', help="Exécuter uniquement apt update sans upgrade")
    parser.add_argument('--clean', action='store_true', help="Nettoyer le système après la mise à jour")
    parser.add_argument('--log-retention', type=int, default=365, 
                      help="Nombre de jours de rétention des logs (défaut: 365)")
    args = parser.parse_args()

    # Initialiser le logging avec la rétention spécifiée
    logger = setup_logging()
    
    try:
        # Vérifier l'espace disque
        if not check_disk_space():
            logger.error("Espace disque insuffisant pour la mise à jour")
            sys.exit(1)

        # Mettre à jour la liste des paquets
        logger.info("Démarrage de la mise à jour du système...")
        if not run_command(['apt', 'update'], logger):
            sys.exit(1)

        # Mettre à niveau les paquets si --no-upgrade n'est pas spécifié
        if not args.no_upgrade:
            if not run_command(['apt', 'upgrade', '-y'], logger):
                sys.exit(1)

        # Nettoyer le système si --clean est spécifié
        if args.clean:
            logger.info("Nettoyage du système...")
            if not clean_system(logger):
                sys.exit(1)

        logger.info('Mise à jour du système terminée avec succès.')

    except Exception as e:
        logger.error(f'Une erreur inattendue est survenue: {str(e)}')
        sys.exit(1)

if __name__ == '__main__':
    main()