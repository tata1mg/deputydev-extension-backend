from sanic.config import Config


class TorpedoConfig(Config):
    """Custom Torpedo config, extending Sanic's Config.

    Use it to define default values for sanic specific configuration.
    """

    # =-= increase request header size limit =-=
    REQUEST_MAX_HEADER_SIZE = 32768  # := 32768 bytes (default 8192 bytes)
    MOTD = False
    # =-= disable sanic's access logger =-=
    ACCESS_LOG = False
