import {
  Heart,
  Baby,
  Bone,
  Brain,
  Ribbon,
  AlertCircle,
  FlaskConical,
  Eye,
  Smile,
  Star,
  Stethoscope,
  type LucideIcon,
} from 'lucide-react';

const DEPT_ICON_MAP: Record<string, LucideIcon> = {
  cardiology: Heart,
  cardiac: Heart,
  pediatrics: Baby,
  paediatrics: Baby,
  orthopedics: Bone,
  orthopaedics: Bone,
  neurology: Brain,
  neurological: Brain,
  oncology: Ribbon,
  cancer: Ribbon,
  emergency: AlertCircle,
  'general medicine': AlertCircle,
  radiology: FlaskConical,
  laboratory: FlaskConical,
  lab: FlaskConical,
  ophthalmology: Eye,
  eye: Eye,
  dermatology: Smile,
  skin: Smile,
  gynecology: Star,
  gynaecology: Star,
  "women's health": Star,
};

export function getDeptIcon(name: string): LucideIcon {
  const lower = name.toLowerCase();
  for (const [key, icon] of Object.entries(DEPT_ICON_MAP)) {
    if (lower.includes(key)) return icon;
  }
  return Stethoscope;
}
