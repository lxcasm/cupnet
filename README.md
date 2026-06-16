# CupNet v2.1.1

Application Windows de **contrôle réseau local** — scan ARP, surveillance et coupure de connexion.

**Auteur :** [lxcasm](https://github.com/lxcasm)  
**Site :** [lxcasm.github.io/cupnet](https://lxcasm.github.io/cupnet)

> Usage strictement éducatif — sur votre propre réseau, avec autorisation.

---

## Lancer CupNet

**Double-cliquez sur `CupNet.bat`** — c'est tout.

1. Écran de chargement au démarrage
2. Acceptez **UAC** (admin) pour la coupure ARP
3. Si **Npcap** est absent, CupNet propose de le télécharger et l'installer
4. **Scanner le réseau** → sélectionner → **Couper la connexion**

**Prérequis :** Windows 10/11 · Python 3.10+ · [Npcap](https://npcap.com/) (proposé au lancement)

Au premier lancement, `CupNet.bat` crée le venv et installe les dépendances. Si `python` n'est pas reconnu, installez Python depuis [python.org](https://www.python.org/downloads/) (cochez **Add to PATH**) — le lanceur `py -3` est aussi supporté.

---

## Modes de coupure

| Mode | Effet |
|------|--------|
| **Coupure réseau (ARP)** | Coupe l'accès Internet/LAN de l'appareil sur le réseau (admin + Npcap) |
| **Pare-feu local (PC)** | Bloque uniquement le trafic entre **ce PC** et la cible |
| **Ping Flood** | Démo légère — ne coupe généralement pas la connexion |

---

## Nouveautés v2.1.1

- Header agrandi : boutons **Scanner** et **⚙** visibles
- Tableau à hauteur fixe (ne masque plus l'interface)
- Coupure ARP corrigée (MAC réelle + interface réseau active)
- Lanceur `CupNet.bat` : fallback `py -3` si Python Store

## Options ⚙

| Option | Description |
|--------|-------------|
| Masquer les IP | Masque IP + réseau affiché en haut |
| Agrandir le tableau | Plus d'appareils visibles |
| Temps de chargement | Splash 0–5 s |

---

## Structure

```
cupnet/
├── CupNet.bat      ← lancer ici
├── docs/           ← site web (GitHub Pages)
├── backend/        ← code source
└── scripts/        ← outils dev (optionnel)
```

---

## Licence

Projet éducatif — usage libre dans un cadre académique.
