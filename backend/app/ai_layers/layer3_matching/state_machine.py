class UnauthorizedStateTransitionError(Exception):
    """Raised when an unauthorized actor attempts to transition a recommendation."""
    pass

class MatchStateMachine:
    """
    Enforces Claim 1 (The Verified Match Protocol) state machine rules.

    INVARIANT:
    - 'Interest Match' -> 'Verified Match': ONLY permitted by human field_worker or district_officer.
      Generative AI layers ('system') and beneficiaries are strictly blocked.
    - 'Verified Match' -> 'Interest Match': Permitted when a batch is full, cancelled, or expired.
    """

    @staticmethod
    def validate_transition(
        current_state: str,
        target_state: str,
        actor_role: str,
        has_confirmed_opportunity: bool
    ) -> None:
        if current_state == target_state:
            return

        if target_state == "Verified Match":
            if actor_role not in ["field_worker", "district_officer"]:
                raise UnauthorizedStateTransitionError(
                    f"State Machine Invariant Violation: Actor role '{actor_role}' is prohibited from transitioning recommendation to 'Verified Match'. Only human field workers or district officers can verify local batch availability."
                )

            if not has_confirmed_opportunity:
                raise ValueError(
                    "Invalid state transition: Cannot verify match without a linked, verified local opportunity with available seats."
                )

    @staticmethod
    def determine_initial_state(has_verified_active_batch: bool) -> str:
        return "Verified Match" if has_verified_active_batch else "Interest Match"
