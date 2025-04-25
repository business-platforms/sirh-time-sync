def get_error_message(error_code):
    """
    Returns the French error message for a given error code.
    Args:
        error_code (str): The error code to look up
    Returns:
        str: The corresponding French error message or a default message if not found
    """
    if error_code == "N/A":
        return error_code
    return pointing_error_translations.get(error_code, "Erreur inconnue *")
# Constants
MONTH_POINTING_ALREADY_EXISTS = "E311"
HOURS_AND_DAYS_MUST_BE_NULL = "E312"
HOURS_MUST_BE_NULL = "E313"
MAX_DAYS_EXCEEDED = "E314"
MAX_HOURS_EXCEEDED = "E315"
POINTING_DAY_GREATER_THAN_EXIT_DAY = "E316"
DAY_POINTING_ALREADY_EXISTS = "E317"
INVALID_POINTING_DAY = "E318"
DAYS_FROM_DIFFERENT_MONTHS = "E319"
DAYS_ARE_DUPLICATED = "E320"
MAX_HOURS_IN_DAY_EXCEEDED = "E321"
INVALID_POINTING_INTERVAL = "E322"
POINTING_OVERLAP = "E323"
DAYS_MUST_BE_NULL = "E325"
HOURS_MUST_NOT_BE_NULL = "E326"
DAYS_MUST_NOT_BE_NULL = "E327"
POINTING_DAY_LESS_THAN_START_DAY = "E344"
MONTH_POINTING_USED_IN_EMPLOYEE_PAY = "E346"
MONTH_POINTING_WAS_UPDATED = "E368"
NO_CORRESPONDING_ENTRANCE = "E360"
INTERSECTION_OF_PERIODS = "E4"
UNKNOWN = "E6"
DATE_PARSE_ERROR = "E2"
REQUIRED_FIELD = "E0"
# Translation mapping
pointing_error_translations = {
    HOURS_MUST_BE_NULL: "Les heures doivent être nulles",
    MAX_DAYS_EXCEEDED: "Nombre maximum de jours dépassé",
    MAX_HOURS_EXCEEDED: "Nombre maximum d'heures dépassé",
    POINTING_DAY_GREATER_THAN_EXIT_DAY: "Le jour de pointage est postérieur au jour de sortie",
    DAY_POINTING_ALREADY_EXISTS: "Le pointage journalier existe déjà",
    INVALID_POINTING_DAY: "Jour de pointage invalide",
    DAYS_FROM_DIFFERENT_MONTHS: "Jours de mois différents",
    DAYS_ARE_DUPLICATED: "Les jours sont dupliqués",
    MAX_HOURS_IN_DAY_EXCEEDED: "Nombre maximum d'heures par jour dépassé",
    INVALID_POINTING_INTERVAL: "Intervalle de pointage invalide",
    POINTING_OVERLAP: "Chevauchement des pointages",
    DAYS_MUST_BE_NULL: "Les jours doivent être nuls",
    HOURS_MUST_NOT_BE_NULL: "Les heures ne doivent pas être nulles",
    DAYS_MUST_NOT_BE_NULL: "Les jours ne doivent pas être nuls",
    POINTING_DAY_LESS_THAN_START_DAY: "Le jour de pointage est antérieur au jour de début",
    MONTH_POINTING_USED_IN_EMPLOYEE_PAY: "Pointage mensuel utilisé dans la paie de l'employé",
    MONTH_POINTING_WAS_UPDATED: "Le pointage mensuel a été mis à jour",
    INTERSECTION_OF_PERIODS: "Chevauchement de pointage",
    DATE_PARSE_ERROR: "Erreur d'analyse de date",
    NO_CORRESPONDING_ENTRANCE: "Aucune entrée pour cette sortie",
    REQUIRED_FIELD: "REQUIRED FIELD",
    UNKNOWN: "Erreur inconnue"
}