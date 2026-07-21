import { useState } from 'react';
import type { FormEvent } from 'react';
import { registerPatient } from '../../api/staff';
import { extractErrorMessage } from '../../api/client';

export function RegisterPatientPage() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [dob, setDob] = useState('');
  const [gender, setGender] = useState('');
  const [address, setAddress] = useState('');
  const [ecName, setEcName] = useState('');
  const [ecPhone, setEcPhone] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ patient_id: number; temporary_password: string } | null>(
    null,
  );
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setSubmitting(true);
    try {
      const res = await registerPatient({
        full_name: fullName,
        email,
        phone,
        date_of_birth: dob,
        gender: gender || undefined,
        address: address || undefined,
        emergency_contact_name: ecName || undefined,
        emergency_contact_phone: ecPhone || undefined,
      });
      setResult(res);
      setFullName('');
      setEmail('');
      setPhone('');
      setDob('');
      setGender('');
      setAddress('');
      setEcName('');
      setEcPhone('');
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1>Register Walk-in Patient</h1>
      {error && <p className="error-text">{error}</p>}
      {result && (
        <div className="card section success-text">
          Patient #{result.patient_id} registered. Temporary password: <strong>{result.temporary_password}</strong>
        </div>
      )}
      <form className="form" onSubmit={handleSubmit}>
        <label>
          Full name
          <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
        </label>
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          Phone
          <input value={phone} onChange={(e) => setPhone(e.target.value)} required />
        </label>
        <label>
          Date of birth
          <input type="date" value={dob} onChange={(e) => setDob(e.target.value)} required />
        </label>
        <label>
          Gender
          <input value={gender} onChange={(e) => setGender(e.target.value)} />
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
        <button className="btn btn-primary" type="submit" disabled={submitting}>
          {submitting ? 'Registering…' : 'Register Patient'}
        </button>
      </form>
    </div>
  );
}
