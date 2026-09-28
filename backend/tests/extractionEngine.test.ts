import { describe, it, expect } from 'vitest';
import { ExtractionEngine } from '../src/ai-layers/layer2-extraction/extractionEngine.js';
import { generateProfileConfirmation } from '../src/ai-layers/layer2-extraction/validation.js';
import { InterviewTurn } from '../src/types/index.js';

describe('Layer 2: Structured Extraction & Confidence Scoring Tests', () => {
  const engine = new ExtractionEngine(0.75);

  it('correctly extracts structured fields from clear conversational turns', () => {
    const turns: InterviewTurn[] = [
      {
        turn_number: 1,
        question_id: 'q1_location',
        question_text: 'District and block?',
        transcript: 'Main Moradabad district ke Chhajlet gaon se hoon',
        confidence: 0.95,
        clarification_needed: false,
        timestamp: new Date().toISOString(),
      },
      {
        turn_number: 2,
        question_id: 'q2_education',
        question_text: 'Education?',
        transcript: 'Maine 10th pass kiya hai',
        confidence: 0.95,
        clarification_needed: false,
        timestamp: new Date().toISOString(),
      },
      {
        turn_number: 3,
        question_id: 'q3_current_work',
        question_text: 'Current work?',
        transcript: 'Humare ghar mein kheti aur khet majdoori ka kaam hota hai',
        confidence: 0.90,
        clarification_needed: false,
        timestamp: new Date().toISOString(),
      },
      {
        turn_number: 4,
        question_id: 'q4_interests',
        question_text: 'Interests?',
        transcript: 'Mujhe bike aur tractor repair ka kaam seekhna hai',
        confidence: 0.92,
        clarification_needed: false,
        timestamp: new Date().toISOString(),
      },
      {
        turn_number: 5,
        question_id: 'q5_prior_skills',
        question_text: 'Prior skills?',
        transcript: 'Main gaon ki dukan par thoda tractor maintenance aur tool chalana seekha hai',
        confidence: 0.88,
        clarification_needed: false,
        timestamp: new Date().toISOString(),
      },
      {
        turn_number: 6,
        question_id: 'q6_travel_radius',
        question_text: 'Travel radius?',
        transcript: 'Main 10 km tak roz aana-jana kar sakta hoon',
        confidence: 0.95,
        clarification_needed: false,
        timestamp: new Date().toISOString(),
      },
      {
        turn_number: 7,
        question_id: 'q7_accessibility',
        question_text: 'Accessibility?',
        transcript: 'Koi dikkat nahi hai',
        confidence: 0.90,
        clarification_needed: false,
        timestamp: new Date().toISOString(),
      },
      {
        turn_number: 8,
        question_id: 'q8_work_preference',
        question_text: 'Work preference?',
        transcript: 'Apna khud ka garage kholna chahta hoon self employment',
        confidence: 0.95,
        clarification_needed: false,
        timestamp: new Date().toISOString(),
      },
    ];

    const profile = engine.extractProfile(turns);

    expect(profile.block.value).toBe('Chhajlet');
    expect(profile.education_level.value).toBe('Class 10');
    expect(profile.education_level.confidence).toBeGreaterThanOrEqual(0.75);
    expect(profile.education_level.confirmed).toBe(true);
    expect(profile.mobility_radius_km.value).toBe(10);
    expect(profile.work_preference.value).toBe('self_employment');
    expect(profile.requires_clarification.length).toBe(0);

    const readback = generateProfileConfirmation(profile, 'hi');
    expect(readback.spokenSummary).toContain('Chhajlet');
    expect(readback.spokenSummary).toContain('Class 10');
  });

  it('flags low-confidence ambiguous answers for beneficiary clarification', () => {
    const noisyTurns: InterviewTurn[] = [
      {
        turn_number: 1,
        question_id: 'q1_location',
        question_text: 'Location?',
        transcript: 'haan', // Ambiguous
        confidence: 0.4,
        clarification_needed: true,
        timestamp: new Date().toISOString(),
      },
      {
        turn_number: 2,
        question_id: 'q2_education',
        question_text: 'Education?',
        transcript: 'kuch nahi', // Ambiguous
        confidence: 0.5,
        clarification_needed: true,
        timestamp: new Date().toISOString(),
      },
    ];

    const profile = engine.extractProfile(noisyTurns);
    expect(profile.requires_clarification.length).toBeGreaterThan(0);
    expect(profile.requires_clarification).toContain('district_and_block');
  });
});
