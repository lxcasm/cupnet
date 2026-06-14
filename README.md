# CupNet

Application Windows de **contrôle réseau local** — scan ARP, surveillance et coupure de connexion.

**Auteur :** [lxcasm](https://github.com/lxcasm)

> Usage strictement éducatif — sur votre propre réseau, avec autorisation.

---

## Lancer CupNet

**Double-cliquez sur `CupNet.bat`** — c'est le seul fichier à utiliser.

1. Acceptez la fenêtre **UAC** (admin) pour la coupure ARP
2. Cliquez **Scanner le réseau**
3. Sélectionnez un appareil → **Couper la connexion**

**Prérequis :** Windows 10/11, Python 3.10+ (installé auto au 1er lancement), [Npcap](https://npcap.com/) pour l'ARP.

---

## Structure du projet

```
cupnet/
├── CupNet.bat          ← LANCER ICI
├── LISEZMOI.txt        ← Instructions rapides
├── README.md
├── backend/            ← Code Python (ne pas ouvrir)
└── scripts/
    └── build.bat       ← Compilation exe (optionnel, dev)
```

**Ne pas ouvrir** `backend/dist/CupNet.exe` — c'est une ancienne compilation. Utilisez toujours `CupNet.bat`.

---

## Fonctionnalités

- Scan réseau (IP, MAC, fabricant, latence, temps en ligne)
- Coupure ARP bidirectionnelle (Scapy + Npcap)
- Pare-feu local et ping flood (démonstration)
- Interface rose/violet, temps de blocage en direct

---

## Compilation exe (optionnel)

Réservé aux développeurs — **inutile pour utiliser CupNet** :

```
scripts\build.bat
```

---

## Licence

Projet éducatif — usage libre dans un cadre académique.
