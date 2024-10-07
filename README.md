# debian12-update
Script en Python qui met à jour un système Debian 12 et journalise les modifications. (+ ajout du crontab)

## Prérequis

- Python3 installé
- Le script doit être executable par **root**

## Arguments lors de l'exécution

```bash
python3 debian12-update.py  # Mise à jour normale
python3 debian12-update.py --clean  # Mise à jour + nettoyage
python3 debian12-update.py --no-upgrade  # Uniquement mise à jour des sources
python3 debian12-update.py  # Rétention personnalisée (180 jours)
```
## Mise en place de l'automatisation du script

Aller dans **crontab** :

```bash
crontab -e
```

Puis ajouter la ligne suivante (*tous les jours à 3h du matin*) :

```bash
0 3 * * * /usr/bin/python3 /path/to/debian12-update.py
```



