// Affichage du tableau du contrôle d'intangibilité (étape 4, GroupingAnalyse.vue).
// Les textes viennent du rapport V1 (api/src/model.py, inchangé) : ces fonctions ne
// changent que leur présentation.

const FORMAT_FR = new Intl.NumberFormat('fr-FR')

// « Écart significatif détecté - Nécessite une justification… » → « Écart significatif détecté ».
export function conclusionCourte(texte) {
  return String(texte || '').split(' - ')[0].trim()
}

// Montants écrits par la V1 au format Python (53898096.0, -10000.0) → format français.
export function montantsEnFrancais(texte) {
  return String(texte || '').replace(/-?\d+\.\d+/g, (m) => FORMAT_FR.format(Number(m)))
}
