# EDIGEO Qgis processing plugin


# Ce plugin nécessite l'installation du module python [edigeo](https://github.com/3liz/edigeo)

## Installer le module edigeo:
    
* Aller sur https://github.com/3liz/edigeo/actions
* Selectionner le dernier run ('CI' pour Linux, "Windows build" pour Windows)
* Récuperer les fichiers wheel dans les artifacts (`wheels-linux-x86_64.zip`)
* Désarchiver le fichiers
* Installer le wheel  correnspondance à la version python de QGIS 
  dans un repertoire de votre choix - note: un fichier wheel est fichier zip, il suffit 
  de désarchiver le fichier `.whl` dans le repertoire choisi.

Dans QGIS: 

* Créer un profile, et ajouter une variable PYTHONPATH  vers le réprtoire
  ou est installé le module.


