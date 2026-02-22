"""Backward-compatible view imports.

Domain HTTP handlers are now implemented under `server.domains.*.http`.
This module re-exports them to avoid breaking older imports.
"""

from server.domains.admin.http import *  # noqa: F403
from server.domains.auth.http import *  # noqa: F403
from server.domains.dashboard.http import *  # noqa: F403
from server.domains.data_updates.http import *  # noqa: F403
from server.domains.projects.http import *  # noqa: F403
from server.domains.research_notes.http import *  # noqa: F403
from server.domains.researchers.http import *  # noqa: F403
from server.domains.signatures.http import *  # noqa: F403
