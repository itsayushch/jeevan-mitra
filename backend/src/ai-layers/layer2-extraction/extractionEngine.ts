import { InterviewTurn, ExtractedBeneficiaryProfile, WorkPreference } from '../../types/index.js';
import { env } from '../../config/env.js';
import { logger } from '../../utils/logger.js';

export class ExtractionEngine {
  private confidenceThreshold: number;

  constructor(threshold: number = env.CONFIDENCE_THRESHOLD) {
    this.confidenceThreshold = threshold;
  }

  /**
   * Extract structured profile JSON from raw transcript history
   */
  extractProfile(turns: InterviewTurn[], defaultDistrict: string = 'Moradabad', defaultBlock: string = 'Moradabad Rural'): ExtractedBeneficiaryProfile {
    logger.debug('ExtractionEngine: Parsing conversation transcript turns', { turnCount: turns.length });

    // Combine transcripts mapped to questions
    const textMap: Record<string, string> = {};
    for (const turn of turns) {
      textMap[turn.question_id] = turn.transcript;
    }

    const locText = (textMap['q1_location'] || '').toLowerCase();
    const eduText = (textMap['q2_education'] || '').toLowerCase();
    const currWorkText = (textMap['q3_current_work'] || '').toLowerCase();
    const interestText = (textMap['q4_interests'] || '').toLowerCase();
    const skillText = (textMap['q5_prior_skills'] || '').toLowerCase();
    const travelText = (textMap['q6_travel_radius'] || '').toLowerCase();
    const accessText = (textMap['q7_accessibility'] || '').toLowerCase();
    const prefText = (textMap['q8_work_preference'] || '').toLowerCase();

    // 1. Location Parsing
    let extractedDistrict = defaultDistrict;
    let extractedBlock = defaultBlock;
    let locConfidence = 0.50; // Default to unconfirmed until location evidence is matched

    if (locText.includes('chhajlet') || locText.includes('छजलैट')) {
      extractedBlock = 'Chhajlet';
      locConfidence = 0.95;
    } else if (locText.includes('bahjoi') || locText.includes('बहजोई')) {
      extractedBlock = 'Bahjoi';
      locConfidence = 0.95;
    } else if (locText.includes('bilari') || locText.includes('बिलारी')) {
      extractedBlock = 'Bilari';
      locConfidence = 0.95;
    } else if (locText.includes('kundarki') || locText.includes('कुंदरकी')) {
      extractedBlock = 'Kundarki';
      locConfidence = 0.95;
    } else if (locText.includes('rural') || locText.includes('देहात') || locText.includes('गांव') || locText.includes('moradabad') || locText.includes('मुरादाबाद')) {
      extractedBlock = 'Moradabad Rural';
      locConfidence = 0.90;
    }

    // 2. Education Parsing
    let educationLevel = 'Class 8';
    let eduConfidence = 0.88;

    if (eduText.includes('12') || eduText.includes('बारह') || eduText.includes('inter')) {
      educationLevel = 'Class 12';
      eduConfidence = 0.95;
    } else if (eduText.includes('10') || eduText.includes('दस') || eduText.includes('matric') || eduText.includes('हाईस्कूल')) {
      educationLevel = 'Class 10';
      eduConfidence = 0.95;
    } else if (eduText.includes('8') || eduText.includes('आठ') || eduText.includes('middle')) {
      educationLevel = 'Class 8';
      eduConfidence = 0.90;
    } else if (eduText.includes('5') || eduText.includes('पांच') || eduText.includes('primary')) {
      educationLevel = 'Class 5';
      eduConfidence = 0.85;
    } else if (eduText.includes('graduate') || eduText.includes('बीए') || eduText.includes('ba')) {
      educationLevel = 'Graduate';
      eduConfidence = 0.95;
    } else if (eduText.includes('anpadh') || eduText.includes('स्कूल नहीं गए') || eduText.includes('कोई नहीं')) {
      educationLevel = 'None';
      eduConfidence = 0.90;
    } else if (eduText.length < 4) {
      educationLevel = 'Class 8';
      eduConfidence = 0.60;
    }

    // 3. Current Work & Family Occupation
    let currentWork = 'Daily Wage Labour';
    let familyOccupation = 'Farming & Labour';
    let workConfidence = 0.85;

    if (currWorkText.includes('खेती') || currWorkText.includes('kheti') || currWorkText.includes('farm')) {
      currentWork = 'Agricultural Labour';
      familyOccupation = 'Traditional Agriculture';
      workConfidence = 0.92;
    } else if (currWorkText.includes('सिलाई') || currWorkText.includes('tailor') || currWorkText.includes('stitching')) {
      currentWork = 'Informal Tailoring';
      familyOccupation = 'Garment Making';
      workConfidence = 0.92;
    } else if (currWorkText.includes('रिपेयर') || currWorkText.includes('repair') || currWorkText.includes('mistri') || currWorkText.includes('मिस्त्री')) {
      currentWork = 'Assistant Mechanic';
      familyOccupation = 'Machine Maintenance';
      workConfidence = 0.90;
    } else if (currWorkText.includes('दुकान') || currWorkText.includes('shop')) {
      currentWork = 'Small Retail Helper';
      familyOccupation = 'Retail/Trade';
      workConfidence = 0.88;
    } else if (currWorkText.length < 3) {
      workConfidence = 0.55;
    }

    // 4. Interests Parsing
    const interests: string[] = [];
    let interestConfidence = 0.90;

    if (interestText.includes('solar') || interestText.includes('सोलर') || interestText.includes('धूप') || interestText.includes('ऊर्जा')) {
      interests.push('Solar Energy', 'Electrical Systems');
    }
    if (interestText.includes('रिपेयर') || interestText.includes('repair') || interestText.includes('बाइक') || interestText.includes('ट्रैक्टर') || interestText.includes('गाड़ी')) {
      interests.push('Automotive Repair', 'Machinery');
    }
    if (interestText.includes('बिजली') || interestText.includes('electric') || interestText.includes('तार')) {
      interests.push('Electrical Wiring', 'Appliance Repair');
    }
    if (interestText.includes('सिलाई') || interestText.includes('कपड़ा') || interestText.includes('tailoring') || interestText.includes('garment')) {
      interests.push('Garment Manufacturing', 'Tailoring & Design');
    }
    if (interestText.includes('मशरूम') || interestText.includes('खाद्य') || interestText.includes('डेयरी') || interestText.includes('दूध') || interestText.includes('food')) {
      interests.push('Food Processing', 'Mushroom Cultivation', 'Dairy Operations');
    }
    if (interestText.includes('ड्रिप') || interestText.includes('सिंचाई') || interestText.includes('irrigation')) {
      interests.push('Micro-Irrigation', 'Agri-Tech');
    }

    if (interests.length === 0) {
      interests.push('Machine Repair', 'General Technical');
      interestConfidence = 0.65; // Ambiguous
    }

    // 5. Prior Skills Parsing
    const skills: string[] = [];
    let skillConfidence = 0.85;

    if (skillText.includes('औजार') || skillText.includes('पेंचकस') || skillText.includes('रिंच') || skillText.includes('tool')) {
      skills.push('Hand Tools Operation');
    }
    if (skillText.includes('तार') || skillText.includes('wiring') || skillText.includes('बिजली')) {
      skills.push('Basic Electrical Wiring');
    }
    if (skillText.includes('सिलाई') || skillText.includes('सुई') || skillText.includes('machine')) {
      skills.push('Sewing Machine Operation');
    }
    if (skillText.includes('ट्रैक्टर') || skillText.includes('इंजन') || skillText.includes('tractor')) {
      skills.push('Basic Tractor Maintenance');
    }

    if (skills.length === 0) {
      skills.push('Manual Precision Work');
      skillConfidence = 0.68;
    }

    // 6. Travel Radius & Mobility
    let mobilityRadiusKm = 10;
    let mobilityConfidence = 0.88;

    if (travelText.includes('5') || travelText.includes('पांच')) {
      mobilityRadiusKm = 5;
      mobilityConfidence = 0.92;
    } else if (travelText.includes('10') || travelText.includes('दस')) {
      mobilityRadiusKm = 10;
      mobilityConfidence = 0.95;
    } else if (travelText.includes('15') || travelText.includes('पंद्रह') || travelText.includes('20') || travelText.includes('बीस')) {
      mobilityRadiusKm = 20;
      mobilityConfidence = 0.90;
    } else if (travelText.includes('हॉस्टल') || travelText.includes('hostel') || travelText.includes('रुक')) {
      mobilityRadiusKm = 50; // Ready for district centre boarding
      mobilityConfidence = 0.95;
    } else if (travelText.includes('घर') || travelText.includes('गांव के पास')) {
      mobilityRadiusKm = 5;
      mobilityConfidence = 0.85;
    } else if (travelText.length < 3) {
      mobilityConfidence = 0.58;
    }

    // 7. Accessibility Needs
    let accessibilityNeeds = 'None';
    let accessConfidence = 0.90;

    if (accessText.includes('वजन') || accessText.includes('कमर') || accessText.includes('भारी')) {
      accessibilityNeeds = 'Light Physical Work (No heavy lifting)';
      accessConfidence = 0.92;
    } else if (accessText.includes('बच्चा') || accessText.includes('घर से') || accessText.includes('home')) {
      accessibilityNeeds = 'Home-based / Flexible timings (Childcare)';
      accessConfidence = 0.92;
    } else if (accessText.includes('चलने') || accessText.includes('पैर') || accessText.includes('दिव्यांग')) {
      accessibilityNeeds = 'Locomotor accessibility required';
      accessConfidence = 0.95;
    }

    // 8. Work Preference (wage vs self_employment)
    let workPreference: WorkPreference = 'both';
    let prefConfidence = 0.88;

    if (prefText.includes('दुकान') || prefText.includes('खुद का') || prefText.includes('self') || prefText.includes('व्यवसाय') || prefText.includes('व्यापार')) {
      workPreference = 'self_employment';
      prefConfidence = 0.95;
    } else if (prefText.includes('नौकरी') || prefText.includes('कंपनी') || prefText.includes('wage') || prefText.includes('पक्की')) {
      workPreference = 'wage';
      prefConfidence = 0.95;
    } else if (prefText.length < 4) {
      prefConfidence = 0.60;
    }

    // Identify low confidence fields needing confirmation
    const requiresClarification: string[] = [];
    if (locConfidence < this.confidenceThreshold) requiresClarification.push('district_and_block');
    if (eduConfidence < this.confidenceThreshold) requiresClarification.push('education_level');
    if (workConfidence < this.confidenceThreshold) requiresClarification.push('current_work');
    if (interestConfidence < this.confidenceThreshold) requiresClarification.push('interests');
    if (skillConfidence < this.confidenceThreshold) requiresClarification.push('skills');
    if (mobilityConfidence < this.confidenceThreshold) requiresClarification.push('mobility_radius_km');
    if (accessConfidence < this.confidenceThreshold) requiresClarification.push('accessibility_needs');
    if (prefConfidence < this.confidenceThreshold) requiresClarification.push('work_preference');

    return {
      education_level: {
        value: educationLevel,
        confidence: eduConfidence,
        confirmed: eduConfidence >= this.confidenceThreshold,
      },
      current_work: {
        value: currentWork,
        confidence: workConfidence,
        confirmed: workConfidence >= this.confidenceThreshold,
      },
      family_occupation: {
        value: familyOccupation,
        confidence: workConfidence,
        confirmed: workConfidence >= this.confidenceThreshold,
      },
      interests: {
        value: interests,
        confidence: interestConfidence,
        confirmed: interestConfidence >= this.confidenceThreshold,
      },
      skills: {
        value: skills,
        confidence: skillConfidence,
        confirmed: skillConfidence >= this.confidenceThreshold,
      },
      mobility_radius_km: {
        value: mobilityRadiusKm,
        confidence: mobilityConfidence,
        confirmed: mobilityConfidence >= this.confidenceThreshold,
      },
      accessibility_needs: {
        value: accessibilityNeeds,
        confidence: accessConfidence,
        confirmed: accessConfidence >= this.confidenceThreshold,
      },
      work_preference: {
        value: workPreference,
        confidence: prefConfidence,
        confirmed: prefConfidence >= this.confidenceThreshold,
      },
      district: {
        value: extractedDistrict,
        confidence: locConfidence,
        confirmed: locConfidence >= this.confidenceThreshold,
      },
      block: {
        value: extractedBlock,
        confidence: locConfidence,
        confirmed: locConfidence >= this.confidenceThreshold,
      },
      requires_clarification: requiresClarification,
    };
  }
}
