import { PrismaClient } from '@prisma/client';
import fs from 'fs';
import path from 'path';

const prisma = new PrismaClient();

async function main() {
  const seedPath = path.resolve(process.cwd(), 'data', 'nqr_sample.json');
  if (!fs.existsSync(seedPath)) {
    console.error(`Seed file not found at ${seedPath}`);
    process.exit(1);
  }

  const data = JSON.parse(fs.readFileSync(seedPath, 'utf8'));

  console.log(`Seeding ${data.length} qualifications...`);

  for (const item of data) {
    await prisma.qualification.upsert({
      where: { nqr_code: item.nqr_code },
      update: {},
      create: {
        id: item.id,
        nqr_code: item.nqr_code,
        title: item.title,
        sector: item.sector,
        nsqf_level: item.nsqf_level,
        duration_hours: item.duration_hours,
        min_education: item.min_education,
        min_education_rank: item.min_education_rank,
        work_type: item.work_type,
        physical_intensity: item.physical_intensity || 'light',
        skills_acquired: JSON.stringify(item.skills_acquired),
        curriculum_summary: item.curriculum_summary,
        entry_criteria: item.entry_criteria,
        certification_body: item.certification_body,
        nqr_link: item.nqr_link,
        verification_status: 'verified',
        verification_date: new Date(),
      },
    });
  }

  console.log('Seeding complete.');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
