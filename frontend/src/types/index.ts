export type Language = 'hi' | 'en' | 'ta' | 'bn' | 'te';

export interface BeneficiaryProfile {
  name: string;
  age: number;
  gender: string;
  district: string;
  village: string;
  education: string;
  aspiration: string;
  familyTrades: string[];
  travelRadiusKm: number;
  workPreference: 'Self-Employment' | 'Wage Employment' | 'Both';
  skills: {
    name: string;
    level: 'Low' | 'Med' | 'High';
    score: number;
  }[];
  nsqfLevel: number;
  targetNsqfLevel: number;
}

export interface RecommendationCard {
  id: string;
  title: string;
  type: 'self' | 'wage';
  category: string;
  description: string;
  duration: string;
  location: string;
  distanceKm: number;
  mode: string;
  stipend?: string;
  nsqfLevel: number;
  demandStatus: 'High Demand' | 'Verified Batch' | 'Emerging' | 'Waitlist';
  batchConfirmed: boolean;
  matchReason: string;
  iconName: string;
  modulesCount: number;
}

export interface JobOpportunity {
  id: string;
  title: string;
  company: string;
  sector: 'Retail' | 'Logistics' | 'Agriculture' | 'Technical';
  wage: string;
  location: string;
  distanceKm: number;
  coordinates: { x: number; y: number }; // Percentage for map display
  type: 'Full-Time' | 'Part-Time' | 'Apprenticeship';
  vacancies: number;
  description: string;
  requirements: string[];
  applied?: boolean;
}

export interface TrainingLesson {
  id: string;
  title: string;
  duration: string;
  description: string;
  icon: string;
  audioPrompt: string;
  completed: boolean;
}

export interface QuizQuestion {
  id: string;
  question: string;
  questionHi: string;
  options: {
    key: string;
    text: string;
    textHi: string;
    isCorrect: boolean;
  }[];
  explanation: string;
}

export interface CareerNode {
  id: string;
  title: string;
  pathway: 'Retail' | 'Agri' | 'Enterprise';
  level: string; // e.g. "NSQF Level 3"
  experienceYears: string;
  avgSalary: string;
  keySkills: string[];
  certifications: string[];
  avatar: string;
  description: string;
  govtSupport: string;
}

export interface FinancialScheme {
  id: string;
  title: string;
  subtitle: string;
  badge: string;
  maxAmount: string;
  subsidyRate: string;
  description: string;
  eligibility: string[];
  documents: string[];
  status: 'Open' | 'Fast-Track' | 'Review Required';
}

export interface Mentor {
  id: string;
  name: string;
  role: string;
  experience: string;
  location: string;
  specialization: string;
  rating: number;
  sessionsCompleted: number;
  avatar: string;
  bio: string;
  languages: string[];
  availableToday: boolean;
}
