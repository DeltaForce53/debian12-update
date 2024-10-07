#!/usr/bin/env python3
import subprocess
import sys
import os
import logging
import argparse
from datetime import datetime, timedelta
import shutil
import re

def clean_old_logs(log_dir, retention_days=365):
    """Nettoie les fichiers de logs plus anciens que retention_days"""
    try:
        current_time = datetime.now()
        count_deleted = 0
        
        for filename in os.listdir(log_dir):
            if filename.startswith('update_') and filename.endswith('.log'):
                file_path = os.path.join(log_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                
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
    free_gb = disk.free / (2**30)
    return free_gb >= min_space_gb

def parse_upgrade_output(output):
    """Parse la sortie de apt list --upgradable pour obtenir les paquets à mettre à jour"""
    packages = []
    for line in output.split('\n'):
        if '/' in line:  # Format typique: paquet/distribution [version]
            package = line.split('/')[0]
            packages.append(package)
    return packages

def get_upgradable_packages(logger):
    """Récupère la liste des paquets qui peuvent être mis à jour"""
    try:
        result = subprocess.run(['apt', 'list', '--upgradable'], 
                              capture_output=True, text=True, check=True)
        packages = parse_upgrade_output(result.stdout)
        return packages
    except subprocess.CalledProcessError as e:
        logger.error("Erreur lors de la récupération des paquets à mettre à jour")
        logger.error(f"Sortie d'erreur: {e.stderr}")
        return []

def parse_upgraded_packages(output):
    """Parse la sortie de apt upgrade pour identifier les paquets mis à jour"""
    upgraded = []
    for line in output.split('\n'):
        if 'Inst' in line:  # Les lignes commençant par 'Inst' indiquent les installations
            match = re.search(r'Inst\s+(\S+)', line)
            if match:
                upgraded.append(match.group(1))
    return upgraded

def run_command(command, logger, parse_output=False):
    """Exécute une commande système et log le résultat"""
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        logger.info(f"Commande réussie: {' '.join(command)}")
        
        if parse_output and 'upgrade' in command:
            upgraded_packages = parse_upgraded_packages(result.stdout)
            if upgraded_packages:
                logger.info("Paquets mis à jour:")
                for pkg in upgraded_packages:
                    logger.info(f"  - {pkg}")
            else:
                logger.info("Aucun paquet n'a été mis à jour")
                
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
    if os.geteuid() != 0:
        print("Ce script doit être exécuté avec les privilèges root (sudo).")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Script de mise à jour système")
    parser.add_argument('--no-upgrade', action='store_true', help="Exécuter uniquement apt update sans upgrade")
    parser.add_argument('--clean', action='store_true', help="Nettoyer le système après la mise à jour")
    parser.add_argument('--log-retention', type=int, default=365, 
                      help="Nombre de jours de rétention des logs (défaut: 365)")
    args = parser.parse_args()

    logger = setup_logging()
    
    try:
        if not check_disk_space():
            logger.error("Espace disque insuffisant pour la mise à jour")
            sys.exit(1)

        logger.info("Démarrage de la mise à jour du système...")
        
        # Mise à jour de la liste des paquets
        if not run_command(['apt', 'update'], logger):
            sys.exit(1)
            
        # Vérifier les paquets disponibles pour mise à jour
        upgradable_packages = get_upgradable_packages(logger)
        if upgradable_packages:
            logger.info("Paquets disponibles pour mise à jour:")
            for pkg in upgradable_packages:
                logger.info(f"  - {pkg}")
        else:
            logger.info("Aucun paquet n'est disponible pour mise à jour")

        # Mettre à niveau les paquets si --no-upgrade n'est pas spécifié
        if not args.no_upgrade:
            if upgradable_packages:
                logger.info("Démarrage de la mise à niveau des paquets...")
                if not run_command(['apt', 'upgrade', '-y'], logger, parse_output=True):
                    sys.exit(1)
            else:
                logger.info("Aucune mise à niveau nécessaire")

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