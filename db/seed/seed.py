"""Seed script for Green Valley Hospital.

Populates db/green_valley.db with one demo account per role (Admin, Doctor,
Patient, Staff, Lab) with known credentials that satisfy the password policy
(SEC-1: min 8 chars, at least one letter and one number — see
docs/requirements.md §3.2), plus a few demo departments, doctor profiles, a
staff profile, a lab technician profile, upcoming appointments, and published
blog articles so the app isn't empty on first load.

v1.1 update (Section 6 visual requirements): doctors now carry a
profile_photo_path pointing to /images/doctors/<slug>.jpg — these static files
are served by Vite's public directory (VI-IMG-3) and do not require any backend
endpoint. Additional departments and doctors are seeded so the home page
"Meet Our Specialists" teaser and featured departments sections have real data.

Idempotent: safe to re-run. Each insert is guarded by a "does this already
exist" check (by unique email / unique name / unique slug), so running this
script twice will not create duplicates or raise integrity errors.

Usage (from repo root, with the backend venv active or referenced directly):
    src/backend/venv/Scripts/python.exe db/seed/seed.py
or:
    cd src/backend && venv\\Scripts\\python.exe ..\\..\\db\\seed\\seed.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Make the backend app package importable regardless of cwd.
BACKEND_DIR = Path(__file__).resolve().parents[2] / "src" / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal, init_db  # noqa: E402
from app.models import (  # noqa: E402
    BlogArticle,
    BillingSpecialist,
    CorporatePackage,
    Department,
    Doctor,
    LabTechnician,
    Patient,
    StaffMember,
    SystemConfig,
    User,
    Appointment,
)
from app.security import hash_password  # noqa: E402

# Demo credentials — meet SEC-1 (>=8 chars, letter + number).
DEMO_USERS = [
    {
        "email": "admin@greenvalleyhospital.com",
        "password": "Admin123!",
        "role": "Admin",
        "full_name": "Alice Admin",
        "phone": "555-0100",
    },
    {
        "email": "doctor@greenvalleyhospital.com",
        "password": "Doctor123!",
        "role": "Doctor",
        "full_name": "Dr. David Heart",
        "phone": "555-0101",
    },
    {
        "email": "patient@greenvalleyhospital.com",
        "password": "Patient123!",
        "role": "Patient",
        "full_name": "Pat Patient",
        "phone": "555-0102",
    },
    {
        "email": "staff@greenvalleyhospital.com",
        "password": "Staff123!",
        "role": "Staff",
        "full_name": "Sam Staff",
        "phone": "555-0103",
    },
    {
        "email": "lab@greenvalleyhospital.com",
        "password": "Lab123!",
        "role": "Lab",
        "full_name": "Lee Lab",
        "phone": "555-0104",
    },
    {
        "email": "billing@greenvalleyhospital.com",
        "password": "Billing123!",
        "role": "BillingSpecialist",
        "full_name": "Bill Billing",
        "phone": "555-0105",
    },
]

# Additional doctor demo users (multi-department coverage for home page teaser).
EXTRA_DOCTOR_USERS = [
    {
        "email": "dr.patel@greenvalleyhospital.com",
        "password": "Doctor123!",
        "role": "Doctor",
        "full_name": "Dr. Priya Patel",
        "phone": "555-0201",
    },
    {
        "email": "dr.nguyen@greenvalleyhospital.com",
        "password": "Doctor123!",
        "role": "Doctor",
        "full_name": "Dr. James Nguyen",
        "phone": "555-0202",
    },
    {
        "email": "dr.martinez@greenvalleyhospital.com",
        "password": "Doctor123!",
        "role": "Doctor",
        "full_name": "Dr. Sofia Martinez",
        "phone": "555-0203",
    },
    {
        "email": "dr.chen@greenvalleyhospital.com",
        "password": "Doctor123!",
        "role": "Doctor",
        "full_name": "Dr. Michael Chen",
        "phone": "555-0204",
    },
    {
        "email": "dr.singh@greenvalleyhospital.com",
        "password": "Doctor123!",
        "role": "Doctor",
        "full_name": "Dr. Anjali Singh",
        "phone": "555-0205",
    },
    {
        "email": "dr.brown@greenvalleyhospital.com",
        "password": "Doctor123!",
        "role": "Doctor",
        "full_name": "Dr. Marcus Brown",
        "phone": "555-0206",
    },
    {
        "email": "dr.kim@greenvalleyhospital.com",
        "password": "Doctor123!",
        "role": "Doctor",
        "full_name": "Dr. Grace Kim",
        "phone": "555-0207",
    },
    {
        "email": "dr.rodriguez@greenvalleyhospital.com",
        "password": "Doctor123!",
        "role": "Doctor",
        "full_name": "Dr. Elena Rodriguez",
        "phone": "555-0208",
    },
    {
        "email": "dr.osei@greenvalleyhospital.com",
        "password": "Doctor123!",
        "role": "Doctor",
        "full_name": "Dr. Kwame Osei",
        "phone": "555-0209",
    },
]

DEMO_DEPARTMENTS = [
    {"name": "Cardiology", "description": "Heart and cardiovascular care."},
    {"name": "Pediatrics", "description": "Medical care for infants, children, and adolescents."},
    {"name": "Orthopedics", "description": "Musculoskeletal system: bones, joints, ligaments."},
    {"name": "Neurology", "description": "Disorders of the nervous system and brain."},
    {
        "name": "Oncology",
        "description": "Comprehensive cancer screening, diagnosis, and treatment, including chemotherapy and survivorship support.",
    },
    {
        "name": "Radiology",
        "description": "Advanced diagnostic imaging including X-ray, CT, MRI, and ultrasound for accurate, timely diagnosis.",
    },
    {
        "name": "Emergency Medicine",
        "description": "24/7 emergency and trauma care with rapid-response teams and a fully equipped resuscitation unit.",
    },
    {
        "name": "Ophthalmology",
        "description": "Complete eye care from routine vision exams to advanced cataract and retinal surgery.",
    },
    {
        "name": "Gynecology",
        "description": "Women's health services spanning prenatal care, minimally invasive surgery, and reproductive wellness.",
    },
    {
        "name": "Dermatology",
        "description": "Diagnosis and treatment of skin, hair, and nail conditions, plus cosmetic and surgical dermatology.",
    },
]

# Extra doctor profile details keyed by email.
# profile_photo_path values use the /images/doctors/ prefix; static files are
# placed in src/frontend/public/images/doctors/ and served by Vite (VI-IMG-3).
EXTRA_DOCTOR_PROFILES = {
    "dr.patel@greenvalleyhospital.com": {
        "department": "Pediatrics",
        "specialty": "Pediatrics",
        "qualifications": "MD, FAAP",
        "bio": "Award-winning pediatrician with 12 years of experience caring for children and adolescents.",
        "years_experience": 12,
        "consultation_hours": "Mon-Fri 8:00-15:00",
        "profile_photo_path": "/images/doctors/dr-patel.jpg",
    },
    "dr.nguyen@greenvalleyhospital.com": {
        "department": "Orthopedics",
        "specialty": "Orthopedic Surgery",
        "qualifications": "MD, FAAOS",
        "bio": "Specialist in joint replacement and sports medicine with 18 years of surgical experience.",
        "years_experience": 18,
        "consultation_hours": "Tue-Sat 9:00-17:00",
        "profile_photo_path": "/images/doctors/dr-nguyen.jpg",
    },
    "dr.martinez@greenvalleyhospital.com": {
        "department": "Neurology",
        "specialty": "Neurology",
        "qualifications": "MD, PhD, FAAN",
        "bio": "Neurologist specializing in stroke, epilepsy, and headache disorders.",
        "years_experience": 10,
        "consultation_hours": "Mon-Thu 10:00-16:00",
        "profile_photo_path": "/images/doctors/dr-martinez.jpg",
    },
    "dr.chen@greenvalleyhospital.com": {
        "department": "Oncology",
        "specialty": "Medical Oncology",
        "qualifications": "MD, PhD, FASCO",
        "bio": "Medical oncologist focused on personalized cancer treatment plans and clinical trial research.",
        "years_experience": 14,
        "consultation_hours": "Mon-Fri 9:00-16:00",
        "profile_photo_path": "/images/doctors/dr-chen.jpg",
    },
    "dr.singh@greenvalleyhospital.com": {
        "department": "Radiology",
        "specialty": "Diagnostic Radiology",
        "qualifications": "MD, FRCR",
        "bio": "Diagnostic radiologist specializing in cross-sectional imaging and early cancer detection.",
        "years_experience": 11,
        "consultation_hours": "Mon-Sat 8:00-14:00",
        "profile_photo_path": "/images/doctors/dr-singh.jpg",
    },
    "dr.brown@greenvalleyhospital.com": {
        "department": "Emergency Medicine",
        "specialty": "Emergency Medicine",
        "qualifications": "MD, FACEP",
        "bio": "Emergency physician with extensive trauma and critical care experience in Level 1 trauma centers.",
        "years_experience": 16,
        "consultation_hours": "24/7 On-Call Rotation",
        "profile_photo_path": "/images/doctors/dr-brown.jpg",
    },
    "dr.kim@greenvalleyhospital.com": {
        "department": "Ophthalmology",
        "specialty": "Ophthalmology",
        "qualifications": "MD, FAAO",
        "bio": "Ophthalmic surgeon specializing in cataract surgery, glaucoma management, and retinal disorders.",
        "years_experience": 9,
        "consultation_hours": "Tue-Sat 9:00-15:00",
        "profile_photo_path": "/images/doctors/dr-kim.jpg",
    },
    "dr.rodriguez@greenvalleyhospital.com": {
        "department": "Gynecology",
        "specialty": "Obstetrics & Gynecology",
        "qualifications": "MD, FACOG",
        "bio": "OB/GYN specialist providing comprehensive women's health care from adolescence through menopause.",
        "years_experience": 13,
        "consultation_hours": "Mon-Fri 8:30-16:30",
        "profile_photo_path": "/images/doctors/dr-rodriguez.jpg",
    },
    "dr.osei@greenvalleyhospital.com": {
        "department": "Dermatology",
        "specialty": "Dermatology",
        "qualifications": "MD, FAAD",
        "bio": "Board-certified dermatologist treating medical, surgical, and cosmetic skin conditions for all ages.",
        "years_experience": 8,
        "consultation_hours": "Mon-Thu 9:00-17:00",
        "profile_photo_path": "/images/doctors/dr-osei.jpg",
    },
}

# Blog articles for the recent_articles section on the home page (VI-HOME-7).
EXTRA_ARTICLES = [
    {
        "slug": "heart-health-tips-2025",
        "title": "5 Heart Health Tips for a Longer Life",
        "summary": (
            "Cardiovascular disease remains the leading cause of death worldwide. "
            "Our cardiologists share five evidence-based lifestyle changes that can "
            "significantly reduce your risk."
        ),
        "body": (
            "1. Exercise regularly — aim for at least 150 minutes of moderate aerobic activity per week.\n"
            "2. Follow a heart-healthy diet rich in fruits, vegetables, and whole grains.\n"
            "3. Quit smoking — the single most impactful change you can make.\n"
            "4. Manage stress through mindfulness, yoga, or other relaxation techniques.\n"
            "5. Get regular check-ups to monitor blood pressure, cholesterol, and blood sugar."
        ),
        "cover_image_path": "/images/dept-cardiology.jpg",
    },
    {
        "slug": "children-vaccination-guide",
        "title": "The Complete Child Vaccination Guide",
        "summary": (
            "Vaccinations protect children from serious diseases. Our pediatrics team "
            "explains the recommended schedule, common questions, and what to expect."
        ),
        "body": (
            "Vaccination is one of the greatest public health achievements. "
            "The recommended childhood schedule includes vaccines for measles, mumps, rubella, "
            "polio, chickenpox, hepatitis B, and more. "
            "Talk to your pediatrician about any questions or concerns — our team is here to help."
        ),
        "cover_image_path": "/images/dept-pediatrics.jpg",
    },
    {
        "slug": "managing-back-pain-at-home",
        "title": "Managing Back Pain at Home: What Works",
        "summary": (
            "Back pain affects 80% of adults at some point. Learn which home remedies "
            "are actually effective, when to see a doctor, and how physiotherapy helps."
        ),
        "body": (
            "Most acute back pain resolves within a few weeks with self-care. "
            "Heat therapy, gentle stretching, and over-the-counter pain relievers are often effective. "
            "However, if pain persists beyond 6 weeks, radiates down your legs, or is accompanied by "
            "weakness or numbness, you should consult an orthopedic specialist promptly."
        ),
        "cover_image_path": "/images/dept-orthopedics.jpg",
    },
    {
        "slug": "cancer-screening-guidelines",
        "title": "Cancer Screening: What You Need at Every Age",
        "summary": (
            "Early detection saves lives. Our oncology team breaks down which cancer "
            "screenings are recommended at each life stage and why they matter."
        ),
        "body": (
            "Routine screening remains one of the most powerful tools against cancer. "
            "Adults should discuss mammograms, colonoscopies, Pap smears, and skin checks with "
            "their physician starting in their 20s and 30s, with frequency increasing with age and "
            "family history. Our oncology department offers same-week screening appointments and "
            "genetic counseling for patients with a family history of cancer. Catching disease early "
            "dramatically improves treatment outcomes and expands the range of available options."
        ),
        "cover_image_path": "/images/dept-oncology.jpg",
    },
    {
        "slug": "when-to-go-to-the-er",
        "title": "When to Go to the ER vs. Urgent Care",
        "summary": (
            "Chest pain, severe bleeding, or a sprained ankle — not every symptom needs the same "
            "level of care. Our emergency medicine team explains how to choose the right option."
        ),
        "body": (
            "Knowing where to seek care can save precious time in a real emergency. "
            "Go to the Emergency Room immediately for chest pain, difficulty breathing, signs of stroke "
            "(facial drooping, slurred speech, arm weakness), severe bleeding, or major trauma. "
            "Urgent care is appropriate for minor fractures, sprains, mild fevers, and infections that "
            "need same-day attention but aren't life-threatening. Green Valley's Emergency Department is "
            "staffed 24/7 with board-certified emergency physicians and a rapid-response trauma team."
        ),
        "cover_image_path": "/images/dept-emergency-medicine.jpg",
    },
    {
        "slug": "protecting-your-eyesight",
        "title": "Protecting Your Eyesight: Habits for Every Decade",
        "summary": (
            "From screen time to UV exposure, our ophthalmologists share simple daily habits "
            "that protect your vision for the long term."
        ),
        "body": (
            "Eye health is often overlooked until symptoms appear, but many of the most common "
            "conditions — glaucoma, cataracts, and macular degeneration — develop slowly and painlessly. "
            "Wear UV-protective sunglasses outdoors, follow the 20-20-20 rule during screen work (every "
            "20 minutes, look at something 20 feet away for 20 seconds), and schedule a comprehensive eye "
            "exam every one to two years, more frequently after age 40 or with a family history of eye "
            "disease. Our ophthalmology team offers same-day evaluations for sudden vision changes."
        ),
        "cover_image_path": "/images/dept-ophthalmology.jpg",
    },
    {
        "slug": "sun-safety-skin-health",
        "title": "Sun Safety and Everyday Skin Health",
        "summary": (
            "Skin cancer is the most common cancer in the world — and one of the most preventable. "
            "Our dermatology team shares practical daily sun-safety habits."
        ),
        "body": (
            "Daily sunscreen use, even on cloudy days, is the single most effective way to reduce your "
            "risk of skin cancer and premature aging. Choose a broad-spectrum SPF 30 or higher, reapply "
            "every two hours when outdoors, and wear protective clothing during peak UV hours (10am-4pm). "
            "Perform a monthly self-skin-check for new or changing moles using the ABCDE rule (Asymmetry, "
            "Border, Color, Diameter, Evolving), and see a dermatologist annually for a full-body skin exam, "
            "especially if you have fair skin, many moles, or a family history of skin cancer."
        ),
        "cover_image_path": "/images/dept-dermatology.jpg",
    },
]


def get_or_create_user(db, spec: dict) -> User:
    user = db.query(User).filter(User.email == spec["email"]).first()
    if user is not None:
        return user
    user = User(
        email=spec["email"],
        password_hash=hash_password(spec["password"]),
        role=spec["role"],
        full_name=spec["full_name"],
        phone=spec["phone"],
        is_active=1,
    )
    db.add(user)
    db.flush()
    return user


def get_or_create_department(db, spec: dict) -> Department:
    dept = db.query(Department).filter(Department.name == spec["name"]).first()
    if dept is not None:
        return dept
    dept = Department(name=spec["name"], description=spec["description"], is_active=1)
    db.add(dept)
    db.flush()
    return dept


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        # --- Departments ---
        departments = {d["name"]: get_or_create_department(db, d) for d in DEMO_DEPARTMENTS}
        db.commit()

        # --- Users + role profiles ---
        users_by_role = {spec["role"]: get_or_create_user(db, spec) for spec in DEMO_USERS}
        db.commit()

        admin_user = users_by_role["Admin"]
        doctor_user = users_by_role["Doctor"]
        patient_user = users_by_role["Patient"]
        staff_user = users_by_role["Staff"]
        lab_user = users_by_role["Lab"]
        billing_user = users_by_role["BillingSpecialist"]

        cardiology = departments["Cardiology"]

        patient_profile = db.query(Patient).filter(Patient.user_id == patient_user.id).first()
        if patient_profile is None:
            patient_profile = Patient(
                user_id=patient_user.id,
                date_of_birth="1990-05-14",
                gender="Other",
                address="123 Main St, Springfield",
                emergency_contact_name="Emma Emergency",
                emergency_contact_phone="555-0199",
            )
            db.add(patient_profile)
            db.flush()

        # Primary demo doctor — update profile_photo_path if column now exists.
        doctor_profile = db.query(Doctor).filter(Doctor.user_id == doctor_user.id).first()
        if doctor_profile is None:
            doctor_profile = Doctor(
                user_id=doctor_user.id,
                department_id=cardiology.department_id,
                specialty="Cardiology",
                qualifications="MD, FACC",
                bio="Board-certified cardiologist with 15 years of experience.",
                years_experience=15,
                consultation_hours="Mon-Fri 9:00-16:00",
                profile_photo_path="/images/doctors/dr-heart.jpg",
            )
            db.add(doctor_profile)
            db.flush()
        else:
            # Update existing record with photo path if not yet set.
            if not doctor_profile.profile_photo_path:
                doctor_profile.profile_photo_path = "/images/doctors/dr-heart.jpg"

        staff_profile = db.query(StaffMember).filter(StaffMember.user_id == staff_user.id).first()
        if staff_profile is None:
            staff_profile = StaffMember(user_id=staff_user.id, department_id=cardiology.department_id)
            db.add(staff_profile)
            db.flush()

        lab_profile = db.query(LabTechnician).filter(LabTechnician.user_id == lab_user.id).first()
        if lab_profile is None:
            lab_profile = LabTechnician(user_id=lab_user.id)
            db.add(lab_profile)
            db.flush()

        billing_profile = db.query(BillingSpecialist).filter(BillingSpecialist.user_id == billing_user.id).first()
        if billing_profile is None:
            billing_profile = BillingSpecialist(user_id=billing_user.id, employee_id="BILL-001")
            db.add(billing_profile)
            db.flush()

        db.commit()

        # --- Extra doctors (multi-department, with profile photos) ---
        for extra_spec in EXTRA_DOCTOR_USERS:
            extra_user = get_or_create_user(db, extra_spec)
            db.flush()
            profile_data = EXTRA_DOCTOR_PROFILES[extra_spec["email"]]
            dept = departments[profile_data["department"]]
            extra_doc = db.query(Doctor).filter(Doctor.user_id == extra_user.id).first()
            if extra_doc is None:
                extra_doc = Doctor(
                    user_id=extra_user.id,
                    department_id=dept.department_id,
                    specialty=profile_data["specialty"],
                    qualifications=profile_data["qualifications"],
                    bio=profile_data["bio"],
                    years_experience=profile_data["years_experience"],
                    consultation_hours=profile_data["consultation_hours"],
                    profile_photo_path=profile_data["profile_photo_path"],
                )
                db.add(extra_doc)
            else:
                if not extra_doc.profile_photo_path:
                    extra_doc.profile_photo_path = profile_data["profile_photo_path"]
        db.commit()

        # --- Demo appointment (Patient <-> Doctor), a few days in the future ---
        scheduled_at = (datetime.now(timezone.utc) + timedelta(days=3)).replace(
            minute=0, second=0, microsecond=0
        ).isoformat()
        existing_appt = (
            db.query(Appointment)
            .filter(
                Appointment.patient_id == patient_profile.patient_id,
                Appointment.doctor_id == doctor_profile.doctor_id,
            )
            .first()
        )
        if existing_appt is None:
            appt = Appointment(
                patient_id=patient_profile.patient_id,
                doctor_id=doctor_profile.doctor_id,
                scheduled_at=scheduled_at,
                status="Scheduled",
                reason="Routine cardiology checkup",
                created_by_user_id=patient_user.id,
            )
            db.add(appt)
            db.commit()

        # --- Demo published blog post (original) ---
        slug = "welcome-to-green-valley-hospital"
        article = db.query(BlogArticle).filter(BlogArticle.slug == slug).first()
        if article is None:
            article = BlogArticle(
                title="Welcome to Green Valley Hospital",
                slug=slug,
                summary="Learn about our departments, doctors, and how to book your first appointment.",
                body=(
                    "Green Valley Hospital is committed to providing compassionate, "
                    "high-quality care across Cardiology, Pediatrics, and Orthopedics. "
                    "Browse our departments, meet our doctors, and book an appointment "
                    "online in just a few clicks."
                ),
                author_user_id=admin_user.id,
                status="Published",
                published_at=datetime.now(timezone.utc).isoformat(),
            )
            db.add(article)
            db.commit()

        # --- Extra published blog articles (for recent_articles on home page, VI-HOME-7) ---
        base_published_at = datetime.now(timezone.utc)
        for i, art_spec in enumerate(EXTRA_ARTICLES):
            existing = db.query(BlogArticle).filter(BlogArticle.slug == art_spec["slug"]).first()
            if existing is None:
                # Offset timestamps so ordering is deterministic: newest first.
                published_ts = (base_published_at - timedelta(days=i + 1)).isoformat()
                new_article = BlogArticle(
                    title=art_spec["title"],
                    slug=art_spec["slug"],
                    summary=art_spec["summary"],
                    body=art_spec["body"],
                    author_user_id=admin_user.id,
                    status="Published",
                    cover_image_path=art_spec["cover_image_path"],
                    published_at=published_ts,
                )
                db.add(new_article)
        db.commit()

        # --- Batch 2 seed data (TASK-003) ---

        # system_config: waitlist confirmation window (REQ-09 admin config)
        existing_config = db.query(SystemConfig).filter(
            SystemConfig.config_key == "waitlist_confirmation_hours"
        ).first()
        if existing_config is None:
            db.add(SystemConfig(
                config_key="waitlist_confirmation_hours",
                config_value="4",
                updated_at=datetime.utcnow().isoformat(),
            ))

        # system_config: survey delay in hours (informational; used by notification service)
        existing_survey_config = db.query(SystemConfig).filter(
            SystemConfig.config_key == "survey_delay_hours"
        ).first()
        if existing_survey_config is None:
            db.add(SystemConfig(
                config_key="survey_delay_hours",
                config_value="24",
                updated_at=datetime.utcnow().isoformat(),
            ))
        db.commit()

        # corporate_packages: 2 default packages so the public /corporate page is not empty
        pkg1_exists = db.query(CorporatePackage).filter(
            CorporatePackage.name == "Wellness Basic"
        ).first()
        if pkg1_exists is None:
            db.add(CorporatePackage(
                name="Wellness Basic",
                tier_order=1,
                description="Foundational health screening for your entire workforce. Ideal for companies looking to establish a proactive health culture.",
                included_services_json='["Annual health screening", "Blood pressure check", "BMI assessment", "Basic blood panel", "Lifestyle counseling session"]',
                price_range_display="$300–$500 per employee",
                is_active=1,
                created_at=datetime.utcnow().isoformat(),
            ))

        pkg2_exists = db.query(CorporatePackage).filter(
            CorporatePackage.name == "Executive Health"
        ).first()
        if pkg2_exists is None:
            db.add(CorporatePackage(
                name="Executive Health",
                tier_order=2,
                description="Comprehensive executive health assessment with advanced diagnostics and specialist consultations. Designed for leadership teams and high-responsibility roles.",
                included_services_json='["Full body check-up", "Advanced cardiac screening", "Oncology screening panel", "Ophthalmology exam", "Dental screening", "Nutritional assessment", "Stress management consultation", "Personalized health report"]',
                price_range_display="$800–$1,200 per employee",
                is_active=1,
                created_at=datetime.utcnow().isoformat(),
            ))
        db.commit()

        print("Seed complete. Demo accounts:")
        for spec in DEMO_USERS:
            print(f"  {spec['role']:17s} {spec['email']:38s} {spec['password']}")
        print("Extra doctors:")
        for spec in EXTRA_DOCTOR_USERS:
            print(f"  Doctor            {spec['email']:38s} {spec['password']}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
