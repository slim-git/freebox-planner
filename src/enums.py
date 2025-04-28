from enum import Enum

class WifiState(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISABLED = "disabled"
    DISABLED_PLANNING = "disabled_planning"
    FAILED = "failed"
    UNKNOWN = "unknown"
    ACTIVE_PLANIF = "active_planif"

    @classmethod
    def get_by_value(cls, value) -> 'WifiState':
        for state in WifiState:
            if state.value == value:
                return state
        return WifiState.UNKNOWN

class WifiPlanningState(Enum):
    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"

class Endpoint(Enum):
    LOGIN = "login/"
    WIFI_CONFIG = "wifi/config/"
    WIFI_AP = "wifi/ap/"
    WIFI_PLANNING = "wifi/planning/"
    WIFI_PLANNING_MAPPING = "wifi/planning/mapping/"
    WIFI_PLANNING_STATE = "wifi/planning/state/"
    WIFI_PLANNING_ACTIVE = "wifi/planning/active/"
    LOGIN_AUTHORIZE = "login/authorize/"
    LOGIN_SESSION = "login/session/"
    LOGIN_LOGOUT = "login/logout/"