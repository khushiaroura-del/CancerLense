import {
  Activity,
  CalendarDays,
  Check,
  ChevronDown,
  CircleUserRound,
  ClipboardList,
  Cigarette,
  Clock3,
  Droplets,
  HeartPulse,
  History,
  Info,
  Wine,
  X,
} from "lucide-react";
import { useState } from "react";

const initialForm = {
  ageGroup: "",
  tobaccoExposure: "",
  alcoholExposure: "",
  previousOralLesion: "",
  previousOralCancer: "",
  dentalHistory: "",
  symptoms: [],
  symptomDuration: "",
  symptomNotes: "",
};

const symptomOptions = [
  "Persistent mouth sore",
  "Pain or discomfort",
  "Bleeding",
  "Non-healing lesion",
  "Lump or thickening",
  "White or red patch",
  "Difficulty chewing",
  "Difficulty swallowing",
  "Numbness",
  "Voice changes",
];

const ageGroups = [
  "Under 18",
  "18–24",
  "25–34",
  "35–44",
  "45–54",
  "55–64",
  "65+",
  "Prefer not to say",
];

const exposureOptions = [
  "Never",
  "Former",
  "Occasional",
  "Regular",
  "Prefer not to say",
];

const yesNoOptions = [
  "Yes",
  "No",
  "Unknown",
  "Prefer not to say",
];

const durationOptions = [
  "Less than 7 days",
  "7–14 days",
  "15–21 days",
  "More than 21 days",
  "Unknown",
];

function SelectField({
  label,
  value,
  options,
  onChange,
  icon: Icon,
  optional = true,
}) {
  return (
    <div className="context-field">
      <label>
        <span className="context-label-icon">
          <Icon size={14} />
        </span>

        <span>{label}</span>

        {optional && (
          <span className="context-optional">OPTIONAL</span>
        )}
      </label>

      <div className="context-select-wrap">
        <select
          value={value}
          onChange={(event) => onChange(event.target.value)}
        >
          <option value="">Select</option>

          {options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>

        <ChevronDown size={16} />
      </div>
    </div>
  );
}

export default function PatientContext({
  onSave,
  onClose,
  initialData = initialForm,
}) {
  const [form, setForm] = useState({
    ...initialForm,
    ...initialData,
    symptoms: initialData?.symptoms || [],
  });

  const updateField = (field, value) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const toggleSymptom = (symptom) => {
    setForm((current) => {
      const exists = current.symptoms.includes(symptom);

      return {
        ...current,
        symptoms: exists
          ? current.symptoms.filter((item) => item !== symptom)
          : [...current.symptoms, symptom],
      };
    });
  };

  const handleSave = () => {
    onSave?.(form);
  };

  const selectedSymptoms = form.symptoms.length;

  return (
    <div className="context-overlay">
      <div className="context-modal">
        <div className="context-modal-header">
          <div>
            <div className="context-kicker">
              CANCERLENSE / CASE CONTEXT
            </div>

            <h2>Patient Risk &amp; History</h2>

            <p>
              Optional information that adds context to the research
              screening workflow.
            </p>
          </div>

          <button
            type="button"
            className="context-close"
            onClick={onClose}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        <div className="context-notice">
          <Info size={17} />

          <div>
            <strong>Research context only</strong>

            <span>
              These responses do not diagnose cancer or determine a
              clinical condition.
            </span>
          </div>
        </div>

        <div className="context-section">
          <div className="context-section-heading">
            <div className="context-section-icon">
              <CircleUserRound size={18} />
            </div>

            <div>
              <span>01 / PATIENT PROFILE</span>
              <h3>Background context</h3>
            </div>
          </div>

          <div className="context-grid">
            <SelectField
              label="Age group"
              value={form.ageGroup}
              options={ageGroups}
              onChange={(value) => updateField("ageGroup", value)}
              icon={CalendarDays}
            />

            <SelectField
              label="Tobacco exposure"
              value={form.tobaccoExposure}
              options={exposureOptions}
              onChange={(value) =>
                updateField("tobaccoExposure", value)
              }
              icon={Cigarette}
            />

            <SelectField
              label="Alcohol exposure"
              value={form.alcoholExposure}
              options={exposureOptions}
              onChange={(value) =>
                updateField("alcoholExposure", value)
              }
              icon={Wine}
            />

            <SelectField
              label="Previous oral lesion"
              value={form.previousOralLesion}
              options={yesNoOptions}
              onChange={(value) =>
                updateField("previousOralLesion", value)
              }
              icon={History}
            />

            <SelectField
              label="Previous oral cancer"
              value={form.previousOralCancer}
              options={yesNoOptions}
              onChange={(value) =>
                updateField("previousOralCancer", value)
              }
              icon={HeartPulse}
            />

            <SelectField
              label="Dental history"
              value={form.dentalHistory}
              options={[
                "No known dental issues",
                "Recent dental treatment",
                "Ongoing dental treatment",
                "Known dental condition",
                "Unknown",
                "Prefer not to say",
              ]}
              onChange={(value) =>
                updateField("dentalHistory", value)
              }
              icon={ClipboardList}
            />
          </div>
        </div>

        <div className="context-divider" />

        <div className="context-section">
          <div className="context-section-heading">
            <div className="context-section-icon">
              <Activity size={18} />
            </div>

            <div>
              <span>02 / SYMPTOMS</span>
              <h3>What are you experiencing?</h3>
            </div>
          </div>

          <div className="symptom-meta">
            <span>
              Select all that apply
            </span>

            <span className="symptom-count">
              {selectedSymptoms} selected
            </span>
          </div>

          <div className="symptom-grid">
            {symptomOptions.map((symptom) => {
              const selected = form.symptoms.includes(symptom);

              return (
                <button
                  type="button"
                  key={symptom}
                  className={`symptom-chip ${
                    selected ? "symptom-chip-selected" : ""
                  }`}
                  onClick={() => toggleSymptom(symptom)}
                >
                  <span className="symptom-check">
                    {selected && <Check size={13} />}
                  </span>

                  <span>{symptom}</span>
                </button>
              );
            })}
          </div>

          <div className="context-grid context-grid-single">
            <SelectField
              label="Symptom duration"
              value={form.symptomDuration}
              options={durationOptions}
              onChange={(value) =>
                updateField("symptomDuration", value)
              }
              icon={Clock3}
            />
          </div>

          <div className="context-notes">
            <label htmlFor="symptom-notes">
              Additional notes
              <span>OPTIONAL</span>
            </label>

            <textarea
              id="symptom-notes"
              value={form.symptomNotes}
              onChange={(event) =>
                updateField("symptomNotes", event.target.value)
              }
              placeholder="Example: noticed a small area approximately 12 days ago..."
              rows={4}
              maxLength={500}
            />

            <div className="context-character-count">
              {form.symptomNotes.length}/500
            </div>
          </div>
        </div>

        <div className="context-footer">
          <div className="context-footer-status">
            <Droplets size={15} />

            <span>
              Information stays attached to this case only.
            </span>
          </div>

          <div className="context-actions">
            <button
              type="button"
              className="context-secondary-button"
              onClick={onClose}
            >
              Cancel
            </button>

            <button
              type="button"
              className="context-primary-button"
              onClick={handleSave}
            >
              <Check size={16} />
              Save Case Context
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}