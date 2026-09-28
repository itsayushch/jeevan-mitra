import { v4 as uuidv4 } from 'uuid';
import { getDb } from './connection.js';
// import { runMigrations } from './migrations.js';
import { QualificationRepository } from '../repositories/qualificationRepository.js';
import { OpportunityRepository } from '../repositories/opportunityRepository.js';
import { BeneficiaryRepository } from '../repositories/beneficiaryRepository.js';
import { SessionRepository } from '../repositories/sessionRepository.js';
import { RecommendationRepository } from '../repositories/recommendationRepository.js';
import { ReferralRepository } from '../repositories/referralRepository.js';
import { OutcomeRepository } from '../repositories/outcomeRepository.js';
import { AuditRepository } from '../repositories/auditRepository.js';
import { logger } from '../utils/logger.js';

export async function seedDatabase(): Promise<void> {
  const db = getDb();
  logger.info('Initializing database schema and migrations...');
  // runMigrations(db); // Prisma handles schema now

  const qualRepo = new QualificationRepository(db);
  const oppRepo = new OpportunityRepository(db);
  const benRepo = new BeneficiaryRepository(db);
  const sessionRepo = new SessionRepository(db);
  const recRepo = new RecommendationRepository(db);
  const refRepo = new ReferralRepository(db);
  const outcomeRepo = new OutcomeRepository(db);
  const auditRepo = new AuditRepository(db);

  // Check if already seeded
  const existingQuals = await qualRepo.listVerified();
  if (existingQuals.length > 0) {
    logger.info('Database already seeded. Skipping initial seed.');
    return;
  }

  logger.info('Seeding verified NQR qualifications...');

  // 1. Qualifications
  const solarQual = await qualRepo.create({
    id: 'qual_solar_01',
    nqr_code: 'SGJ/Q0101',
    title: 'Solar PV Installer (Suryamitra)',
    sector: 'Green Energy',
    nsqf_level: 4,
    duration_hours: 320,
    min_education: 'Class 10',
    min_education_rank: 3,
    work_type: 'wage',
    physical_intensity: 'medium_high',
    skills_acquired: ['Solar PV Installation', 'Electrical Inverter Wiring', 'Rooftop Mounts', 'Grid Safety'],
    curriculum_summary: 'Comprehensive rooftop solar PV installation, electrical connection, and routine fault diagnosis.',
    entry_criteria: 'Class 10th standard pass or ITI electrical pass',
    certification_body: 'Skill Council for Green Jobs (SCGJ)',
    nqr_link: 'https://nqr.gov.in/qualifications/SGJ-Q0101',
    verification_status: 'verified',
    verification_date: '2026-01-15',
  });

  const sewingQual = await qualRepo.create({
    id: 'qual_sewing_02',
    nqr_code: 'AMH/Q0301',
    title: 'Sewing Machine Operator',
    sector: 'Apparel',
    nsqf_level: 2,
    duration_hours: 210,
    min_education: 'Class 5',
    min_education_rank: 1,
    work_type: 'self_employment',
    physical_intensity: 'light',
    skills_acquired: ['Garment Stitching', 'Sewing Machine Operation', 'Pattern Cutting', 'Finishing & Quality'],
    curriculum_summary: 'Industrial and domestic sewing machine operation, standard seam stitching, garment construction, and equipment maintenance.',
    entry_criteria: 'Ability to read and write (Class 5 preferred)',
    certification_body: 'Apparel Made-Ups & Home Furnishing Sector Skill Council',
    nqr_link: 'https://nqr.gov.in/qualifications/AMH-Q0301',
    verification_status: 'verified',
    verification_date: '2026-01-20',
  });

  const electricianQual = await qualRepo.create({
    id: 'qual_elec_03',
    nqr_code: 'ELE/Q5801',
    title: 'Assistant Electrician',
    sector: 'Electronics',
    nsqf_level: 3,
    duration_hours: 350,
    min_education: 'Class 8',
    min_education_rank: 2,
    work_type: 'both',
    physical_intensity: 'medium',
    skills_acquired: ['Domestic Wiring', 'Conduit Installation', 'Earthing & Fuse Repair', 'Safety Protocols'],
    curriculum_summary: 'Laying domestic circuits, installation of light points, test equipment usage, and safety regulations.',
    entry_criteria: 'Class 8th standard pass',
    certification_body: 'Electronics Sector Skills Council of India',
    nqr_link: 'https://nqr.gov.in/qualifications/ELE-Q5801',
    verification_status: 'verified',
    verification_date: '2026-02-01',
  });

  const foodQual = await qualRepo.create({
    id: 'qual_food_04',
    nqr_code: 'FIC/Q9001',
    title: 'Small Food Business Operator',
    sector: 'Food Processing',
    nsqf_level: 2,
    duration_hours: 240,
    min_education: 'Class 5',
    min_education_rank: 1,
    work_type: 'self_employment',
    physical_intensity: 'light',
    skills_acquired: ['Food Hygiene & FSSAI Standards', 'Packaging & Labelling', 'Small Enterprise Bookkeeping', 'Pickle/Spice Processing'],
    curriculum_summary: 'Fundamentals of micro food processing, spice grinding, packaging, local distribution, and regulatory licensing.',
    entry_criteria: 'Basic literacy (Class 5 pass preferred)',
    certification_body: 'Food Industry Capacity & Skill Initiative (FICSI)',
    nqr_link: 'https://nqr.gov.in/qualifications/FIC-Q9001',
    verification_status: 'verified',
    verification_date: '2026-02-10',
  });

  const bikeQual = await qualRepo.create({
    id: 'qual_bike_05',
    nqr_code: 'ASC/Q1411',
    title: 'Two-Wheeler Service Technician',
    sector: 'Automotive',
    nsqf_level: 4,
    duration_hours: 400,
    min_education: 'Class 8',
    min_education_rank: 2,
    work_type: 'both',
    physical_intensity: 'medium',
    skills_acquired: ['Engine Overhaul', 'Brake & Suspension Servicing', 'Electrical Diagnostics', 'Workshop Safety'],
    curriculum_summary: 'Inspection, routine periodic servicing, troubleshooting, and overhaul of two-wheeler mechanical and electrical assemblies.',
    entry_criteria: 'Class 8th pass with practical interest in mechanical systems',
    certification_body: 'Automotive Skills Development Council (ASDC)',
    nqr_link: 'https://nqr.gov.in/qualifications/ASC-Q1411',
    verification_status: 'verified',
    verification_date: '2026-01-25',
  });

  const irrigationQual = await qualRepo.create({
    id: 'qual_irrig_06',
    nqr_code: 'AGR/Q1003',
    title: 'Micro-Irrigation Technician',
    sector: 'Agriculture',
    nsqf_level: 3,
    duration_hours: 200,
    min_education: 'Class 8',
    min_education_rank: 2,
    work_type: 'wage',
    physical_intensity: 'medium',
    skills_acquired: ['Drip Irrigation Piping', 'Sprinkler Assembly', 'Water Pressure Pumps', 'Field Trenching'],
    curriculum_summary: 'Installation and maintenance of micro-irrigation systems in farm fields, pump coupling, and filter flushing.',
    entry_criteria: 'Class 8th pass',
    certification_body: 'Agriculture Skill Council of India (ASCI)',
    nqr_link: 'https://nqr.gov.in/qualifications/AGR-Q1003',
    verification_status: 'verified',
    verification_date: '2026-02-05',
  });

  logger.info('Seeding verified local opportunities (Batches & Seats)...');

  // 2. Local Opportunities (Batches) in Moradabad District
  const rsetiElectrician = await oppRepo.create({
    id: 'opp_rseti_elec',
    qualification_id: electricianQual.id,
    centre_or_employer_name: 'Rural Self-Employment Training Inst. (RSETI) Moradabad',
    type: 'training_centre',
    district: 'Moradabad',
    block: 'Moradabad Rural',
    address: 'Sector 4, Industrial Area, District Centre, Moradabad',
    latitude: 28.835,
    longitude: 78.77,
    batch_start_date: '2026-11-15',
    batch_end_date: '2027-02-28',
    total_seats: 25,
    available_seats: 11,
    sc_reserved_seats: 11,
    batch_status: 'active',
    hostel_available: true,
    stipend_amount_inr: 1500,
    free_toolkit_provided: true,
    source: 'pm_ajay_district_mission',
    verified_by_worker_id: 'worker_vle_01',
    verified_at: '2026-09-20T10:00:00Z',
  });

  const rsetiSewing = await oppRepo.create({
    id: 'opp_rseti_sewing',
    qualification_id: sewingQual.id,
    centre_or_employer_name: 'PMKK Skill Training Centre, Moradabad Rural',
    type: 'training_centre',
    district: 'Moradabad',
    block: 'Moradabad Rural',
    address: 'Near Block Development Office, Moradabad Rural',
    latitude: 28.838,
    longitude: 78.773,
    batch_start_date: '2026-11-01',
    batch_end_date: '2027-01-15',
    total_seats: 30,
    available_seats: 14,
    sc_reserved_seats: 15,
    batch_status: 'active',
    hostel_available: false,
    stipend_amount_inr: 1000,
    free_toolkit_provided: true,
    source: 'pm_ajay_district_mission',
    verified_by_worker_id: 'worker_vle_01',
    verified_at: '2026-09-22T11:30:00Z',
  });

  const chhajletBike = await oppRepo.create({
    id: 'opp_chhajlet_bike',
    qualification_id: bikeQual.id,
    centre_or_employer_name: 'Government ITI Chhajlet Extension Centre',
    type: 'training_centre',
    district: 'Moradabad',
    block: 'Chhajlet',
    address: 'Kanth-Chhajlet Road, Block Chhajlet, Moradabad',
    latitude: 28.985,
    longitude: 78.681,
    batch_start_date: '2026-11-20',
    batch_end_date: '2027-03-31',
    total_seats: 20,
    available_seats: 8,
    sc_reserved_seats: 8,
    batch_status: 'active',
    hostel_available: false,
    stipend_amount_inr: 1200,
    free_toolkit_provided: true,
    source: 'pm_ajay_district_mission',
    verified_by_worker_id: 'worker_vle_02',
    verified_at: '2026-09-18T14:00:00Z',
  });

  const bilariSolar = await oppRepo.create({
    id: 'opp_bilari_solar',
    qualification_id: solarQual.id,
    centre_or_employer_name: 'Govt ITI Bilari Green Energy Hub',
    type: 'training_centre',
    district: 'Moradabad',
    block: 'Bilari',
    address: 'Station Road, Bilari, Moradabad',
    latitude: 28.625,
    longitude: 78.802,
    batch_start_date: '2026-12-01',
    batch_end_date: '2027-04-15',
    total_seats: 25,
    available_seats: 9,
    sc_reserved_seats: 10,
    batch_status: 'active',
    hostel_available: true,
    stipend_amount_inr: 1800,
    free_toolkit_provided: true,
    source: 'pm_ajay_district_mission',
    verified_by_worker_id: 'worker_vle_03',
    verified_at: '2026-09-19T09:00:00Z',
  });

  logger.info('Seeding test beneficiaries across PM-AJAY user journey stages...');

  // 3. Beneficiary 1: Sunita Devi (Matches Screen 9 Progress Tracker: Tailoring & Apparel, Moradabad Rural)
  const sunita = await benRepo.create({
    id: 'ben_sunita_8812',
    name: 'Sunita Devi',
    phone: '9876543210',
    gender: 'female',
    age: 26,
    category: 'SC',
    preferred_language: 'hi',
    district: 'Moradabad',
    block: 'Moradabad Rural',
    village: 'Sirsi',
    contact_preference: 'voice',
  });

  // Consented - no longer using db.prepare. Use Prisma
  // We can just use Prisma client if exposed, or rely on not seeding this if unnecessary.
  // We'll skip it for seed since consent is handled via API mostly, or use raw:
  await db.$executeRaw`
    INSERT INTO "Consent" (id, beneficiary_id, purpose, notice_version, audio_consent_recorded, voice_retention_choice, dpdp_affirmative_consent, timestamp)
    VALUES (${`cns_${uuidv4()}`}, ${sunita.id}, 'PM-AJAY GIA Skilling Counseling', '1.0', 1, 'do_not_keep', 1, '2026-09-10T10:00:00Z')
  `;

  // Answers
  await sessionRepo.saveProfileAnswer({ beneficiaryId: sunita.id, fieldName: 'education_level', fieldValue: 'Class 8', confidenceScore: 0.95, confirmationStatus: 'confirmed' });
  await sessionRepo.saveProfileAnswer({ beneficiaryId: sunita.id, fieldName: 'current_work', fieldValue: 'Informal Stitching at Home', confidenceScore: 0.92, confirmationStatus: 'confirmed' });
  await sessionRepo.saveProfileAnswer({ beneficiaryId: sunita.id, fieldName: 'interests', fieldValue: JSON.stringify(['Tailoring & Design', 'Garment Making']), confidenceScore: 0.95, confirmationStatus: 'confirmed' });
  await sessionRepo.saveProfileAnswer({ beneficiaryId: sunita.id, fieldName: 'skills', fieldValue: JSON.stringify(['Hand Stitching', 'Basic Needle Work']), confidenceScore: 0.90, confirmationStatus: 'confirmed' });
  await sessionRepo.saveProfileAnswer({ beneficiaryId: sunita.id, fieldName: 'mobility_radius_km', fieldValue: '5', confidenceScore: 0.95, confirmationStatus: 'confirmed' });
  await sessionRepo.saveProfileAnswer({ beneficiaryId: sunita.id, fieldName: 'accessibility_needs', fieldValue: 'Home-based / Flexible (Childcare)', confidenceScore: 0.92, confirmationStatus: 'confirmed' });
  await sessionRepo.saveProfileAnswer({ beneficiaryId: sunita.id, fieldName: 'work_preference', fieldValue: 'self_employment', confidenceScore: 0.95, confirmationStatus: 'confirmed' });

  // Recommendations for Sunita: Verified Match for Sewing Machine Operator
  const sunitaRecs = await recRepo.saveRecommendations(sunita.id, undefined, [
    {
      session_id: undefined,
      qualification_id: sewingQual.id,
      local_opportunity_id: rsetiSewing.id,
      rank: 1,
      score: 94,
      score_breakdown: { interest: 30, prior_skills: 20, access: 20, local_demand: 18, work_preference: 10 },
      match_state: 'Verified Match', // Verified live batch nearby
      explanation_text: 'आपकी सिलाई में रुचि और स्वरोजगार की प्राथमिकता के अनुसार "Sewing Machine Operator" आपके लिए सर्वोत्तम विकल्प है। ब्लॉक डेवलपमेंट ऑफिस के पास स्थित PMKK केंद्र में नया बैच 1 नवंबर से शुरू हो रहा है।',
      audio_explanation_script: 'नमस्ते सुनीता जी! आपकी रुचि के अनुसार सिलाई ऑपरेटर का 210 घंटे का कोर्स स्वीकृत केंद्र पर उपलब्ध है। आप सीधे नामांकन हेतु अनुरोध कर सकती हैं।',
      tradeoff_summary: 'घर से खुद की दुकान शुरू करने की सुविधा, सरकारी टूलकिट और सिलाई मशीन सहायता उपलब्ध।',
      skill_gap_summary: 'बेसिक हाथ की सिलाई से औद्योगिक मशीन ऑपरेटर बनने हेतु 7 सप्ताह की ट्रेनिंग।',
      data_snapshot: { qualification: sewingQual, opportunity: rsetiSewing, timestamp: new Date().toISOString() },
    },
    {
      session_id: undefined,
      qualification_id: foodQual.id,
      local_opportunity_id: null,
      rank: 2,
      score: 72,
      score_breakdown: { interest: 22, prior_skills: 12, access: 6, local_demand: 6, work_preference: 10 },
      match_state: 'Interest Match', // No confirmed live batch in immediate block
      explanation_text: 'Small Food Business Operator का कोर्स भी आपकी घरेलू स्वरोजगार प्राथमिकता से मेल खाता है, लेकिन वर्तमान में आपके ब्लॉक में इसका स्थानीय बैच सत्यापित नहीं है।',
      audio_explanation_script: 'खाद्य प्रसंस्करण का विकल्प भी अच्छा है, लेकिन अभी आपके पास इसका बैच कन्फर्म नहीं है।',
      tradeoff_summary: 'घरेलू उत्पाद और कम लागत में शुरू होने वाला व्यवसाय।',
      skill_gap_summary: 'फूड हाइजीन और पैकेजिंग हेतु 8 सप्ताह का प्रशिक्षण।',
      data_snapshot: { qualification: foodQual, opportunity: null, timestamp: new Date().toISOString() },
    },
  ]);

  // Referral for Sunita (Matches Screen 9)
  const sunitaRef = await refRepo.createReferral({
    beneficiaryId: sunita.id,
    recommendationId: sunitaRecs[0].id,
    localOpportunityId: rsetiSewing.id,
    assignedWorkerId: 'Ramesh Kumar (VLE)',
    notes: 'Candidate documents verified. Scheduled for November batch.',
  });
  await refRepo.updateReferral(sunitaRef.id, {
    status: 'enrolled',
    caste_document_verified: true,
    income_criteria_verified: true,
    residence_proof_verified: true,
    actorId: 'worker_vle_01',
    actorName: 'Ramesh Kumar (VLE)',
  });

  // 4. Beneficiary 2: Rajesh Kumar (Matches Screen 11: Case ID #7821, Chhajlet, 8th pass, Tractor/bike repair, max 5 km)
  const rajesh = await benRepo.create({
    id: 'ben_rajesh_7821',
    name: 'Rajesh Kumar',
    phone: '9876543211',
    gender: 'male',
    age: 23,
    category: 'SC',
    preferred_language: 'hi',
    district: 'Moradabad',
    block: 'Chhajlet',
    village: 'Chhajlet Khurd',
    contact_preference: 'voice',
  });

  await sessionRepo.saveProfileAnswer({ beneficiaryId: rajesh.id, fieldName: 'education_level', fieldValue: 'Class 8', confidenceScore: 0.89, confirmationStatus: 'confirmed' });
  await sessionRepo.saveProfileAnswer({ beneficiaryId: rajesh.id, fieldName: 'current_work', fieldValue: 'Tractor Repair Helper', confidenceScore: 0.91, confirmationStatus: 'confirmed' });
  await sessionRepo.saveProfileAnswer({ beneficiaryId: rajesh.id, fieldName: 'interests', fieldValue: JSON.stringify(['Automotive Repair', 'Machinery']), confidenceScore: 0.92, confirmationStatus: 'confirmed' });
  await sessionRepo.saveProfileAnswer({ beneficiaryId: rajesh.id, fieldName: 'skills', fieldValue: JSON.stringify(['Tractor Maintenance', 'Hand Tools Operation']), confidenceScore: 0.88, confirmationStatus: 'confirmed' });
  await sessionRepo.saveProfileAnswer({ beneficiaryId: rajesh.id, fieldName: 'mobility_radius_km', fieldValue: '5', confidenceScore: 0.85, confirmationStatus: 'confirmed' });
  await sessionRepo.saveProfileAnswer({ beneficiaryId: rajesh.id, fieldName: 'accessibility_needs', fieldValue: 'None', confidenceScore: 0.95, confirmationStatus: 'confirmed' });
  await sessionRepo.saveProfileAnswer({ beneficiaryId: rajesh.id, fieldName: 'work_preference', fieldValue: 'both', confidenceScore: 0.90, confirmationStatus: 'confirmed' });

  // Recommendations for Rajesh: Two-Wheeler Service Technician (Verified Match in Chhajlet)
  await recRepo.saveRecommendations(rajesh.id, undefined, [
    {
      session_id: undefined,
      qualification_id: bikeQual.id,
      local_opportunity_id: chhajletBike.id,
      rank: 1,
      score: 96,
      score_breakdown: { interest: 30, prior_skills: 20, access: 20, local_demand: 16, work_preference: 10 },
      match_state: 'Verified Match',
      explanation_text: 'आपकी ट्रैक्टर और बाइक रिपेयर अनुभव के आधार पर Two-Wheeler Service Technician (NSQF L4) सबसे सटीक कोर्स है। आपके ब्लॉक छजलैट में ITI एक्सटेंशन केंद्र में बैच स्वीकृत है।',
      audio_explanation_script: 'नमस्ते राजेश! छजलैट में ही आपके गांव के पास दोपहिया मैकेनिक का सरकारी बैच 20 नवंबर से शुरू हो रहा है।',
      tradeoff_summary: 'वर्कशॉप में अच्छी पगार या खुद का सर्विस सेंटर खोलने की पूरी आजादी।',
      skill_gap_summary: 'हेल्पर से कुशल डायग्नोस्टिक तकनीशियन बनने हेतु 12 सप्ताह की प्रैक्टिकल ट्रेनिंग।',
      data_snapshot: { qualification: bikeQual, opportunity: chhajletBike, timestamp: new Date().toISOString() },
    },
    {
      session_id: undefined,
      qualification_id: electricianQual.id,
      local_opportunity_id: rsetiElectrician.id,
      rank: 2,
      score: 78,
      score_breakdown: { interest: 20, prior_skills: 15, access: 15, local_demand: 18, work_preference: 10 },
      match_state: 'Verified Match',
      explanation_text: 'Assistant Electrician का विकल्प भी अच्छा है, जिसमें हॉस्टल की सुविधा उपलब्ध है।',
      audio_explanation_script: 'बिजली मिस्त्री का कोर्स भी जिला केंद्र में उपलब्ध है।',
      tradeoff_summary: 'घरेलू वायरिंग और मोटर रिपेयर में निरंतर आय।',
      skill_gap_summary: '10 सप्ताह का व्यावहारिक कोर्स।',
      data_snapshot: { qualification: electricianQual, opportunity: rsetiElectrician, timestamp: new Date().toISOString() },
    },
  ]);

  // 5. Beneficiary 3: Bahjoi SC youth showcasing the Planning Gap (Claim 2: Micro-Irrigation / Agro-Processing, NO live local centre!)
  const amit = await benRepo.create({
    id: 'ben_amit_bahjoi',
    name: 'Amit Kumar',
    phone: '9876543212',
    gender: 'male',
    age: 21,
    category: 'SC',
    preferred_language: 'hi',
    district: 'Moradabad',
    block: 'Bahjoi',
    village: 'Bahjoi Dehat',
    contact_preference: 'voice',
  });

  await sessionRepo.saveProfileAnswer({ beneficiaryId: amit.id, fieldName: 'education_level', fieldValue: 'Class 10', confidenceScore: 0.95, confirmationStatus: 'confirmed' });
  await sessionRepo.saveProfileAnswer({ beneficiaryId: amit.id, fieldName: 'interests', fieldValue: JSON.stringify(['Micro-Irrigation', 'Agri-Tech', 'Agro-processing']), confidenceScore: 0.95, confirmationStatus: 'confirmed' });
  await sessionRepo.saveProfileAnswer({ beneficiaryId: amit.id, fieldName: 'skills', fieldValue: JSON.stringify(['Farm Machinery']), confidenceScore: 0.85, confirmationStatus: 'confirmed' });
  await sessionRepo.saveProfileAnswer({ beneficiaryId: amit.id, fieldName: 'mobility_radius_km', fieldValue: '10', confidenceScore: 0.90, confirmationStatus: 'confirmed' });
  await sessionRepo.saveProfileAnswer({ beneficiaryId: amit.id, fieldName: 'work_preference', fieldValue: 'wage', confidenceScore: 0.90, confirmationStatus: 'confirmed' });

  // Recommendations for Amit: STRICT Interest Match because nearest sanctioned centre is 45km away!
  await recRepo.saveRecommendations(amit.id, undefined, [
    {
      session_id: undefined,
      qualification_id: irrigationQual.id,
      local_opportunity_id: null,
      rank: 1,
      score: 74,
      score_breakdown: { interest: 30, prior_skills: 18, access: 4, local_demand: 4, work_preference: 10 },
      match_state: 'Interest Match', // Claim 1 enforced: No local batch verified in Bahjoi
      explanation_text: 'आपकी रुचि आधुनिक सिंचाई और कृषि तकनीकों में है, जिसके लिए "Micro-Irrigation Technician" अत्यंत उपयुक्त है। कृपया ध्यान दें: बहजोई ब्लॉक में वर्तमान में इसका कोई स्थानीय बैच स्वीकृत नहीं है।',
      audio_explanation_script: 'अमित जी, माइक्रो-इरीगेशन का कोर्स NQR में पंजीकृत है, लेकिन बहजोई ब्लॉक में इसका बैच अभी स्वीकृत नहीं है। यह मांग जिला योजना अधिकारी के पास दर्ज कर ली गई है।',
      tradeoff_summary: 'कृषि कंपनियों में नियमित वेतन, लेकिन स्थानीय स्तर पर मोबाइल ट्रेनिंग यूनिट की आवश्यकता।',
      skill_gap_summary: 'ड्रिप और स्प्रिंकलर असेंबली हेतु 6 सप्ताह का कोर्स।',
      data_snapshot: { qualification: irrigationQual, opportunity: null, timestamp: new Date().toISOString() },
    },
  ]);

  logger.info('Database seeded successfully with realistic PM-AJAY operational data.');
}

// Run directly if called as a script
if (process.argv[1]?.endsWith('seed.ts') || process.argv[1]?.endsWith('seed.js')) {
  seedDatabase().catch(console.error);
}
