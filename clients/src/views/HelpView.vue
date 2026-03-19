<script setup>
import { ref } from 'vue'

const lastUpdated = ref('2026-03-19')
</script>

<template>
  <div class="h-full w-full overflow-auto p-6 space-y-6">
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h1 class="text-2xl font-semibold text-gray-800 mb-2">Manuel d'utilisation</h1>
      <p class="text-sm text-gray-500">Base de guide à compléter – dernière mise à jour : {{ lastUpdated }}</p>
    </div>

    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-4">
      <h2 class="text-xl font-semibold text-gray-800">1. Vue d'ensemble</h2>
      <p class="text-sm text-gray-700">
        Cette application permet de gérer les missions d'audit, de générer les analyses (quantitative, qualitative),
        de produire des états financiers et d'exporter les résultats (XLSX).
      </p>
    </div>

    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-3">
      <h2 class="text-xl font-semibold text-gray-800">2. Navigation</h2>
      <ul class="list-disc pl-5 text-sm text-gray-700 space-y-1">
        <li>Accueil : accès rapide aux missions et clients.</li>
        <li>Missions : liste, création et accès aux analyses.</li>
        <li>Grouping analyse : point central des étapes d'analyse.</li>
      </ul>
    </div>

    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-3">
      <h2 class="text-xl font-semibold text-gray-800">3. Étapes principales</h2>
      <ul class="list-disc pl-5 text-sm text-gray-700 space-y-1">
        <li>Contrôle de cohérence</li>
        <li>Contrôle d'intangibilité</li>
        <li>Calcul des seuils</li>
        <li>Analyse quantitative</li>
        <li>Analyse qualitative</li>
        <li>Décision finale des comptes à tester</li>
        <li>Préparation des leads</li>
        <li>États financiers préliminaires</li>
        <li>Revue analytique finale</li>
      </ul>
    </div>

    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-3">
      <h2 class="text-xl font-semibold text-gray-800">4. Analyses et seuils</h2>
      <p class="text-sm text-gray-700">
        Les seuils (matérialité et performance) déterminent les comptes significatifs.
        L'analyse quantitative se base sur le seuil sélectionné.
        L'analyse qualitative affiche uniquement les comptes inférieurs au seuil.
      </p>
    </div>

    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-3">
      <h2 class="text-xl font-semibold text-gray-800">5. Téléchargements (XLSX)</h2>
      <ul class="list-disc pl-5 text-sm text-gray-700 space-y-1">
        <li>Grouping : export avec possibilité de sélectionner des groupes.</li>
        <li>Revue analytique : export multi-feuilles.</li>
        <li>Analyse quantitative : export multi-feuilles (Actifs, Passifs, Comptes de résultat).</li>
        <li>Analyse qualitative : export multi-feuilles filtrées par seuil.</li>
      </ul>
    </div>

    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-3">
      <h2 class="text-xl font-semibold text-gray-800">6. Conseils</h2>
      <ul class="list-disc pl-5 text-sm text-gray-700 space-y-1">
        <li>Vérifier la mission et l'année auditee avant d'exporter.</li>
        <li>Utiliser le filtrage Actif/Passif/Compte de résultat pour la revue.</li>
        <li>Mettre à jour les analyses après modification des seuils.</li>
      </ul>
    </div>
  </div>
</template>
