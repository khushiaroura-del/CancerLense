import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  Droplets,
  History,
  ShieldAlert,
  Cigarette,
  Wine,
  Activity,
  Info,
} from "lucide-react";

const flagDefinitions = [
  {
    id: "persistent-sore",
    label: "Persistent mouth sore",
    description:
      "A persistent or non-healing oral sore was reported.",
    icon: Activity,
    type: "review",
    matches: (context) =>
      context.symptoms?.includes("Persistent mouth sore") ||
      context.symptoms?.includes("Non-healing lesion"),
  },

  {
    id: "bleeding",
    label: "Bleeding reported",
    description:
      "Bleeding was included in the reported symptoms.",
    icon: Droplets,
    type: "review",
    matches: (context) =>
      context.symptoms?.includes("Bleeding"),
  },

  {
    id: "white-red-patch",
    label: "White or red patch",
    description:
      "A white or red oral patch was reported.",
    icon: AlertCircle,
    type: "review",
    matches: (context) =>
      context.symptoms?.includes("White or red patch"),
  },

  {
    id: "lump",
    label: "Lump or thickening",
    description:
      "A lump or area of thickening was reported.",
    icon: ShieldAlert,
    type: "review",
    matches: (context) =>
      context.symptoms?.includes("Lump or thickening"),
  },

  {
    id: "swallowing",
    label: "Difficulty swallowing",
    description:
      "Difficulty swallowing was included in the reported symptoms.",
    icon: Activity,
    type: "review",
    matches: (context) =>
      context.symptoms?.includes("Difficulty swallowing"),
  },

  {
    id: "numbness",
    label: "Numbness reported",
    description:
      "Oral numbness was included in the reported symptoms.",
    icon: Activity,
    type: "review",
    matches: (context) =>
      context.symptoms?.includes("Numbness"),
  },

  {
    id: "tobacco",
    label: "Tobacco exposure",
    description:
      "The case includes reported tobacco exposure.",
    icon: Cigarette,
    type: "context",
    matches: (context) =>
      ["Former", "Occasional", "Regular"].includes(
        context.tobaccoExposure
      ),
  },

  {
    id: "alcohol",
    label: "Alcohol exposure",
    description:
      "The case includes reported alcohol exposure.",
    icon: Wine,
    type: "context",
    matches: (context) =>
      ["Former", "Occasional", "Regular"].includes(
        context.alcoholExposure
      ),
  },

  {
    id: "previous-lesion",
    label: "Previous oral lesion",
    description:
      "A previous oral lesion was reported.",
    icon: History,
    type: "context",
    matches: (context) =>
      context.previousOralLesion === "Yes",
  },

  {
    id: "previous-cancer",
    label: "Previous oral cancer",
    description:
      "Previous oral cancer was reported in the case context.",
    icon: History,
    type: "context",
    matches: (context) =>
      context.previousOralCancer === "Yes",
  },

  {
    id: "duration",
    label: "Extended symptom duration",
    description:
      "The reported symptom duration is more than 21 days.",
    icon: Clock3,
    type: "duration",
    matches: (context) =>
      context.symptomDuration === "More than 21 days",
  },
];

function getFlags(context) {
  if (!context) return [];

  return flagDefinitions.filter((flag) =>
    flag.matches(context)
  );
}

export default function RedFlagPanel({
  patientContext,
}) {
  const flags = getFlags(patientContext);

  const reviewFlags = flags.filter(
    (flag) => flag.type === "review"
  );

  const contextFlags = flags.filter(
    (flag) => flag.type === "context"
  );

  const durationFlags = flags.filter(
    (flag) => flag.type === "duration"
  );

  const hasContext =
    patientContext &&
    (
      patientContext.ageGroup ||
      patientContext.tobaccoExposure ||
      patientContext.alcoholExposure ||
      patientContext.previousOralLesion ||
      patientContext.previousOralCancer ||
      patientContext.dentalHistory ||
      patientContext.symptoms?.length ||
      patientContext.symptomDuration ||
      patientContext.symptomNotes
    );

  if (!hasContext) {
    return (
      <div className="red-flag-panel red-flag-empty">

        <div className="red-flag-header">

          <div className="red-flag-heading">

            <div className="red-flag-icon">
              <ShieldAlert size={18} />
            </div>

            <div>
              <div className="red-flag-kicker">
                STEP 04 / CASE INTELLIGENCE
              </div>

              <h3>
                Research Context Flags
              </h3>
            </div>

          </div>

          <div className="red-flag-status neutral">
            NO CONTEXT
          </div>

        </div>

        <div className="red-flag-empty-content">

          <Info size={18} />

          <div>
            <strong>
              Add Case Context to enable review flags.
            </strong>

            <span>
              This panel uses only information voluntarily
              provided for the current case.
            </span>
          </div>

        </div>

      </div>
    );
  }

  if (flags.length === 0) {
    return (
      <div className="red-flag-panel">

        <div className="red-flag-header">

          <div className="red-flag-heading">

            <div className="red-flag-icon">
              <ShieldAlert size={18} />
            </div>

            <div>
              <div className="red-flag-kicker">
                STEP 04 / CASE INTELLIGENCE
              </div>

              <h3>
                Research Context Flags
              </h3>
            </div>

          </div>

          <div className="red-flag-status clear">
            NO FLAGS
          </div>

        </div>

        <div className="red-flag-clear">

          <div className="red-flag-clear-icon">
            <CheckCircle2 size={20} />
          </div>

          <div>
            <strong>
              No configured context flags detected.
            </strong>

            <span>
              No matching review prompts were found in
              the information provided for this case.
            </span>
          </div>

        </div>

        <div className="red-flag-disclaimer">
          <Info size={14} />

          <span>
            This does not indicate absence of disease and
            does not change the model prediction.
          </span>
        </div>

      </div>
    );
  }

  return (
    <div className="red-flag-panel">

      {/* ================================================
          HEADER
          ================================================ */}

      <div className="red-flag-header">

        <div className="red-flag-heading">

          <div className="red-flag-icon">
            <ShieldAlert size={18} />
          </div>

          <div>

            <div className="red-flag-kicker">
              STEP 04 / CASE INTELLIGENCE
            </div>

            <h3>
              Research Context Flags
            </h3>

          </div>

        </div>

        <div className="red-flag-status">
          {flags.length} FLAG
          {flags.length !== 1 ? "S" : ""}
        </div>

      </div>

      {/* ================================================
          DESCRIPTION
          ================================================ */}

      <div className="red-flag-intro">

        <p>
          Contextual review prompts generated from the
          information provided for this case.
        </p>

        <span>
          These flags do not diagnose disease or modify
          the AI model output.
        </span>

      </div>

      {/* ================================================
          SUMMARY
          ================================================ */}

      <div className="red-flag-summary">

        <div>
          <strong>
            {reviewFlags.length}
          </strong>

          <span>
            REVIEW
          </span>
        </div>

        <div>
          <strong>
            {contextFlags.length}
          </strong>

          <span>
            CONTEXT
          </span>
        </div>

        <div>
          <strong>
            {durationFlags.length}
          </strong>

          <span>
            DURATION
          </span>
        </div>

      </div>

      {/* ================================================
          FLAGS
          ================================================ */}

      <div className="red-flag-list">

        {flags.map((flag) => {

          const Icon = flag.icon;

          return (
            <div
              className={`red-flag-item red-flag-${flag.type}`}
              key={flag.id}
            >

              <div className="red-flag-item-icon">
                <Icon size={16} />
              </div>

              <div className="red-flag-item-content">

                <div className="red-flag-item-top">

                  <strong>
                    {flag.label}
                  </strong>

                  <span>
                    {flag.type === "review"
                      ? "REVIEW CONTEXT"
                      : flag.type === "duration"
                      ? "DURATION"
                      : "CONTEXT"}
                  </span>

                </div>

                <p>
                  {flag.description}
                </p>

              </div>

            </div>
          );
        })}

      </div>

      {/* ================================================
          DISCLAIMER
          ================================================ */}

      <div className="red-flag-disclaimer">

        <Info size={14} />

        <span>
          Research context only. These prompts are based
          on user-provided information and are not clinical
          risk scores, diagnoses, or changes to the model
          prediction.
        </span>

      </div>

    </div>
  );
}