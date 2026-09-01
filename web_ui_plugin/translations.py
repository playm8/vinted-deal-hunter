"""
Translations for the web interface.

English strings are used as keys, so a template reads as plain English and a
missing translation falls back to it instead of showing an identifier.
"""

import db

DEFAULT_LANGUAGE = "en"

LANGUAGES = {"en": "English", "fr": "Français"}

TRANSLATIONS = {
    "fr": {
        # Navigation and layout
        "Dashboard": "Tableau de bord",
        "Queries": "Recherches",
        "Items": "Articles",
        "Allowlist": "Liste de pays",
        "Configuration": "Configuration",
        "Logs": "Journaux",
        "Report an issue": "Signaler un problème",
        "Documentation": "Documentation",
        "Up to date": "À jour",
        "Toggle navigation": "Afficher la navigation",
        "Close": "Fermer",
        "Cancel": "Annuler",
        "Actions": "Actions",
        "Remove": "Supprimer",
        "Add": "Ajouter",
        "Edit": "Modifier",
        "View": "Voir",
        "Name": "Nom",
        "Start": "Démarrer",
        "Stop": "Arrêter",
        # Allowlist
        "Country Allowlist": "Liste de pays autorisés",
        "Add Country": "Ajouter un pays",
        "Country Code (2 letters)": "Code pays (2 lettres)",
        "Enter a 2-letter country code (e.g., FR for France, DE for Germany)":
            "Saisissez un code pays à 2 lettres (par exemple FR pour la France, DE pour l'Allemagne)",
        "Current Allowlist": "Liste actuelle",
        "Country Code": "Code pays",
        "Clear Allowlist": "Vider la liste",
        "Confirm Clearing Allowlist": "Confirmer le vidage de la liste",
        "Are you sure you want to clear the entire allowlist? This will allow items from all countries.":
            "Voulez-vous vraiment vider toute la liste ? Les articles de tous les pays seront acceptés.",
        "No countries in the allowlist. Items from all countries will be shown.":
            "Aucun pays dans la liste. Les articles de tous les pays seront affichés.",
        "About Country Allowlist": "À propos de la liste de pays",
        "The country allowlist allows you to filter items based on the seller's country. Only items from sellers in the allowed countries will be shown.":
            "La liste de pays permet de filtrer les articles selon le pays du vendeur. Seuls les articles des vendeurs situés dans les pays autorisés seront affichés.",
        "If the allowlist is empty, items from all countries will be shown.":
            "Si la liste est vide, les articles de tous les pays seront affichés.",
        "Country codes are 2-letter ISO codes, such as:":
            "Les codes pays sont des codes ISO à 2 lettres, par exemple :",
        "- France": "— France",
        "- Germany": "— Allemagne",
        "- Spain": "— Espagne",
        "- Italy": "— Italie",
        "- United Kingdom": "— Royaume-Uni",
        # Configuration
        "Application Settings": "Paramètres de l'application",
        "System Settings": "Paramètres système",
        "Items Per Query": "Articles par recherche",
        "Maximum number of items to fetch per query":
            "Nombre maximum d'articles à récupérer par recherche",
        "Query Refresh Delay (seconds)": "Délai de rafraîchissement (secondes)",
        "Delay between query refreshes in seconds":
            "Délai entre deux rafraîchissements, en secondes",
        "Banwords": "Mots exclus",
        "Maximum Item Age (minutes)": "Âge maximum des articles (minutes)",
        "Adapt the age window automatically": "Adapter automatiquement la fenêtre d'âge",
        "Follows the indexing delay measured on Vinted, using the value above as a floor.":
            "Suit le délai d'indexation mesuré sur Vinted, en utilisant la valeur ci-dessus comme plancher.",
        "Currently": "Actuellement",
        "Age Window Cap (minutes)": "Plafond de la fenêtre d'âge (minutes)",
        "Upper bound the automatic window will never exceed":
            "Limite haute que la fenêtre automatique ne dépassera jamais",
        "Ignore items older than this. Vinted publishes an item in its search results long after the timestamp it carries, so a window under two hours can drop every item.":
            "Ignorer les articles plus anciens que cette durée. Vinted publie un article dans ses résultats de recherche bien après l'horodatage qu'il porte : une fenêtre inférieure à deux heures peut écarter tous les articles.",
        "Words to filter out from item titles. Items with these words in their titles will be ignored.":
            "Mots à exclure des titres d'articles. Les articles contenant ces mots seront ignorés.",
        "Enter a word to ban": "Saisissez un mot à exclure",
        # Deal detection
        "This interface is not password protected.": "Cette interface n'est pas protégée par mot de passe.",
        "Anyone who can reach it can read and change your settings. Set WEB_UI_PASSWORD in the environment to require a password.":
            "Toute personne pouvant y accéder peut lire et modifier vos réglages. Définissez WEB_UI_PASSWORD dans l'environnement pour exiger un mot de passe.",
        "Monitoring": "Surveillance",
        "Alert when nothing is kept": "Alerter quand plus rien n'est retenu",
        "Warns you when searches return results but every item is discarded, the signature of a silent breakdown.":
            "Vous avertit quand les recherches renvoient des résultats mais que tous les articles sont écartés, la signature d'une panne silencieuse.",
        "Cycles Before Alerting": "Cycles avant alerte",
        "Empty cycles to tolerate before warning": "Cycles à vide tolérés avant l'avertissement",
        "Send a daily summary": "Envoyer un résumé quotidien",
        "One message a day with what was found, notified and skipped.":
            "Un message par jour indiquant ce qui a été trouvé, notifié et ignoré.",
        "Summary Hour": "Heure du résumé",
        "Hour of the day, server time": "Heure de la journée, heure du serveur",
        "Deal Detection": "Détection de bonnes affaires",
        "Enable market price reference": "Activer le prix de référence du marché",
        "Compares each new item with the median price of similar Vinted listings to score the deal. Costs one extra request per new item (cached).":
            "Compare chaque nouvel article au prix médian des annonces Vinted similaires pour évaluer l'affaire. Coûte une requête supplémentaire par article (mise en cache).",
        "Sample Size": "Taille de l'échantillon",
        "Listings fetched per comparison": "Annonces récupérées par comparaison",
        "Minimum Samples": "Échantillon minimum",
        "Below this, no reference is shown": "En dessous, aucune référence n'est affichée",
        "Cache TTL (hours)": "Durée du cache (heures)",
        "How long a reference price is reused": "Durée de réutilisation d'un prix de référence",
        "Good / Hot Deal (%)": "Bonne / excellente affaire (%)",
        "Discount thresholds below market": "Seuils de remise sous le prix du marché",
        "Maximum Price Spread (%)": "Dispersion maximale des prix (%)",
        "Above this spread the comparable listings describe different products, so no verdict is announced. Leave empty to always announce one.":
            "Au-delà de cette dispersion, les annonces comparables décrivent des produits différents et aucun verdict n'est annoncé. Laissez vide pour toujours en annoncer un.",
        "Silent Below (%)": "Silencieux en dessous de (%)",
        "Items discounted less than this arrive without a sound. Leave empty to make every notification audible.":
            "Les articles moins remisés que ce seuil arrivent sans son. Laissez vide pour que toutes les notifications soient sonores.",
        "Skip Below (%)": "Ignorer en dessous de (%)",
        "Items discounted less than this are not notified at all. Leave empty to notify everything. Use 0 to drop anything above market.":
            "Les articles moins remisés que ce seuil ne sont pas notifiés du tout. Laissez vide pour tout notifier. Mettez 0 pour écarter tout ce qui dépasse le prix du marché.",
        # Telegram / RSS / proxies
        "Telegram Bot": "Bot Telegram",
        "Auto Start": "Démarrage automatique",
        "Bot Token": "Jeton du bot",
        "Get this from BotFather": "À récupérer auprès de BotFather",
        "Set by the environment; edit it there.": "Défini par l'environnement ; modifiez-le à cet endroit.",
        "A value is set. Leave empty to keep it, or type - to clear it.":
            "Une valeur est enregistrée. Laissez vide pour la conserver, ou saisissez - pour l'effacer.",
        "Chat ID": "Identifiant de conversation",
        "The chat ID where notifications will be sent":
            "L'identifiant de la conversation où les notifications seront envoyées",
        "RSS Feed": "Flux RSS",
        "Port": "Port",
        "The port on which the RSS feed will be served":
            "Le port sur lequel le flux RSS sera servi",
        "Maximum Items": "Articles maximum",
        "Maximum number of items to keep in the RSS feed":
            "Nombre maximum d'articles à conserver dans le flux RSS",
        "Proxy Settings": "Paramètres des proxys",
        "Check Proxies": "Vérifier les proxys",
        "Verify if proxies are working before using them":
            "Vérifier que les proxys fonctionnent avant de les utiliser",
        "Proxy List": "Liste de proxys",
        "List of proxies separated by semicolons (;)":
            "Liste de proxys séparés par des points-virgules (;)",
        "Format: http://ip:port or ip:port": "Format : http://ip:port ou ip:port",
        "Proxy List Link": "Lien vers une liste de proxys",
        "URL to fetch proxies from (one proxy per line)":
            "URL depuis laquelle récupérer les proxys (un par ligne)",
        # Advanced
        "Advanced Settings": "Paramètres avancés",
        "Notification Message Template": "Modèle de message de notification",
        "User Agents": "Agents utilisateur",
        "List of user agents for HTTP requests (JSON format)":
            "Liste d'agents utilisateur pour les requêtes HTTP (format JSON)",
        "Default Headers": "En-têtes par défaut",
        "Default headers for HTTP requests (JSON format)":
            "En-têtes par défaut pour les requêtes HTTP (format JSON)",
        "Save Configuration": "Enregistrer la configuration",
        "Language": "Langue",
        "Interface language": "Langue de l'interface",
        # Dashboard
        "Process Control": "Contrôle des processus",
        "Checking status...": "Vérification de l'état...",
        "Total Items": "Articles au total",
        "Items grabbed for monitored queries so far":
            "Articles récupérés jusqu'ici pour les recherches surveillées",
        "Active Queries": "Recherches actives",
        "Queries being monitored": "Recherches actuellement surveillées",
        "Items per Day": "Articles par jour",
        "Average items found daily": "Moyenne d'articles trouvés par jour",
        "Last Found Item": "Dernier article trouvé",
        "No items found yet": "Aucun article trouvé pour l'instant",
        "Process Status": "État des processus",
        "Recent Items": "Articles récents",
        "Price Trends": "Tendances de prix",
        "no category": "sans catégorie",
        "Add a category to this Vinted search to get more reliable price references":
            "Ajoutez une catégorie à cette recherche Vinted pour obtenir des références de prix plus fiables",
        "Last 30 days": "30 derniers jours",
        "Brand": "Marque",
        "References": "Références",
        "Average median": "Médiane moyenne",
        "Lowest": "Plus bas",
        "Highest": "Plus haut",
        "No price references recorded yet. They build up as new items are found.":
            "Aucune référence de prix enregistrée pour l'instant. Elles s'accumulent au fil des articles trouvés.",
        "Cards": "Cartes",
        "List": "Liste",
        "View All": "Tout voir",
        # Items
        "No items found": "Aucun article trouvé",
        "Image": "Image",
        "Title": "Titre",
        "Price": "Prix",
        "Timestamp": "Horodatage",
        "Manage": "Gérer",
        "Query": "Recherche",
        "No queries found": "Aucune recherche trouvée",
        "View toggle": "Changer d'affichage",
        "Filter Items": "Filtrer les articles",
        "Search by Query": "Filtrer par recherche",
        "All Queries": "Toutes les recherches",
        "Number of Items": "Nombre d'articles",
        "10 items": "10 articles",
        "25 items": "25 articles",
        "50 items": "50 articles",
        "100 items": "100 articles",
        "Apply Filter": "Appliquer le filtre",
        "View on Vinted": "Voir sur Vinted",
        "Date": "Date",
        # Logs
        "Refresh Now": "Rafraîchir maintenant",
        "Auto-Refresh: ON": "Rafraîchissement auto : activé",
        "Log Level": "Niveau de journal",
        "All Levels": "Tous les niveaux",
        "Debug": "Débogage",
        "Info": "Information",
        "Warning": "Avertissement",
        "Error": "Erreur",
        "Critical": "Critique",
        "Log Entries": "Entrées de journal",
        "0 entries": "0 entrée",
        "Level": "Niveau",
        "Module": "Module",
        "Message": "Message",
        "Loading logs...": "Chargement des journaux...",
        "Log file: logs/vinted.log": "Fichier de journal : logs/vinted.log",
        "Load More": "Charger plus",
        # Queries
        "Add New Query": "Ajouter une recherche",
        "Vinted search URL": "URL de recherche Vinted",
        "Paste a valid Vinted search URL (e.g.&nbsp;`https://www.vinted.fr/catalog?...`)":
            "Collez une URL de recherche Vinted valide (par exemple&nbsp;`https://www.vinted.fr/catalog?...`)",
        "Name&nbsp;": "Nom&nbsp;",
        "(optional)": "(facultatif)",
        "Add Query": "Ajouter la recherche",
        "Current Queries": "Recherches actuelles",
        "View Items": "Voir les articles",
        "Edit Query": "Modifier la recherche",
        "Save Changes": "Enregistrer les modifications",
        "Confirm Deletion": "Confirmer la suppression",
        "Are you sure you want to remove the query:":
            "Voulez-vous vraiment supprimer la recherche :",
        "Remove All Queries": "Supprimer toutes les recherches",
        "Are you sure you want to remove": "Voulez-vous vraiment supprimer",
        "queries? This action cannot be undone.":
            "recherches ? Cette action est irréversible.",
        "Remove All": "Tout supprimer",
        "My search": "Ma recherche",
        # Flash messages
        "Configuration updated": "Configuration mise à jour",
        "Query added": "Recherche ajoutée",
        "No query provided": "Aucune recherche fournie",
        "Query removed": "Recherche supprimée",
        "All queries removed": "Toutes les recherches ont été supprimées",
        "Query updated": "Recherche mise à jour",
        "No country provided": "Aucun pays fourni",
        "Allowlist cleared": "Liste de pays vidée",
        # Dynamic strings rendered by the page scripts
        "Running": "En marche",
        "Stopped": "Arrêté",
        "Unknown": "Inconnu",
        "Running on port": "En marche sur le port",
        "No log entries found": "Aucune entrée de journal",
        "Error loading logs": "Erreur lors du chargement des journaux",
    }
}


# Strings the page scripts need at runtime, exposed to JavaScript as a map.
JS_STRINGS = [
    "Running",
    "Stopped",
    "Unknown",
    "Running on port",
    "No log entries found",
    "Error loading logs",
    "Loading logs...",
]


def js_translations(language=None):
    """
    Build the map of strings the page scripts translate at runtime.

    Args:
        language (str, optional): Force a language instead of the selected one.

    Returns:
        dict: English string -> translated string.
    """
    return {text: translate(text, language) for text in JS_STRINGS}


def get_language():
    """
    Return the language code selected in the settings.

    Returns:
        str: A key of LANGUAGES, falling back to DEFAULT_LANGUAGE.
    """
    language = db.get_parameter("ui_language")
    return language if language in LANGUAGES else DEFAULT_LANGUAGE


def translate(text, language=None):
    """
    Translate an English string into the selected language.

    Args:
        text (str): The English string, used as the translation key.
        language (str, optional): Force a language instead of the selected one.

    Returns:
        str: The translation, or the English string when none exists.
    """
    language = language or get_language()
    return TRANSLATIONS.get(language, {}).get(text, text)
