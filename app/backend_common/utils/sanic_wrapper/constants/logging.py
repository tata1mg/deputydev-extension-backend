"""Logging related constants."""

from enum import StrEnum

FORMAT_VERSION = "v2"


class LogType(StrEnum):
    ACCESS_LOG = "access"
    CUSTOM_LOG = "custom"
    BACKGROUND_CUSTOM_LOG = "background"
    EXTERNAL_CALL_LOG = "external"


class LogLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TracebackTheme(StrEnum):
    """Supported traceback themes.

    These are essentially ``pygments'`` styles:

    ```python
    from pygments.styles import get_all_styles

    list(get_all_styles())
    ```

    """

    # =-= default =-=
    ONE_DARK = "one-dark"

    ABAP = "abap"
    ALGOL = "algol"
    ALGOL_NU = "algol_nu"
    ARDUINO = "arduino"
    AUTUMN = "autumn"
    BW = "bw"
    BORLAND = "borland"
    COLORFUL = "colorful"
    DEFAULT = "default"
    DRACULA = "dracula"
    EMACS = "emacs"
    FRIENDLY_GRAYSCALE = "friendly_grayscale"
    FRIENDLY = "friendly"
    FRUITY = "fruity"
    GITHUB_DARK = "github-dark"
    GRUVBOX_DARK = "gruvbox-dark"
    GRUVBOX_LIGHT = "gruvbox-light"
    IGOR = "igor"
    INKPOT = "inkpot"
    LIGHTBULB = "lightbulb"
    LILYPOND = "lilypond"
    LOVELACE = "lovelace"
    MANNI = "manni"
    MATERIAL = "material"
    MONOKAI = "monokai"
    MURPHY = "murphy"
    NATIVE = "native"
    NORD_DARKER = "nord-darker"
    NORD = "nord"
    PARAISO_DARK = "paraiso-dark"
    PARAISO_LIGHT = "paraiso-light"
    PASTIE = "pastie"
    PERLDOC = "perldoc"
    RAINBOW_DASH = "rainbow_dash"
    RRT = "rrt"
    SAS = "sas"
    SOLARIZED_DARK = "solarized-dark"
    SOLARIZED_LIGHT = "solarized-light"
    STAROFFICE = "staroffice"
    STATA_DARK = "stata-dark"
    STATA_LIGHT = "stata-light"
    TANGO = "tango"
    TRAC = "trac"
    VIM = "vim"
    VS = "vs"
    XCODE = "xcode"
    ZENBURN = "zenburn"
