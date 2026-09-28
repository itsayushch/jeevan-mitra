import { describe, it, expect } from 'vitest';
import { DriftDetector } from '../src/ai-layers/layer6-monitoring/driftDetector.js';

describe('Layer 6: Drift & Bias Detector Tests', () => {
  it('detects gender skew and generates an advisory note for human review', async () => {
    // Mock prisma returning skewed recommendations (15 apparel, 1 green energy for females)
    const mockPrisma: any = {
      $queryRaw: async (query: any) => {
        return [
          { gender: 'female', sector: 'Apparel', count: 15 },
          { gender: 'female', sector: 'Green Energy', count: 1 },
          { gender: 'male', sector: 'Green Energy', count: 12 },
        ];
      },
    };

    const detector = new DriftDetector(mockPrisma);
    const advisories = await detector.scanForDrift('Moradabad');
    const genderAdvisory = advisories.find((a) => a.flag_type === 'gender_skew');

    expect(genderAdvisory).toBeDefined();
    expect(genderAdvisory?.severity).toBe('high');
    expect(genderAdvisory?.headline).toContain('Potential Gender Skew Detected');
    expect(genderAdvisory?.suggested_human_action).toContain('Audit intake interview re-prompting');
  });

  it('does not generate advisory when distribution is balanced', async () => {
    const mockPrisma: any = {
      $queryRaw: async () => [
        { gender: 'female', sector: 'Apparel', count: 8 },
        { gender: 'female', sector: 'Green Energy', count: 8 },
        { gender: 'male', sector: 'Green Energy', count: 8 },
      ],
    };

    const detector = new DriftDetector(mockPrisma);
    const advisories = await detector.scanForDrift('Moradabad');
    const genderAdvisory = advisories.find((a) => a.flag_type === 'gender_skew');

    expect(genderAdvisory).toBeUndefined();
  });
});
