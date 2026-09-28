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
  runAuditCycle(district: string = 'Moradabad'): DriftAdvisory[] {
    logger.info('AdvisoryQueueManager: Running drift and bias audit cycle', { district });
    const detected = this.driftDetector.scanForDrift(district);

    for (const advisory of detected) {
      this.monitoringRepo.recordAdvisory(advisory);
    }

    return detected;
  }

  getReviewerQueue(district?: string): DriftAdvisory[] {
    return this.monitoringRepo.listAdvisories({ district, status: 'open' });
  }

  acknowledgeAdvisory(id: string): boolean {
    return this.monitoringRepo.updateStatus(id, 'acknowledged');
  }

  resolveAdvisory(id: string): boolean {
    return this.monitoringRepo.updateStatus(id, 'resolved');
  }
}
