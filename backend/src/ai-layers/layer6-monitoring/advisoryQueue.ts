import { MonitoringRepository } from '../../repositories/monitoringRepository.js';
import { DriftDetector } from './driftDetector.js';
import { DriftAdvisory } from '../../types/index.js';
import { logger } from '../../utils/logger.js';

export class AdvisoryQueueManager {
  private monitoringRepo: MonitoringRepository;
  private driftDetector: DriftDetector;

  constructor(monitoringRepo?: MonitoringRepository, driftDetector?: DriftDetector) {
    this.monitoringRepo = monitoringRepo || new MonitoringRepository();
    this.driftDetector = driftDetector || new DriftDetector();
  }

  /**
   * Run automated drift detection and post new advisories to human reviewer queue
   */
  async runAuditCycle(district: string = 'Moradabad'): Promise<DriftAdvisory[]> {
    logger.info('AdvisoryQueueManager: Running drift and bias audit cycle', { district });
    const detected = await this.driftDetector.scanForDrift(district);

    for (const advisory of detected) {
      await this.monitoringRepo.recordAdvisory(advisory);
    }

    return detected;
  }

  async getReviewerQueue(district?: string): Promise<DriftAdvisory[]> {
    return this.monitoringRepo.listAdvisories({ district, status: 'open' });
  }

  async acknowledgeAdvisory(id: string): Promise<boolean> {
    return this.monitoringRepo.updateStatus(id, 'acknowledged');
  }

  async resolveAdvisory(id: string): Promise<boolean> {
    return this.monitoringRepo.updateStatus(id, 'resolved');
  }
}
