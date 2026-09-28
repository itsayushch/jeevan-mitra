import { MatchState, ActorRole } from '../../types/index.js';
import { UnauthorizedStateTransitionError } from '../../repositories/recommendationRepository.js';

/**
 * Enforces Claim 1 (The Verified Match Protocol) state machine rules.
 *
 * INVARIANT:
 * - 'Interest Match' -> 'Verified Match': ONLY permitted by human field_worker or district_officer.
 *   Generative AI layers ('system') and beneficiaries are strictly blocked.
 * - 'Verified Match' -> 'Interest Match': Permitted when a batch is full, cancelled, or expired.
 */
export class MatchStateMachine {
  static validateTransition(
    current: MatchState,
    target: MatchState,
    actorRole: ActorRole,
    hasConfirmedOpportunity: boolean
  ): void {
    if (current === target) return;

    if (target === 'Verified Match') {
      if (actorRole !== 'field_worker' && actorRole !== 'district_officer') {
        throw new UnauthorizedStateTransitionError(
          `State Machine Invariant Violation: Actor role '${actorRole}' is prohibited from transitioning recommendation to 'Verified Match'. Only human field workers or district officers can verify local batch availability.`
        );
      }

      if (!hasConfirmedOpportunity) {
        throw new Error(
          `Invalid state transition: Cannot verify match without a linked, verified local opportunity with available seats.`
        );
      }
    }
  }

  /**
   * Determine initial match state based on ground truth availability
   */
  static determineInitialState(hasVerifiedActiveBatch: boolean): MatchState {
    // If a verified live batch exists right now, it qualifies as Verified Match
    return hasVerifiedActiveBatch ? 'Verified Match' : 'Interest Match';
  }
}
