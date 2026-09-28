import type { BeneficiaryProfile, RecommendationCard, JobOpportunity, TrainingLesson, QuizQuestion, CareerNode, FinancialScheme, Mentor } from '../types';

export const initialProfile: BeneficiaryProfile = {
  name: 'Rajesh Kumar',
  age: 22,
  gender: 'Male',
  district: 'Moradabad',
  village: 'Chhajlet',
  education: '10th Pass',
  aspiration: 'Agri-Business & Enterprise',
  familyTrades: ['Farming', 'Pottery', 'Livestock'],
  travelRadiusKm: 5,
  workPreference: 'Both',
  skills: [
    { name: 'Crop & Agri Knowledge', level: 'High', score: 88 },
    { name: 'Handicrafts & Pottery', level: 'High', score: 82 },
    { name: 'Mechanical & Tool Handling', level: 'Med', score: 62 },
    { name: 'Customer Communication', level: 'Med', score: 58 },
    { name: 'Digital & Financial Accounts', level: 'Low', score: 34 }
  ],
  nsqfLevel: 2,
  targetNsqfLevel: 4
};

export const recommendationsData: RecommendationCard[] = [
  {
    id: 'mushroom-cultivation',
    title: 'Mushroom Cultivation',
    type: 'self',
    category: 'Agri-Business & Micro-Enterprise',
    description: 'Commercial button and oyster mushroom production with climate-controlled spawn bags.',
    duration: '3 Months',
    location: 'Nearest Skilling Center, Chhajlet',
    distanceKm: 4.2,
    mode: 'Voice / In-person Hybrid',
    stipend: '₹1,500 / month',
    nsqfLevel: 4,
    demandStatus: 'Verified Batch',
    batchConfirmed: true,
    matchReason: 'Matches family farming background and 5km local radius.',
    iconName: 'mushroom',
    modulesCount: 6
  },
  {
    id: 'small-retail-shop',
    title: 'Small Retail Shop',
    type: 'self',
    category: 'Retail & Entrepreneurship',
    description: 'Inventory management, POS digital payments, and FMCG retail for rural marketplaces.',
    duration: '2 Months',
    location: 'District Skill Training Hub, Moradabad',
    distanceKm: 4.8,
    mode: 'In-person & Voice Modules',
    stipend: '₹1,500 / month',
    nsqfLevel: 3,
    demandStatus: 'High Demand',
    batchConfirmed: true,
    matchReason: 'High local footfall in weekly haat and local village cluster.',
    iconName: 'shop',
    modulesCount: 5
  },
  {
    id: 'solar-technician',
    title: 'Solar Technician',
    type: 'wage',
    category: 'Renewable Energy',
    description: 'Rooftop solar panel installation, inverter maintenance under PM Surya Ghar Yojana.',
    duration: '4 Months',
    location: 'Govt ITI Moradabad Centre',
    distanceKm: 5.0,
    mode: 'Practical Hands-on',
    stipend: '₹2,000 / month',
    nsqfLevel: 4,
    demandStatus: 'High Demand',
    batchConfirmed: true,
    matchReason: '300+ installations planned under district renewable energy scheme.',
    iconName: 'solar',
    modulesCount: 8
  },
  {
    id: 'apparel-maker',
    title: 'Apparel Maker',
    type: 'wage',
    category: 'Textile & Garments',
    description: 'Industrial sewing machine operations and quality inspection for garment clusters.',
    duration: '3 Months',
    location: 'Apparel Training & Design Centre',
    distanceKm: 3.5,
    mode: 'Classroom & Factory Floor',
    stipend: '₹1,800 / month',
    nsqfLevel: 3,
    demandStatus: 'Verified Batch',
    batchConfirmed: true,
    matchReason: 'Direct placement tie-up with Moradabad textile exporters.',
    iconName: 'sewing',
    modulesCount: 6
  }
];

export const mushroomModules: TrainingLesson[] = [
  {
    id: 'lesson-1',
    title: 'Soil & Compost with Medium Content',
    duration: '12 mins audio',
    description: 'Substrate sterilization, wheat straw preparation, and gypsum balance.',
    icon: 'soil',
    audioPrompt: 'Learn how to sterilize agricultural waste and mix straw with proper nitrogen supplements.',
    completed: true
  },
  {
    id: 'lesson-2',
    title: 'Water & Moisture Content',
    duration: '15 mins audio',
    description: 'Maintaining 75-85% relative humidity and mist spraying techniques.',
    icon: 'water',
    audioPrompt: 'Discover precise misting schedules without drenching mushroom mycelium pinheads.',
    completed: false
  },
  {
    id: 'lesson-3',
    title: 'Temperature Controls & Ventilation',
    duration: '10 mins audio',
    description: 'Regulating growing chamber temperature between 20°C and 25°C.',
    icon: 'temp',
    audioPrompt: 'Understand how airflow and temperature regulate fruiting body formation.',
    completed: false
  }
];

export const mushroomQuiz: QuizQuestion[] = [
  {
    id: 'q1',
    question: 'What is the optimal humidity level required during the mushroom pinhead fruiting stage?',
    questionHi: 'मशरूम के पिनहेड फलने के दौरान आवश्यक नमी (Humidity) का स्तर क्या होना चाहिए?',
    options: [
      {
        key: 'A',
        text: 'Maintain 75% to 85% relative humidity with light misting',
        textHi: '75% से 85% नमी हल्की फुहार के साथ बनाए रखें',
        isCorrect: true
      },
      {
        key: 'B',
        text: 'Keep completely dry below 20% humidity',
        textHi: '20% से कम नमी में बिल्कुल सूखा रखें',
        isCorrect: false
      },
      {
        key: 'C',
        text: 'Submerge the grow bags in direct standing water',
        textHi: 'बैग को सीधे पानी में डुबोकर रखें',
        isCorrect: false
      }
    ],
    explanation: 'Mushrooms require high ambient humidity (75-85%) for pinheads to develop into healthy caps without drying out.'
  },
  {
    id: 'q2',
    question: 'How should straw substrate be sterilized before spawning?',
    questionHi: 'स्पॉनिंग से पहले भूसे (Substrate) को कैसे निष्फल (Sterilize) करना चाहिए?',
    options: [
      {
        key: 'A',
        text: 'Wash with cold river water only',
        textHi: 'केवल ठंडे नदी के पानी से धोएं',
        isCorrect: false
      },
      {
        key: 'B',
        text: 'Boil or steam treat at 80°C for 60-90 minutes',
        textHi: '80°C पर 60-90 मिनट तक भाप या उबालकर उपचार करें',
        isCorrect: true
      },
      {
        key: 'C',
        text: 'Leave unwashed in direct sunlight for 5 minutes',
        textHi: 'बिना धोए 5 मिनट धूप में छोड़ दें',
        isCorrect: false
      }
    ],
    explanation: 'Heat sterilization eliminates competing mold spores and bacterial contaminants.'
  }
];

export const jobOpportunitiesData: JobOpportunity[] = [
  {
    id: 'job-1',
    title: 'Sales Associate',
    company: 'Big Basket Hub',
    sector: 'Retail',
    wage: '₹14,000 / mo',
    location: 'Civil Lines, Moradabad',
    distanceKm: 3.0,
    coordinates: { x: 42, y: 38 },
    type: 'Full-Time',
    vacancies: 6,
    description: 'Assist walk-in B2B buyers, barcode scan incoming grocery shipments, manage inventory stock.',
    requirements: ['10th Pass or equivalent', 'Basic Hindi literacy', 'Friendly demeanor']
  },
  {
    id: 'job-2',
    title: 'Delivery Executive',
    company: 'Swiggy Instamart',
    sector: 'Logistics',
    wage: '₹18,000 / mo + Incentives',
    location: 'Rampur Road Hub, Moradabad',
    distanceKm: 2.1,
    coordinates: { x: 58, y: 52 },
    type: 'Full-Time',
    vacancies: 12,
    description: 'Fast hyper-local package and grocery deliveries within a 4 km service radius.',
    requirements: ['Own two-wheeler / EV or bicycle', 'Valid Driving License / Aadhaar', 'Smartphone usage']
  },
  {
    id: 'job-3',
    title: 'Field Sales Assistant',
    company: 'Kisan Agri-Coop Centre',
    sector: 'Agriculture',
    wage: '₹15,000 / mo',
    location: 'Chhajlet Mandi Road',
    distanceKm: 5.0,
    coordinates: { x: 30, y: 64 },
    type: 'Full-Time',
    vacancies: 4,
    description: 'Distribute organic fertilizers, micro-irrigation kits, and book mushroom spawn orders with local growers.',
    requirements: ['Farming background', 'Good communication in local dialect', 'Basic arithmetic']
  },
  {
    id: 'job-4',
    title: 'Rooftop Solar Assistant',
    company: 'Urja Vikas CleanTech',
    sector: 'Technical',
    wage: '₹16,500 / mo',
    location: 'Industrial Area, Moradabad',
    distanceKm: 4.5,
    coordinates: { x: 70, y: 30 },
    type: 'Full-Time',
    vacancies: 8,
    description: 'Assist senior technicians in panel rail mounting, solar cable crimping, and earthing pit setups.',
    requirements: ['NSQF Level 3 or 4 Solar / ITI preferred', 'Physical fitness for rooftop safety']
  }
];

export const careerPathwaysData: CareerNode[] = [
  // Pathway 1: Retail
  {
    id: 'retail-1',
    title: 'Sales Associate',
    pathway: 'Retail',
    level: 'NSQF Level 3',
    experienceYears: '0 - 1 Year',
    avgSalary: '₹1.5L - ₹2.2L / yr',
    keySkills: ['Customer greeting', 'Stock arranging', 'POS billing'],
    certifications: ['RASCI Retail Sales Certificate'],
    avatar: '👨‍💼',
    description: 'Entry role handling direct retail sales, customer queries, and cash register.',
    govtSupport: '100% PM-AJAY subsidized skilling with ₹1,500 stipend.'
  },
  {
    id: 'retail-2',
    title: 'Store Manager',
    pathway: 'Retail',
    level: 'NSQF Level 5',
    experienceYears: '2 - 4 Years',
    avgSalary: '₹3.6L - ₹4.8L / yr',
    keySkills: ['Staff supervision', 'Shrinkage control', 'P&L reporting'],
    certifications: ['Diploma in Retail Store Operations'],
    avatar: '🧑‍💼',
    description: 'Oversees day-to-day outlet operations, shift scheduling, and inventory audits.',
    govtSupport: 'Upskilling through RPL (Recognition of Prior Learning).'
  },
  {
    id: 'retail-3',
    title: 'Regional Manager',
    pathway: 'Retail',
    level: 'NSQF Level 7',
    experienceYears: '5+ Years',
    avgSalary: '₹7.0L - ₹10.0L / yr',
    keySkills: ['Cluster logistics', 'Vendor contracting', 'Expansion strategy'],
    certifications: ['Executive Retail Leadership'],
    avatar: '👔',
    description: 'Directs multi-store performance across 3 to 5 districts.',
    govtSupport: 'Corporate CSR partnership & leadership sponsorship.'
  },

  // Pathway 2: Agri
  {
    id: 'agri-1',
    title: 'Cold Storage Supervisor',
    pathway: 'Agri',
    level: 'NSQF Level 3',
    experienceYears: '0 - 2 Years',
    avgSalary: '₹1.8L - ₹2.6L / yr',
    keySkills: ['Temperature logging', 'Crate handling', 'Pre-cooling checks'],
    certifications: ['Agri-Skill Council Post-Harvest Specialist'],
    avatar: '👷‍♂️',
    description: 'Monitors cold storage chambers for perishables, mushrooms, and fruits.',
    govtSupport: 'PM-AJAY GIA skill sponsorship & tool-kit grant.'
  },
  {
    id: 'agri-2',
    title: 'Cold Chain Manager',
    pathway: 'Agri',
    level: 'NSQF Level 4',
    experienceYears: '3 - 5 Years',
    avgSalary: '₹3.8L - ₹5.5L / yr',
    keySkills: ['Reefer fleet routing', 'HACCP quality standards', 'Cold-chain IoT'],
    certifications: ['Advanced Cold Chain Logistics Professional'],
    avatar: '👨‍🌾',
    description: 'Manages refrigerated farm-to-mandi transport logistics and quality compliance.',
    govtSupport: 'National Horticulture Mission subsidy assistance.'
  },
  {
    id: 'agri-3',
    title: 'Agri Export Manager',
    pathway: 'Agri',
    level: 'NSQF Level 6',
    experienceYears: '6+ Years',
    avgSalary: '₹8.0L - ₹12.0L / yr',
    keySkills: ['APEDA export protocols', 'Organic certification', 'Cross-border trade'],
    certifications: ['APEDA Certified Exporter Credentials'],
    avatar: '🌾',
    description: 'Leads agricultural export contracts and global distributor partnerships.',
    govtSupport: 'Ministry of Commerce APEDA export grant scheme.'
  },

  // Pathway 3: Enterprise
  {
    id: 'ent-1',
    title: 'Micro-Business Owner',
    pathway: 'Enterprise',
    level: 'NSQF Level 4',
    experienceYears: '1 - 2 Years',
    avgSalary: '₹2.4L - ₹4.0L profit / yr',
    keySkills: ['Spawn cultivation', 'Packaging & brand labeling', 'Local mandi sales'],
    certifications: ['PM-AJAY Certified Micro-Entrepreneur'],
    avatar: '🧑‍🌾',
    description: 'Runs an independent mushroom cultivation or agro-processing shed with 4 workers.',
    govtSupport: '₹50,000 Seed Grant + 35% MUDRA subsidy.'
  },
  {
    id: 'ent-2',
    title: 'Franchisor / Cluster Lead',
    pathway: 'Enterprise',
    level: 'NSQF Level 5',
    experienceYears: '3 - 5 Years',
    avgSalary: '₹5.5L - ₹8.5L / yr',
    keySkills: ['Grower aggregation', 'Bulk substrate supply', 'Cold room pooling'],
    certifications: ['FPO / Farmer Producer Company Management'],
    avatar: '🏭',
    description: 'Creates a cluster cooperative aggregating 25+ local SC mushroom growers.',
    govtSupport: 'SFAC Equity Grant + PM-AJAY Common Facility Centre funding.'
  },
  {
    id: 'ent-3',
    title: 'Agri-Business Leader',
    pathway: 'Enterprise',
    level: 'NSQF Level 7',
    experienceYears: '6+ Years',
    avgSalary: '₹12.0L+ / yr',
    keySkills: ['Brand distribution', 'Modern trade tie-ups', 'Processing plant setup'],
    certifications: ['Enterprise Board Leadership'],
    avatar: '🌟',
    description: 'Directs a regional brand supplying packaged mushrooms & dried agro-products nationwide.',
    govtSupport: 'Venture Capital Fund for Scheduled Castes (IFCI/MoSJE).'
  }
];

export const financialSchemesData: FinancialScheme[] = [
  {
    id: 'mudra-loan',
    title: 'MUDRA Loan Support (Shishu / Kishor)',
    subtitle: 'Pradhan Mantri MUDRA Yojana for Micro-Units',
    badge: 'PM-AJAY Subsidized',
    maxAmount: 'Up to ₹5,00,000',
    subsidyRate: '35% Capital Subsidy for SC Beneficiaries',
    description: 'Collateral-free institutional credit to purchase mushroom grow racks, dehumidifiers, spawn, and packaging machines.',
    eligibility: [
      'Belongs to Scheduled Caste (Aadhaar / Caste Certificate)',
      'Completed NSQF Skill Training Course',
      'Viable micro-business project plan'
    ],
    documents: ['Aadhaar Card', 'SC Certificate', 'Bank Passbook', 'Course Completion Certificate'],
    status: 'Fast-Track'
  },
  {
    id: 'startup-community-fund',
    title: 'Startup Community Fund & GIA Grant',
    subtitle: 'PM-AJAY Micro-Enterprise Development Assistance',
    badge: '100% Grant Support',
    maxAmount: '₹50,000 to ₹2,00,000 Seed Grant',
    subsidyRate: 'Zero Repayment (Direct Benefit Transfer)',
    description: 'Direct capital grant from MoSJE for self-employment setups, equipment kits, and working capital for first 3 production cycles.',
    eligibility: [
      'Annual family income within PM-AJAY poverty guidelines',
      'Passed verification by designated Field-Worker',
      'Individual or Self-Help Group (SHG) formation'
    ],
    documents: ['Ration Card / Income Affidavit', 'Field Worker Verification Slip', 'Village Panchayat NOC'],
    status: 'Open'
  }
];

export const mentorsData: Mentor[] = [
  {
    id: 'mentor-1',
    name: 'Sunita Devi',
    role: 'Agri-Tech & Mushroom Expert',
    experience: '8 Years Field Experience',
    location: 'Chhajlet, Moradabad',
    specialization: 'Oyster & Milky Mushroom Cultivation, Spawning Techniques',
    rating: 4.9,
    sessionsCompleted: 142,
    avatar: '👩‍🌾',
    bio: 'Pioneered organic mushroom farming across 6 villages. Trained over 300 women and youth into viable home enterprises.',
    languages: ['Hindi', 'Bhojpuri'],
    availableToday: true
  },
  {
    id: 'mentor-2',
    name: 'Rameshwar Sharma',
    role: 'Retail & FMCG Mentor',
    experience: '15 Years Enterprise Experience',
    location: 'Station Road, Moradabad',
    specialization: 'Store Setup, POS Digital Accounting, FMCG Wholesale Deals',
    rating: 4.8,
    sessionsCompleted: 218,
    avatar: '👨‍🦳',
    bio: 'Runs 3 thriving retail supermarkets and helps young PM-AJAY entrepreneurs negotiate wholesale supplier rates.',
    languages: ['Hindi', 'English'],
    availableToday: true
  },
  {
    id: 'mentor-3',
    name: 'Mahendra Ram',
    role: 'Panchayat & Community Leader',
    experience: '12 Years Social Leadership',
    location: 'Bahjoi Cluster',
    specialization: 'Govt Scheme Facilitation, Mudra Application, Land Lease',
    rating: 4.9,
    sessionsCompleted: 305,
    avatar: '👴',
    bio: 'Dedicated community elder assisting SC youth in securing training certificates, caste documentation, and bank loans.',
    languages: ['Hindi'],
    availableToday: false
  }
];

export const voiceFAQData = [
  {
    id: 'faq-1',
    en: 'What is the stipend provided?',
    hi: 'कितनी वजीफा राशि मिलती है?',
    answer: 'Under PM-AJAY GIA, beneficiaries receive ₹1,500 to ₹2,000 per month direct into their bank account during training.',
    answerHi: 'PM-AJAY योजना के तहत प्रशिक्षण के दौरान ₹1,500 से ₹2,000 प्रति माह सीधे आपके बैंक खाते में मिलते हैं।'
  },
  {
    id: 'faq-2',
    en: 'Is transport assistance provided?',
    hi: 'क्या आने-जाने का किराया मिलेगा?',
    answer: 'Yes! For centers beyond 3 km, daily travel reimbursement of ₹50/day or free transport pass is arranged by the district office.',
    answerHi: 'हाँ! 3 किमी से अधिक दूरी के केंद्रों के लिए ₹50 प्रतिदिन का यात्रा भत्ता या निःशुल्क पास उपलब्ध कराया जाता है।'
  },
  {
    id: 'faq-3',
    en: 'Can I work part-time while learning?',
    hi: 'क्या पार्ट-टाइम काम कर सकते हैं?',
    answer: 'Yes, training batches are scheduled in morning (8am-12pm) or afternoon shifts so you can continue family farming or part-time work.',
    answerHi: 'हाँ, सुबह या दोपहर की पाली में कक्षाएं होती हैं ताकि आप अपने परिवार का काम या पार्ट-टाइम काम भी जारी रख सकें।'
  },
  {
    id: 'faq-4',
    en: 'Will I get an official government certificate?',
    hi: 'क्या सरकारी प्रमाण पत्र मिलेगा?',
    answer: 'Yes, you receive an NCVET & Skill India NSQF Level 4 Government certificate recognized by employers nationwide.',
    answerHi: 'हाँ, आपको NCVET और Skill India द्वारा मान्यता प्राप्त NSQF लेवल 4 का सरकारी सर्टिफिकेट मिलेगा।'
  }
];
