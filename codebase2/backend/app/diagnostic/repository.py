"""Replaceable repository abstraction with an in-memory hackathon implementation."""

from abc import ABC, abstractmethod
from threading import RLock

from .models import DiagnosticSession, StudentResponse


class SessionNotFoundError(LookupError):
    """Raised when a session identifier is unknown."""


class DiagnosticSessionRepository(ABC):
    """Persistence boundary that can later be backed by PostgreSQL."""

    @abstractmethod
    def create_session(self, session: DiagnosticSession) -> DiagnosticSession:
        """Store a newly generated diagnostic session."""

    @abstractmethod
    def get_session(self, session_id: str) -> DiagnosticSession:
        """Return a session or raise a stable not-found error."""

    @abstractmethod
    def save_response(self, response: StudentResponse) -> StudentResponse:
        """Store or replace one student's answer to one session question."""


class InMemoryDiagnosticSessionRepository(DiagnosticSessionRepository):
    """Process-local repository intended for demos, not durable classroom records."""

    def __init__(self) -> None:
        self._sessions: dict[str, DiagnosticSession] = {}
        self._lock = RLock()

    def create_session(self, session: DiagnosticSession) -> DiagnosticSession:
        """Store a session under its generated ID."""
        with self._lock:
            self._sessions[session.id] = session
            return session

    def get_session(self, session_id: str) -> DiagnosticSession:
        """Read one session while preserving a clear absent-session contract."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError("Diagnostic session was not found.")
            return session

    def save_response(self, response: StudentResponse) -> StudentResponse:
        """Replace the student's earlier answer to the same question, if present."""
        with self._lock:
            session = self.get_session(response.session_id)
            session.responses = [
                item
                for item in session.responses
                if not (item.student_id == response.student_id and item.question_id == response.question_id)
            ]
            session.responses.append(response)
            return response
