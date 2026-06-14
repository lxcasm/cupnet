# CupNet v2.1

Application Windows de **contrôle réseau local** — scan ARP, surveillance et coupure de connexion.

**Auteur :** [lxcasm](https://github.com/lxcasm)

> Usage strictement éducatif — sur votre propre réseau, avec autorisation.

---

## Lancer CupNet

**Double-cliquez sur `CupNet.bat`**

1. Écran de chargement au démarrage
2. Acceptez **UAC** (admin) pour la coupure ARP
3. **Scanner le réseau** → sélectionner → **Couper la connexion**

---

## Options (bouton ⚙)

| Option | Description |
|--------|-------------|
| **Masquer les IP** | Affiche `192.***.***.***` dans le tableau |
| **Agrandir le tableau** | Cache le bas de page pour plus d'appareils visibles |
| **Temps de chargement** | Durée du splash au démarrage (0–5 s) |

---

## Prérequis

Windows 10/11 · Python 3.10+ (auto) · [Npcap](https://npcap.com/) pour l'ARP

---

## Structure

```
cupnet/
├── CupNet.bat       ← lancer ici
├── LISEZMOI.txt
├── backend/         ← code source
└── scripts/         ← outils dev
```

---

## Licence

Projet éducatif — usage libre dans un cadre académique.
