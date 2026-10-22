// Test de parcours de l'interface : clique sur les boutons de navigation
// principaux et vérifie que le bon écran s'ouvre, sans erreur dans la
// console. Sans dépendance : Node pilote le Chrome installé (protocole
// DevTools, WebSocket intégré à Node 22+).
//
// Prérequis : API Flask sur http://localhost:5000 et Vite sur
// http://localhost:5173 (surchargeables : PARCOURS_API, PARCOURS_FRONT,
// PARCOURS_CHROME, PARCOURS_PYTHON).
// Lancement : npm run test:parcours   (depuis clients/)
//
// Données : un client et une mission FICTIFS sont créés avant le test par
// api/parcours_donnees_test.py, puis supprimés à la fin, même en cas d'échec.
import { spawn, execFileSync } from 'node:child_process'
import { mkdirSync, mkdtempSync, writeFileSync, existsSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const ICI = dirname(fileURLToPath(import.meta.url))
const DOSSIER_API = resolve(ICI, '../../../api')
const API = process.env.PARCOURS_API || 'http://localhost:5000'
const FRONT = process.env.PARCOURS_FRONT || 'http://localhost:5173'
const PYTHON = process.env.PARCOURS_PYTHON || 'python'
const CAPTURES = process.env.PARCOURS_CAPTURES || join(ICI, 'captures')
const CHROMES = [
  process.env.PARCOURS_CHROME,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  '/usr/bin/google-chrome', '/usr/bin/chromium',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
].filter(Boolean)
const PORT = 9400 + Math.floor(Math.random() * 400)
const attendre = (ms) => new Promise((r) => setTimeout(r, ms))

// --- Données fictives -------------------------------------------------------
function donnees(...args) {
  const sortie = execFileSync(PYTHON, ['parcours_donnees_test.py', ...args], {
    cwd: DOSSIER_API, env: { ...process.env, PYTHONIOENCODING: 'utf-8' }, encoding: 'utf-8',
  })
  return JSON.parse(sortie.trim().split('\n').filter((l) => l.startsWith('{')).pop())
}

// --- Pilotage de Chrome -----------------------------------------------------
async function lancerChrome() {
  const executable = CHROMES.find((c) => existsSync(c))
  if (!executable) throw new Error('Chrome introuvable (PARCOURS_CHROME pour indiquer son chemin)')
  const profil = mkdtempSync(join(tmpdir(), 'parcours-'))
  const processus = spawn(executable, ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${profil}`,
    '--window-size=1600,1000', '--no-first-run', 'about:blank'])
  let cible
  for (let i = 0; i < 60 && !cible; i++) {
    try { cible = (await (await fetch(`http://127.0.0.1:${PORT}/json`)).json()).find((t) => t.type === 'page') } catch { await attendre(250) }
  }
  if (!cible) throw new Error('Chrome ne répond pas')
  const ws = new WebSocket(cible.webSocketDebuggerUrl)
  await new Promise((r, e) => { ws.addEventListener('open', r); ws.addEventListener('error', e) })
  let id = 0
  const enAttente = new Map()
  const erreurs = []
  ws.addEventListener('message', (m) => {
    const d = JSON.parse(m.data)
    if (d.id && enAttente.has(d.id)) { enAttente.get(d.id)(d.result || {}); enAttente.delete(d.id) }
    if (d.method === 'Runtime.exceptionThrown') {
      erreurs.push(d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text)
    }
    if (d.method === 'Runtime.consoleAPICalled' && d.params.type === 'error') {
      erreurs.push(d.params.args.map((a) => a.value ?? a.description ?? '').join(' '))
    }
  })
  const cdp = (method, params = {}) => new Promise((r) => { const n = ++id; enAttente.set(n, r); ws.send(JSON.stringify({ id: n, method, params })) })
  await cdp('Runtime.enable')
  await cdp('Page.enable')
  // Une exception dans la page (ex. bouton introuvable) fait échouer l'étape, jamais en silence.
  const evaluer = async (expression) => {
    const reponse = await cdp('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })
    if (reponse.exceptionDetails) {
      throw new Error(reponse.exceptionDetails.exception?.description?.split('\n')[0] || reponse.exceptionDetails.text)
    }
    return reponse.result?.value
  }
  return {
    cdp, evaluer, erreurs,
    fermer: () => { try { ws.close() } catch { /* déjà fermé */ } processus.kill() },
  }
}

// --- Assertions --------------------------------------------------------------
const resultats = []

async function etape(navigateur, nom, action, attendu) {
  navigateur.erreurs.length = 0
  let echec = null
  try {
    await action()
    // Attente active (jusqu'à 10 s) que l'écran attendu soit affiché.
    let etat
    for (let i = 0; i < 40; i++) {
      etat = await navigateur.evaluer(`({ url: location.pathname + location.search, texte: document.body.innerText,
        barre: !!document.querySelector('[data-barre-mission]') })`)
      const ok = (!attendu.url || attendu.url.test(etat.url))
        && (!attendu.texte || etat.texte.includes(attendu.texte))
        && (attendu.barre === undefined || etat.barre === attendu.barre)
      if (ok) break
      await attendre(250)
    }
    if (attendu.url && !attendu.url.test(etat.url)) echec = `adresse ${etat.url}, attendu ${attendu.url}`
    else if (attendu.texte && !etat.texte.includes(attendu.texte)) echec = `texte « ${attendu.texte} » absent (adresse ${etat.url})`
    else if (attendu.barre !== undefined && etat.barre !== attendu.barre) echec = `barre latérale ${etat.barre ? 'visible' : 'absente'}`
    await attendre(600) // laisse arriver les erreurs asynchrones
    if (!echec && navigateur.erreurs.length) echec = `erreur(s) console : ${navigateur.erreurs.join(' | ').slice(0, 400)}`
  } catch (e) {
    echec = e.message
  }
  const fichier = join(CAPTURES, `${String(resultats.length + 1).padStart(2, '0')}_${nom.replace(/[^a-z0-9]+/gi, '_').slice(0, 60)}.png`)
  try {
    const { data } = await navigateur.cdp('Page.captureScreenshot', { format: 'png' })
    writeFileSync(fichier, Buffer.from(data, 'base64'))
  } catch { /* capture facultative */ }
  resultats.push({ nom, ok: !echec, echec, fichier })
  console.log(`${echec ? '✗' : '✓'} ${nom}${echec ? ' — ' + echec : ''}`)
}

// Clic sur un élément visible par son texte exact (le premier, ou celui dans `dans`).
// Les <span> sont inclus : certains boutons sont des blocs cliquables (ex. « Détail »).
const cliquer = (navigateur, texte, dans = 'document') => navigateur.evaluer(`(() => {
  const racine = ${dans};
  if (!racine) throw new Error('zone introuvable pour « ' + ${JSON.stringify(texte)} + ' »');
  const el = [...racine.querySelectorAll('button, a, label, [role=button], span')]
    .find((x) => x.textContent.trim() === ${JSON.stringify(texte)} && x.offsetParent !== null);
  if (!el) throw new Error('bouton « ' + ${JSON.stringify(texte)} + ' » introuvable');
  el.click();
})()`)

const aller = async (navigateur, chemin) => {
  await navigateur.cdp('Page.navigate', { url: FRONT + chemin })
  await attendre(1500)
}

// --- Parcours -----------------------------------------------------------------
async function parcours(navigateur, d) {
  const mission = new RegExp(`^/grouping-analyse/${d.mission_id}`)
  const ligneDuClient = `[...document.querySelectorAll('tr')].find((tr) => tr.textContent.includes(${JSON.stringify(d.client_nom)}))`

  await aller(navigateur, '/')
  await navigateur.evaluer(`sessionStorage.setItem('token', 'test-parcours');
    sessionStorage.setItem('user', JSON.stringify({ firstname: 'Test', lastname: 'Parcours' }))`)

  // Liste des clients -> « Voir » d'un client -> fiche
  await etape(navigateur, 'Liste des clients', () => aller(navigateur, '/clients'), { url: /^\/clients/, texte: 'Liste des clients' })
  await etape(navigateur, 'Liste des clients : « Voir » du client', async () => {
    await navigateur.evaluer(`(() => { const i = [...document.querySelectorAll('input')].find((x) => /recherch/i.test(x.placeholder || ''));
      i.value = ${JSON.stringify(d.client_nom)}; i.dispatchEvent(new Event('input', { bubbles: true })) })()`)
    await attendre(800)
    await cliquer(navigateur, 'Voir', ligneDuClient)
  }, { texte: 'Voir les missions' })
  await etape(navigateur, 'Fenêtre client : « Voir les missions » -> fiche client', () => cliquer(navigateur, 'Voir les missions'),
    { url: new RegExp(`^/client/${d.client_id}`), texte: d.client_nom })

  // Fiche client -> « Modifier client », « Nouvelle mission », « Voir » d'une mission
  await etape(navigateur, 'Fiche client : « Modifier client »', () => cliquer(navigateur, 'Modifier client'), { texte: 'Enregistrer' })
  await etape(navigateur, 'Fiche client : « Annuler » la modification', () => cliquer(navigateur, 'Annuler'), { texte: 'Modifier client' })
  await etape(navigateur, 'Fiche client : « Nouvelle mission »', () => cliquer(navigateur, 'Nouvelle mission'),
    { url: new RegExp(`^/newMission/${d.client_id}`) })
  await etape(navigateur, 'Retour à la fiche client', () => aller(navigateur, `/client/${d.client_id}`), { texte: d.client_nom })
  await etape(navigateur, 'Fiche client : « Voir » de la mission', () => cliquer(navigateur, 'Voir'),
    { url: mission, texte: 'Contrôle de cohérence', barre: true })

  // Barre latérale
  await etape(navigateur, 'Barre latérale : Fichiers complémentaires', () => cliquer(navigateur, 'Fichiers complémentaires'),
    { url: /step=fichiers_complementaires/, texte: 'BALANCE AUXILIAIRE CLIENTS', barre: true })
  await etape(navigateur, 'Fichiers complémentaires : « Voir le rapprochement IPE »', () => cliquer(navigateur, 'Voir le rapprochement IPE'),
    { url: /step=fiabilite_ipe/, texte: 'Lancer le rapprochement', barre: true })
  await etape(navigateur, 'Barre latérale : Fichiers complémentaires (retour)', () => cliquer(navigateur, 'Fichiers complémentaires'),
    { url: /step=fichiers_complementaires/, barre: true })
  await etape(navigateur, 'Barre latérale : Fiabilité IPE (Détail)', () => cliquer(navigateur, 'Détail'),
    { url: /step=fiabilite_ipe/, texte: 'Lancer le rapprochement', barre: true })
  // Fiabilité IPE (docs/PLAN_ecrans_lot1.md §2.1) : circuit en quatre étapes, action attendue, lien vers les commentaires généraux.
  await etape(navigateur, 'Fiabilité IPE : circuit de revue en quatre étapes', async () => {},
    { url: /step=fiabilite_ipe/, texte: '4 · Validé', barre: true })
  await etape(navigateur, 'Fiabilité IPE : soumission bloquée sans rapprochement (règle serveur)', async () => {},
    { url: /step=fiabilite_ipe/, texte: "Lancez d'abord le rapprochement.", barre: true })
  await etape(navigateur, 'Fiabilité IPE : synthèse avec colonne Fichier', async () => {},
    { url: /step=fiabilite_ipe/, texte: 'Aucun fichier importé', barre: true })
  // Panneau latéral d'un compte en écart (§2.4) : rapprochement lancé, « Commenter » sur 401.
  await etape(navigateur, 'Fiabilité IPE : « Lancer le rapprochement »', () => cliquer(navigateur, 'Lancer le rapprochement'),
    { url: /step=fiabilite_ipe/, texte: 'Balance auxiliaire fournisseurs · v1', barre: true })
  await etape(navigateur, 'Fiabilité IPE : « Commenter » ouvre le panneau du compte 401000', () => navigateur.evaluer(`(() => {
      const tr = [...document.querySelectorAll('tr')].find((t) => t.querySelector('td')?.textContent.trim() === '401000');
      if (!tr) throw new Error('ligne 401000 introuvable'); tr.querySelector('button').click() })()`),
    { url: /step=fiabilite_ipe/, texte: 'Écart · compte 401000', barre: true })
  await etape(navigateur, 'Fiabilité IPE : fermer le panneau', () => navigateur.evaluer(
    `document.querySelector('[aria-label="Fermer le panneau"]').click()`),
    { url: /step=fiabilite_ipe/, barre: true })
  await etape(navigateur, 'Fiabilité IPE : « Commentaires généraux (0) » -> section', () => cliquer(navigateur, 'Commentaires généraux (0)'),
    { url: /step=fiabilite_ipe/, texte: 'Aucun commentaire général.', barre: true })
  // Journal d'audit (page B) : lecture seule de l'historique ; le rapprochement lancé ci-dessus y figure.
  await etape(navigateur, "Barre latérale : Journal d'audit", () => cliquer(navigateur, "Journal d'audit"),
    { url: /step=journal_audit/, texte: 'Rapprochement lancé', barre: true })
  await etape(navigateur, "Journal d'audit : import tracé, aucune action de modification", () => navigateur.evaluer(`(() => {
      const lignes = [...document.querySelectorAll('tbody tr')];
      if (lignes.some((tr) => tr.querySelector('button, input, select, a'))) throw new Error('action dans une ligne du journal');
    })()`),
    { url: /step=journal_audit/, texte: 'Fichier importé', barre: true })
  await etape(navigateur, "Journal d'audit : filtre Module « Fiabilité IPE »", async () => {
    await navigateur.evaluer(`(() => { const s = document.querySelector('select');
      s.value = 'Fiabilité IPE'; s.dispatchEvent(new Event('change', { bubbles: true })) })()`)
    await attendre(1500)
    await navigateur.evaluer(`(() => {
      if ([...document.querySelectorAll('tbody tr')].some((tr) => tr.children[2]?.textContent.trim() === 'Import'))
        throw new Error('entrée « Import » encore affichée'); })()`)
  }, { url: /step=journal_audit/, texte: 'Rapprochement lancé', barre: true })
  await etape(navigateur, "Journal d'audit : export Excel (fichier .xlsx)", () => navigateur.evaluer(`(async () => {
      const r = await fetch(${JSON.stringify(API)} + '/api/v1/missions/' + ${JSON.stringify(d.mission_id)} + '/journal/export?module=Import');
      if (!r.ok || !r.headers.get('content-type').includes('spreadsheetml')) throw new Error('export HTTP ' + r.status); })()`),
    { url: /step=journal_audit/, texte: 'Exporter (Excel)', barre: true })
  // Paramètres (page C) : consultation seule, valeurs lues côté serveur.
  await etape(navigateur, 'Barre latérale : Paramètres', () => cliquer(navigateur, 'Paramètres'),
    { url: /step=parametres/, texte: "Erreur d'imputation", barre: true })
  await etape(navigateur, 'Paramètres : consultation seule (aucun champ modifiable, aucun bouton actif)', () => navigateur.evaluer(`(() => {
      const champs = [...document.querySelectorAll('input')].filter((i) => !i.readOnly && !i.disabled && i.closest('section'));
      if (champs.length) throw new Error(champs.length + ' champ(s) modifiable(s)');
      const actifs = [...document.querySelectorAll('section button')].filter((b) => !b.disabled);
      if (actifs.length) throw new Error('bouton actif : ' + actifs[0].textContent.trim());
    })()`),
    { url: /step=parametres/, texte: "Modification réservée aux administrateurs, disponible avec l'authentification", barre: true })
  // Circularisation, sous-lot a (docs/PLAN_circularisation.md) : population, tiers retenu avec motif, mémo soumis.
  await etape(navigateur, 'Barre latérale : Sélection des tiers', () => cliquer(navigateur, 'Sélection des tiers'),
    { url: /step=selection_tiers/, texte: 'Sélection des tiers à circulariser', barre: true })
  await etape(navigateur, 'Sélection des tiers : « Lancer la sélection » (fournisseurs)',
    () => cliquer(navigateur, 'Lancer la sélection'),
    { url: /step=selection_tiers/, texte: 'FOURNISSEUR TEST', barre: true })
  await etape(navigateur, 'Sélection des tiers : retenir 4011TEST avec un motif', async () => {
    await navigateur.evaluer(`document.querySelector('[aria-label="Retenir 4011TEST"]').click()`)
    await attendre(400)
    await navigateur.evaluer(`(() => { const t = document.querySelector('.fixed textarea');
      t.value = 'Solde le plus élevé de la population fournisseurs'; t.dispatchEvent(new Event('input', { bubbles: true })) })()`)
    await attendre(200)
    await cliquer(navigateur, 'Confirmer')
  }, { url: /step=selection_tiers/, texte: 'Ajout manuel', barre: true })
  await etape(navigateur, 'Sélection des tiers : « Générer le mémo de sélection »', () => cliquer(navigateur, 'Générer le mémo de sélection'),
    { url: /step=selection_tiers/, texte: '4. Ajouts et exclusions manuels', barre: true })
  // Mémo : actions en barre, fenêtres centrées (croix, Échap, clic à l'extérieur ; focus dans la fenêtre).
  const fenetreAvecFocus = `(() => { const d = document.querySelector('[role=dialog]');
    if (!d) throw new Error('fenêtre absente'); if (!d.contains(document.activeElement)) throw new Error('focus hors de la fenêtre') })()`
  const fenetreFermee = `(() => { if (document.querySelector('[role=dialog]')) throw new Error('fenêtre encore ouverte') })()`
  const ouvrirFenetre = async (bouton) => { await cliquer(navigateur, bouton); await attendre(500); await navigateur.evaluer(fenetreAvecFocus) }
  const verifierFermee = async () => { await attendre(400); await navigateur.evaluer(fenetreFermee) }
  await etape(navigateur, 'Mémo : « Télécharger » ouvre la fenêtre (focus dans la fenêtre)', () => ouvrirFenetre('Télécharger'),
    { url: /step=selection_tiers/, texte: 'Verser au dossier de travail', barre: true })
  await etape(navigateur, 'Mémo : fenêtre « Télécharger » fermée par Échap', async () => {
    await navigateur.evaluer(`document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))`)
    await verifierFermee()
  }, { url: /step=selection_tiers/, texte: '4. Ajouts et exclusions manuels', barre: true })
  await etape(navigateur, 'Mémo : « Étape suivante : courriers » (mémo non validé) ouvre la fenêtre', () => ouvrirFenetre('Étape suivante : courriers'),
    { url: /step=selection_tiers/, texte: 'Y aller quand même', barre: true })
  await etape(navigateur, 'Mémo : fenêtre « Étape suivante » fermée par un clic à l’extérieur', async () => {
    await navigateur.evaluer(`document.querySelector('[role=dialog]').parentElement.click()`)
    await verifierFermee()
  }, { url: /step=selection_tiers/, texte: '4. Ajouts et exclusions manuels', barre: true })
  await etape(navigateur, 'Mémo : « Soumettre pour revue » ouvre la fenêtre', () => ouvrirFenetre('Soumettre pour revue'),
    { url: /step=selection_tiers/, texte: 'Confirmer la soumission', barre: true })
  await etape(navigateur, 'Mémo : fenêtre de soumission fermée par la croix', async () => {
    await navigateur.evaluer(`document.querySelector('[role=dialog] [aria-label="Fermer"]').click()`)
    await verifierFermee()
  }, { url: /step=selection_tiers/, texte: '4. Ajouts et exclusions manuels', barre: true })
  await etape(navigateur, 'Mémo : soumission confirmée depuis la fenêtre', async () => {
    await ouvrirFenetre('Soumettre pour revue')
    await cliquer(navigateur, 'Confirmer la soumission')
    await verifierFermee()
  }, { url: /step=selection_tiers/, texte: 'Demander une correction', barre: true })
  await etape(navigateur, 'Mémo : « Valider » ouvre la fenêtre (commentaire obligatoire), fermée par Échap', async () => {
    await ouvrirFenetre('Valider')
    if (!(await navigateur.evaluer(`[...document.querySelectorAll('[role=dialog] button')].find((b) => b.textContent.trim() === 'Confirmer la validation').disabled`)))
      throw new Error('validation possible sans commentaire')
    await navigateur.evaluer(`document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))`)
    await verifierFermee()
  }, { url: /step=selection_tiers/, texte: 'Soumis pour revue', barre: true })
  await etape(navigateur, 'Mémo : « Retour à la sélection » (sélection figée)', () => cliquer(navigateur, 'Retour à la sélection'),
    { url: /step=selection_tiers/, texte: 'Mémo soumis pour revue', barre: true })
  // Circularisation, sous-lot b : courriers en quatre étapes (Modèle, Coordonnées, Aperçu, Génération).
  await etape(navigateur, 'Barre latérale : Courriers (étape Modèle)', () => cliquer(navigateur, 'Courriers'),
    { url: /step=courriers/, texte: 'Gérer les modèles', barre: true })
  await etape(navigateur, 'Courriers : « Gérer les modèles » ouvre la bibliothèque, fermée par Échap', async () => {
    await ouvrirFenetre('Gérer les modèles')
    await navigateur.evaluer(`(() => { if (!document.querySelector('[role=dialog]').innerText.includes('Importer un modèle Word')) throw new Error('import absent') })()`)
    await navigateur.evaluer(`document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))`)
    await verifierFermee()
  }, { url: /step=courriers/, texte: 'Gérer les modèles', barre: true })
  await etape(navigateur, 'Courriers : « Suivant » mène à l’étape Coordonnées', () => cliquer(navigateur, 'Suivant'),
    { url: /step=courriers/, texte: '1 à compléter', barre: true })
  await etape(navigateur, 'Courriers : coordonnées du tiers retenu enregistrées (« Compléter »)', async () => {
    await ouvrirFenetre('Compléter')
    await navigateur.evaluer(`(() => {
      const saisir = (el, v) => { el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })) };
      saisir(document.querySelector('form textarea'), 'BP 1 Abidjan');
      saisir(document.querySelector('form input[type=email]'), 'compta@fournisseur-test.ci') })()`)
    await attendre(200)
    await cliquer(navigateur, 'Enregistrer les coordonnées')
    await verifierFermee()
  }, { url: /step=courriers/, texte: '0 à compléter', barre: true })
  await etape(navigateur, 'Courriers : étape Aperçu (clic sur l’étape)', () => cliquer(navigateur, '3 · Aperçu'),
    { url: /step=courriers/, texte: 'Les champs fusionnés sont surlignés', barre: true })
  await etape(navigateur, 'Courriers : aperçu, sélecteur du tiers (recherche, Échap, choix au clavier)', async () => {
    await navigateur.evaluer(`document.querySelector('[aria-haspopup=listbox]').click()`)
    await attendre(400)
    await navigateur.evaluer(`(() => {
      const r = document.querySelector('input[aria-label="Rechercher un tiers"]');
      if (!r || document.activeElement !== r) throw new Error('recherche absente ou sans focus');
      r.value = 'zzz-aucun'; r.dispatchEvent(new Event('input', { bubbles: true })) })()`)
    await attendre(300)
    await navigateur.evaluer(`(() => { if (!document.querySelector('[role=listbox]').innerText.includes('Aucun tiers ne correspond')) throw new Error('filtre inopérant');
      document.querySelector('input[aria-label="Rechercher un tiers"]').dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })) })()`)
    await attendre(300)
    await navigateur.evaluer(`(() => { if (document.querySelector('[role=listbox]')) throw new Error('liste encore ouverte') })()`)
    await navigateur.evaluer(`document.querySelector('[aria-haspopup=listbox]').click()`)
    await attendre(400)
    await navigateur.evaluer(`document.querySelector('input[aria-label="Rechercher un tiers"]').dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))`)
    await attendre(300)
    await navigateur.evaluer(`(() => {
      if (document.querySelector('[role=listbox]')) throw new Error('liste encore ouverte après le choix');
      const b = (t) => [...document.querySelectorAll('button')].find((x) => x.textContent.trim() === t);
      if (!b('Tiers précédent') || !b('Tiers suivant')) throw new Error('boutons Tiers précédent / suivant absents') })()`)
  }, { url: /step=courriers/, texte: 'prêt sur 1', barre: true })
  // Les modèles sont communs au cabinet : l'étape ne suppose ni la présence ni l'absence d'un modèle C2.
  await etape(navigateur, 'Courriers : étape Génération (résumé)', () => cliquer(navigateur, '4 · Génération'),
    { url: /step=courriers/, texte: 'Courriers prêts', barre: true })
  await etape(navigateur, 'Courriers : « Générer » ouvre la fenêtre (confirmation indisponible), fermée par un clic à l’extérieur', async () => {
    await ouvrirFenetre('Générer')
    if (!(await navigateur.evaluer(`[...document.querySelectorAll('[role=dialog] button')].find((b) => b.textContent.trim() === 'Confirmer la génération').disabled`)))
      throw new Error('génération confirmable')
    await navigateur.evaluer(`document.querySelector('[role=dialog]').parentElement.click()`)
    await verifierFermee()
  }, { url: /step=courriers/, texte: 'Tiers bloqués', barre: true })
  await etape(navigateur, 'Courriers : « Générer » en mode « Un seul tiers », liste non vide', async () => {
    await ouvrirFenetre('Générer')
    await navigateur.evaluer(`document.querySelector('[role=dialog] input[value=unitaire]').click()`)
    await attendre(400)
    const nb = await navigateur.evaluer(`(() => { const s = document.querySelector('[role=dialog] select[aria-label="Tiers à générer"]');
      if (!s) throw new Error('liste des tiers absente'); return [...s.options].filter((o) => o.value).length })()`)
    if (!nb) throw new Error('liste des tiers vide')
    await navigateur.evaluer(`document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))`)
    await verifierFermee()
  }, { url: /step=courriers/, texte: 'Tiers bloqués', barre: true })
  await etape(navigateur, 'Courriers : « Précédent » revient à l’étape Aperçu', () => cliquer(navigateur, 'Précédent'),
    { url: /step=courriers/, texte: 'Les champs fusionnés sont surlignés', barre: true })
  // Circularisation, sous-lot c : suivi des réponses (envoi enregistré, réponse saisie ; aucun envoi réel).
  await etape(navigateur, 'Barre latérale : Suivi des réponses', () => cliquer(navigateur, 'Suivi des réponses'),
    { url: /step=suivi_reponses/, texte: 'Enregistrer l’envoi', barre: true })
  await etape(navigateur, 'Suivi : envoi enregistré (destinataire repris de l’annuaire)', async () => {
    await cliquer(navigateur, 'Enregistrer l’envoi')
    await attendre(400)
    await cliquer(navigateur, 'Enregistrer')
  }, { url: /step=suivi_reponses/, texte: 'Saisir la réponse', barre: true })
  await etape(navigateur, 'Suivi : réponse saisie (accord total)', async () => {
    await cliquer(navigateur, 'Saisir la réponse')
    await attendre(400)
    await navigateur.evaluer(`(() => { const t = document.querySelector('[role=dialog] textarea');
      t.value = 'Réponse signée reçue par courriel'; t.dispatchEvent(new Event('input', { bubbles: true })) })()`)
    await attendre(200)
    await cliquer(navigateur, 'Enregistrer')
  }, { url: /step=suivi_reponses/, texte: 'Réponse reçue', barre: true })
  await etape(navigateur, 'Barre latérale : étape « Contrôle d’intangibilité »', () => navigateur.evaluer(`(() => {
      const el = [...document.querySelectorAll('span')].find((s) => s.textContent.trim().startsWith('Contrôle d') && s.textContent.includes('intangibilit'));
      if (!el) throw new Error('étape introuvable'); el.closest('[data-etape]').click() })()`),
    { url: /step=intang/, barre: true })
  await etape(navigateur, 'Barre latérale : cadence de relance lue sur le serveur', async () => {},
    { url: /step=intang/, texte: 'Relances J0 / J+15 / J+30 / J+45', barre: true })
  await etape(navigateur, 'Barre latérale : Phase 2 repliée -> résumé', () => cliquer(navigateur, 'Phase 2 – Exécution'),
    { url: /step=intang/, texte: 'Étapes 3 à 10 · cohérence', barre: true })
  await etape(navigateur, 'Barre latérale : Phase 2 dépliée -> étape « Contrôle de cohérence »', async () => {
    await cliquer(navigateur, 'Phase 2 – Exécution')
    await attendre(300)
    await cliquer(navigateur, 'Contrôle de cohérence')
  }, { url: /step=coherence/, barre: true })
  await etape(navigateur, 'Barre latérale : « Retour »', () => cliquer(navigateur, 'Retour'),
    { url: new RegExp(`^/client/${d.client_id}`), texte: d.client_nom })

  // Liste des missions -> ouverture d'une mission
  await etape(navigateur, 'Liste des missions', () => aller(navigateur, '/missions'), { url: /^\/missions/ })
  await etape(navigateur, 'Liste des missions : ouverture de la mission', async () => {
    await navigateur.evaluer(`(() => { const i = [...document.querySelectorAll('input')].find((x) => /recherch/i.test(x.placeholder || ''));
      if (i) { i.value = ${JSON.stringify(d.client_nom)}; i.dispatchEvent(new Event('input', { bubbles: true })) } })()`)
    await attendre(800)
    await navigateur.evaluer(`(() => { const tr = ${ligneDuClient}; if (!tr) throw new Error('mission absente de la liste'); tr.click() })()`)
  }, { url: mission, texte: 'Contrôle de cohérence', barre: true })
}

// --- Programme principal --------------------------------------------------------
async function principal() {
  mkdirSync(CAPTURES, { recursive: true })
  for (const [nom, url] of [['API', `${API}/health`], ['Interface (Vite)', FRONT]]) {
    try { await fetch(url) } catch { throw new Error(`${nom} injoignable sur ${url} : démarrez-la avant le test`) }
  }
  const d = donnees('creer')
  console.log(`Données fictives : client ${d.client_id}, mission ${d.mission_id}`)
  let navigateur
  try {
    navigateur = await lancerChrome()
    await parcours(navigateur, d)
  } finally {
    if (navigateur) navigateur.fermer()
    const nettoyage = donnees('supprimer', d.client_id, d.mission_id)
    console.log(`Nettoyage : ${JSON.stringify(nettoyage)}`)
  }
  const echecs = resultats.filter((r) => !r.ok)
  console.log(`\n${resultats.length - echecs.length}/${resultats.length} étapes OK — captures : ${CAPTURES}`)
  process.exit(echecs.length ? 1 : 0)
}

principal().catch((e) => { console.error(`Échec du test de parcours : ${e.message}`); process.exit(2) })
