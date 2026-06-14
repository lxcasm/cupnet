# CupNet

**CupNet** est une application Windows desktop développée par **[lxcasm](https://github.com/lxcasm)** dans le cadre d'un projet de fin d'année en cybersécurité. Elle permet de **détecter les appareils** connectés à votre réseau local et de **couper leur connexion** via plusieurs méthodes.

> ⚠️ **Usage strictement éducatif** — à utiliser uniquement sur votre propre réseau, avec l'autorisation explicite de tous les utilisateurs concernés.

---

## Fonctionnalités

| Fonction | Description |
|----------|-------------|
| **Interface desktop** | Application native Windows (CustomTkinter, thème rose/violet) |
| **Scan réseau** | ARP + ping → IP, MAC, hostname, fabricant, latence |
| **Coupure ARP** | Coupure réseau bidirectionnelle via Scapy/Npcap |
| **Pare-feu local** | Bloque le trafic entre votre PC et la cible |
| **Ping Flood** | DoS léger à des fins de démonstration |
| **Surveillance** | Temps sur le réseau, latence, durée de blocage |

---

## Lancement rapide

1. Double-cliquez sur **`LANCER-CupNet.bat`** (recommandé, avec droits admin)
2. Ou **`start.bat`** pour lancer sans admin (scan uniquement)
3. Cliquez sur **« Scanner le réseau »**
4. Sélectionnez un appareil → **Couper la connexion**

**Prérequis :** Windows 10/11, Python 3.10+ (installé automatiquement via le `.bat`), [Npcap](https://npcap.com/) pour la coupure ARP.

---

## Compilation (.exe)

```powershell
# Fermez CupNet avant de compiler
build.bat
# → backend\dist\CupNet.exe
```

---

## Architecture

```
cupnet/
├── backend/
│   ├── app/
│   │   ├── gui/              # Interface graphique
│   │   ├── core/             # Logique métier
│   │   ├── scanner/          # Découverte des appareils
│   │   ├── blockers/         # Méthodes de coupure
│   │   └── models/           # Modèles de données
│   ├── main.py
│   └── requirements.txt
├── LANCER-CupNet.bat         # Lance en admin
├── start.bat                 # Lance sans admin
└── build.bat                 # Compile l'exe
```

---

## Auteur

**[lxcasm](https://github.com/lxcasm)** — projet éducatif cybersécurité.

---

## Licence

Usage libre dans un cadre académique et éducatif.
