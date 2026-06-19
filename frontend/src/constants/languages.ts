// Languages offered for a voice profile. OmniVoice infers the spoken language
// from the text itself, so this is metadata/display only (see the README).
export interface LanguageOption {
  code: string;
  label: string;
}

export const LANGUAGES: LanguageOption[] = [
  { code: "en", label: "English" },
  { code: "lt", label: "Lithuanian" },
  { code: "de", label: "German" },
  { code: "fr", label: "French" },
  { code: "es", label: "Spanish" },
  { code: "pt-BR", label: "Portuguese (Brazil)" },
  { code: "ru", label: "Russian" },
  { code: "zh", label: "Chinese" },
];

export const DEFAULT_LANGUAGE = LANGUAGES[0].code;
