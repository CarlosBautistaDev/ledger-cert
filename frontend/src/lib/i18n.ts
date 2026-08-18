import i18n from "i18next";
import { initReactI18next } from "react-i18next";

/** Minimal i18n setup (Spanish). The infra is wired to add English later. */
void i18n.use(initReactI18next).init({
  resources: {
    es: {
      translation: {
        app: "Ledger de Certificados",
      },
    },
  },
  lng: "es",
  fallbackLng: "es",
  interpolation: { escapeValue: false },
});

export default i18n;
