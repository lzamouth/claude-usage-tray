# claude-usage-tray

[English](README.md) · **Français**

Indicateur systray Linux (GNOME / KDE) affichant l'utilisation de ton
abonnement claude.ai :

- le label de l'icône indique l'utilisation de la **session de 5 h** ;
- le menu affiche l'utilisation sur **7 jours**, les limites hebdomadaires
  par modèle renvoyées par l'API (ex. Fable, Opus, Sonnet), et l'heure de
  réinitialisation de chaque fenêtre ;
- chaque valeur est aussi convertie en durée (heures pour la fenêtre de
  5 h, jours pour les fenêtres hebdomadaires), à côté du temps écoulé depuis
  le dernier reset, pour voir d'un coup d'œil si tu consommes plus vite ou
  moins vite que le temps : `7 jours : 16% (1,1 j / 1,3 j écoulés)` ;
- l'icône reflète la **pire de toutes les fenêtres** (5 h, 7 jours, par
  modèle) : avertissement à 75 %, erreur à 90 %, et avertissement aussi
  quand tu consommes **plus vite que le temps** — au moins 25 % utilisés et
  10 points de plus que la part de la fenêtre déjà écoulée. Les lignes en
  cause sont marquées d'un ⚠ ;
- le menu indique l'heure de la dernière mise à jour ; après une erreur, les
  chiffres restent affichés mais grisés, pour ne jamais confondre des
  données périmées avec des données actuelles.

L'interface est disponible en **français, anglais, allemand, espagnol,
italien, néerlandais et portugais** (voir [Langue](#langue)).

> [!WARNING]
> Cet outil repose sur l'**API interne non documentée** qu'appelle le site
> claude.ai lui-même. Elle peut changer ou être bloquée sans préavis. C'est
> un projet non officiel, sans lien avec Anthropic ni approuvé par Anthropic.

## Fonctionnement

- **Aucun secret stocké.** L'applet lit le cookie `sessionKey` que Firefox
  possède déjà après une connexion normale à claude.ai, directement dans le
  `cookies.sqlite` du profil (copié en répertoire temporaire, car Firefox le
  verrouille). Seul le conteneur par défaut est utilisé ; les cookies expirés
  sont ignorés. Firefox installé en .deb, en snap (le défaut d'Ubuntu) ou en
  Flatpak est pris en charge ; s'il y en a plusieurs, le plus récemment
  utilisé l'emporte.
- Toutes les 5 minutes (configurable), elle appelle :
  - `GET https://claude.ai/api/organizations`
  - `GET https://claude.ai/api/organizations/{id}/usage`
- Elle rafraîchit immédiatement à la sortie de veille et au retour du
  réseau.
- En cas d'échecs répétés côté serveur, l'intervalle double (jusqu'à 1 h)
  au lieu de marteler le serveur ; il revient à la normale dès le premier
  succès. Les coupures réseau ne déclenchent pas ce ralentissement.

## Prérequis

- Linux avec **Firefox**, connecté à claude.ai.
- Python ≥ 3.11, GTK 3 et une bibliothèque AppIndicator :

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1
```

- **GNOME** n'affiche pas les icônes systray par défaut. Installe et active
  l'extension *AppIndicator and KStatusNotifierItem Support*, puis
  reconnecte-toi :

```bash
sudo apt install gnome-shell-extension-appindicator
```

- **KDE Plasma** affiche nativement les icônes StatusNotifierItem.

## Installation

```bash
git clone https://github.com/lzamouth/claude-usage-tray.git
cd claude-usage-tray
./install.sh
```

`install.sh` crée un virtualenv (avec `--system-site-packages`, car
`python3-gi` vient de la distribution) et ajoute une entrée de démarrage
automatique. `./install.sh --systemd` installe plutôt un service systemd
utilisateur (relancé en cas de plantage), `--no-start` se contente du
virtualenv.

Lancement au premier plan (pratique pour déboguer) :

```bash
./.venv/bin/python -m claude_usage_tray
```

## Configuration

Créée au premier lancement dans `~/.config/claude-usage-tray/config.toml` :

```toml
poll_interval_seconds = 300   # intervalle de rafraîchissement
firefox_profile = ""          # vide = profil Firefox par défaut
language = ""                 # "en", "fr", "de", "es", "it", "nl", "pt", ou vide = langue du système
```

### Langue

Avec `language = ""`, la langue suit les variables de locale habituelles
(`LANGUAGE`, `LC_ALL`, `LC_MESSAGES`, `LANG`) ; une langue non prise en charge
retombe sur l'anglais. Le portugais suit l'usage brésilien et sert aussi pour
`pt_PT`. Les traductions allemande, espagnole, italienne, néerlandaise et
portugaise ont été écrites par Claude et n'ont pas encore été relues par des locuteurs natifs :
les corrections sont bienvenues.

Pour ajouter une langue : créer `claude_usage_tray/locales/<code>.py` (en
copiant `fr.py`), ajouter le code à `SUPPORTED_LANGUAGES` dans
`claude_usage_tray/i18n.py`, puis lancer les tests — ils échouent si une
chaîne manque ou si un placeholder diffère.

## Dépannage

Commence par le script de diagnostic : il affiche les cookies trouvés, une
requête sans en-têtes de navigateur et une requête faite exactement comme
l'applet :

```bash
./.venv/bin/python diag_usage.py
```

| Message du menu | Signification |
|---|---|
| *Cookie sessionKey introuvable* | Pas connecté à claude.ai dans Firefox, ou mauvais profil (`firefox_profile`). |
| *Cookie expiré* / *Session refusée* | Reconnecte-toi ; l'entrée **Se reconnecter à Claude…** ouvre Firefox et interroge rapidement jusqu'à ce que ça passe. |
| *Requête bloquée par Cloudflare* | Challenge anti-bot, sans rapport avec ta session : se reconnecter n'y changera rien. L'applet espace automatiquement ses requêtes. |
| Icône absente sous GNOME | L'extension AppIndicator n'est pas installée ou pas activée. |

## Développement

```bash
./.venv/bin/python -m unittest discover -s tests -t .
```

Voir [CLAUDE.md](CLAUDE.md) pour l'architecture et les conventions de code.

## Auteur

Le code de ce projet a été écrit par **Claude**, le modèle d'IA d'Anthropic,
dans [Claude Code](https://claude.com/claude-code), à la demande de
[@lzamouth](https://github.com/lzamouth), qui le publie.

## Licence

[MIT](LICENSE)
