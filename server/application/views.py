"""Backward-compatible view imports.

Domain HTTP handlers are now implemented under `server.domains.*.api`.
This module re-exports them to avoid breaking older imports.
"""

from server.domains.admin.api import *  # noqa: F403
from server.domains.auth.api import *  # noqa: F403
from server.domains.dashboard.api import *  # noqa: F403
from server.domains.data_updates.api import *  # noqa: F403
from server.domains.projects.api import *  # noqa: F403
from server.domains.research_notes.api import *  # noqa: F403
from server.domains.researchers.api import *  # noqa: F403
from server.domains.signatures.api import *  # noqa: F403
