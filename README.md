# debian12-update
Script en Python qui met à jour un système Debian 12. (+ ajout du crontab)

## Prérequis

- Python3 installé
- Le script doit être executable par **root**

## Mise en place de l'automatisation du script

Aller dans **crontab** :

```bash
crontab -e
```

Puis ajouter la ligne suivante (*tous les jours à 3h du matin*) :

```bash
0 3 * * * /usr/bin/python3 /path/to/debian12-update.py
```



