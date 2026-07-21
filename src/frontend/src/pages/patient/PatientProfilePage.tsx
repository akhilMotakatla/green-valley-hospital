import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { getMyPatientProfile, updateMyPatientProfile, type PatientProfile } from '../../api/patient';
import { extractErrorMessage } from '../../api/client';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';

export function PatientProfilePage() {
  const [profile, setProfile] = useState<PatientProfile | null>(null);
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [ecName, setEcName] = useState('');
  const [ecPhone, setEcPhone] = useState('');
  const [dob, setDob] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getMyPatientProfile()
      .then((p) => {
        setProfile(p);
        setPhone(p.phone ?? '');
        setAddress(p.address ?? '');
        setEcName(p.emergency_contact_name ?? '');
        setEcPhone(p.emergency_contact_phone ?? '');
        setDob(p.date_of_birth ?? '');
      })
      .catch((e) => setError(extractErrorMessage(e)));
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    setSaving(true);
    try {
      const updated = await updateMyPatientProfile({
        phone,
        address,
        emergency_contact_name: ecName,
        emergency_contact_phone: ecPhone,
        date_of_birth: dob,
      });
      setProfile(updated);
      setSuccess(true);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  if (!profile && !error) return <SkeletonBlock lines={7} />;
  if (!profile && error) return <PageError message={error} />;

  return (
    <div>
      <h1>My Profile</h1>
      {error && <p className="error-text">{error}</p>}
      {success && <p className="success-text">Profile updated.</p>}
      {profile && (
        <form className="form" onSubmit={handleSubmit}>
          <label>
            Full name
            <input value={profile.full_name} disabled />
          </label>
          <label>
            Email
            <input value={profile.email} disabled />
          </label>
          <label>
            Date of birth
            <input type="date" value={dob} onChange={(e) => setDob(e.target.value)} />
          </label>
          <label>
            Phone
            <input value={phone} onChange={(e) => setPhone(e.target.value)} />
          </label>
          <label>
            Address
            <input value={address} onChange={(e) => setAddress(e.target.value)} />
          </label>
          <label>
            Emergency contact name
            <input value={ecName} onChange={(e) => setEcName(e.target.value)} />
          </label>
          <label>
            Emergency contact phone
            <input value={ecPhone} onChange={(e) => setEcPhone(e.target.value)} />
          </label>
          <button className="btn btn-primary" type="submit" disabled={saving}>
            {saving ? 'Saving…' : 'Save changes'}
          </button>
        </form>
      )}
    </div>
  );
}
