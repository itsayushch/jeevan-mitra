import { describe, it, expect } from 'vitest';
import { MatchStateMachine } from '../src/ai-layers/layer3-matching/stateMachine.js';
import { UnauthorizedStateTransitionError } from '../src/repositories/recommendationRepository.js';

describe('Claim 1: The Verified Match Protocol Data-Layer Invariant Tests', () => {
  it('strictly blocks AI / system actor from upgrading Interest Match to Verified Match', () => {
    expect(() => {
      MatchStateMachine.validateTransition(
        'Interest Match',
        'Verified Match',
        'system',
        true
      );
    }).toThrow(UnauthorizedStateTransitionError);
  });

  it('strictly blocks beneficiary from self-assigning Verified Match', () => {
    expect(() => {
      MatchStateMachine.validateTransition(
        'Interest Match',
        'Verified Match',
        'beneficiary',
        true
      );
    }).toThrow(UnauthorizedStateTransitionError);
  });

  it('blocks field_worker from upgrading to Verified Match when no confirmed opportunity exists', () => {
    expect(() => {
      MatchStateMachine.validateTransition(
        'Interest Match',
        'Verified Match',
        'field_worker',
        false
      );
    }).toThrow(/Cannot verify match without a linked, verified local opportunity/);
  });

  it('allows authorized human field_worker to verify match when opportunity has confirmed seats', () => {
    expect(() => {
      MatchStateMachine.validateTransition(
        'Interest Match',
        'Verified Match',
        'field_worker',
        true
      );
    }).not.toThrow();
  });

  it('allows district_officer to verify match when opportunity has confirmed seats', () => {
    expect(() => {
      MatchStateMachine.validateTransition(
        'Interest Match',
        'Verified Match',
        'district_officer',
        true
      );
    }).not.toThrow();
  });

  it('correctly determines initial match state based on batch availability', () => {
    expect(MatchStateMachine.determineInitialState(true)).toBe('Verified Match');
    expect(MatchStateMachine.determineInitialState(false)).toBe('Interest Match');
  });
});
