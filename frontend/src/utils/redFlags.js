const FLAG_RULES = [
  {
    id: "persistent-lesion",
    title: "Persistent / non-healing lesion",
    description:
      "A persistent or non-healing lesion was reported in the patient context.",
    severity: "REVIEW",
    matches: ({ symptoms = [] }) =>
      symptoms.includes("Persistent mouth sore") ||
      symptoms.includes("Non-healing lesion"),
  },

  {
    id: "bleeding",
    title: "Bleeding reported",
    description:
      "Bleeding was reported as part of the recorded symptoms.",
    severity: "REVIEW",
    matches: ({ symptoms = [] }) =>
      symptoms.includes("Bleeding"),
  },

  {
    id: "white-red-patch",
    title: "White / red patch reported",
    description:
      "A white or red oral patch was reported in the patient context.",
    severity: "REVIEW",
    matches: ({ symptoms = [] }) =>
      symptoms.includes("White or red patch"),
  },

  {
    id: "lump-thickening",
    title: "Lump / thickening reported",
    description:
      "A lump or thickening was reported in the patient context.",
    severity: "REVIEW",
    matches: ({ symptoms = [] }) =>
      symptoms.includes("Lump or thickening"),
  },

  {
    id: "swallowing-difficulty",
    title: "Difficulty swallowing",
    description:
      "Difficulty swallowing was reported in the patient context.",
    severity: "REVIEW",
    matches: ({ symptoms = [] }) =>
      symptoms.includes("Difficulty swallowing"),
  },

  {
    id: "numbness",
    title: "Oral numbness reported",
    description:
      "Numbness was reported in the patient context.",
    severity: "REVIEW",
    matches: ({ symptoms = [] }) =>
      symptoms.includes("Numbness"),
  },

  {
    id: "tobacco-exposure",
    title: "Tobacco exposure recorded",
    description:
      "Tobacco exposure was recorded in the research context.",
    severity: "CONTEXT",
    matches: ({ tobacco }) =>
      Boolean(
        tobacco &&
        tobacco !== "Never" &&
        tobacco !== "Not provided"
      ),
  },

  {
    id: "alcohol-exposure",
    title: "Alcohol exposure recorded",
    description:
      "Alcohol exposure was recorded in the research context.",
    severity: "CONTEXT",
    matches: ({ alcohol }) =>
      Boolean(
        alcohol &&
        alcohol !== "Never" &&
        alcohol !== "Not provided"
      ),
  },

  {
    id: "previous-lesion",
    title: "Previous oral lesion reported",
    description:
      "A previous oral lesion was reported in the patient context.",
    severity: "CONTEXT",
    matches: ({ previousOralLesion }) =>
      previousOralLesion === "Yes",
  },

  {
    id: "previous-cancer",
    title: "Previous oral cancer reported",
    description:
      "Previous oral cancer was reported in the patient context.",
    severity: "CONTEXT",
    matches: ({ previousOralCancer }) =>
      previousOralCancer === "Yes",
  },

  {
    id: "symptom-duration",
    title: "Symptom duration recorded",
    description:
      "A symptom duration was provided for the current research case.",
    severity: "CONTEXT",
    matches: ({ symptomDuration }) =>
      Boolean(
        symptomDuration &&
        symptomDuration.trim()
      ),
  },
];

export function detectRedFlags(patientContext) {
  if (!patientContext) {
    return [];
  }

  return FLAG_RULES
    .filter((rule) => {
      try {
        return rule.matches(patientContext);
      } catch {
        return false;
      }
    })
    .map((rule) => ({
      id: rule.id,
      title: rule.title,
      description: rule.description,
      severity: rule.severity,
    }));
}

export function getRedFlagSummary(flags = []) {
  const reviewCount = flags.filter(
    (flag) => flag.severity === "REVIEW"
  ).length;

  const contextCount = flags.filter(
    (flag) => flag.severity === "CONTEXT"
  ).length;

  return {
    total: flags.length,
    reviewCount,
    contextCount,
  };
}